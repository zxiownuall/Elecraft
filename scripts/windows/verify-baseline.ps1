$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..\..'))
$env:PATH = (Join-Path $HOME '.cargo\bin') + ';' + $env:PATH
$vcvars = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat'
if (!(Test-Path $vcvars)) { throw "MSVC developer environment unavailable: $vcvars" }
$vars = & cmd.exe /d /s /c ('"' + $vcvars + '" >nul && set')
if ($LASTEXITCODE -ne 0) { throw "vcvars64 failed with exit $LASTEXITCODE" }
foreach ($line in $vars) {
    if ($line -match '^([^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], 'Process') }
}
if (!(Get-Command link.exe -ErrorAction SilentlyContinue)) { throw 'MSVC linker not found after vcvars64' }
Write-Output ('MSVC linker: ' + (Get-Command link.exe).Source)
# Keep the cold Windows build inside this PC's limited free-space budget.
$env:CARGO_PROFILE_DEV_DEBUG = '0'
$env:CARGO_PROFILE_TEST_DEBUG = '0'
$env:CARGO_INCREMENTAL = '0'
$env:CARGO_BUILD_JOBS = '2'
function Invoke-Checked([string]$label, [scriptblock]$body) {
    Write-Output "BEGIN $label"
    & $body
    if ($LASTEXITCODE -ne 0) { throw "$label failed with exit $LASTEXITCODE" }
    Write-Output "PASS $label"
}
Invoke-Checked 'format' { cargo fmt --all -- --check }
Invoke-Checked 'clippy' { cargo clippy --locked --workspace --all-targets -- -D warnings }
Invoke-Checked 'tests' { cargo test --locked --workspace }
Invoke-Checked 'build' { cargo build --release --locked -p cadcraft -p cadcraft-cli }
$desktop = Join-Path (Get-Location) 'target\release\elecraft.exe'
$cli = Join-Path (Get-Location) 'target\release\elecraft-cli.exe'
if (!(Test-Path $desktop) -or !(Test-Path $cli)) { throw 'Elecraft executables missing' }
$version = & $cli --version
if ($LASTEXITCODE -ne 0 -or $version -notmatch '^elecraft-cli ') { throw "wrong CLI identity: $version" }
$tmp = Join-Path $env:TEMP ('elecraft-smoke-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tmp | Out-Null
$dxf = Join-Path $tmp 'sample.dxf'
Invoke-Checked 'synthetic DXF' { & $cli run --sample --save $dxf }
if (!(Test-Path $dxf) -or (Get-Item $dxf).Length -eq 0) { throw 'DXF missing or empty' }
Invoke-Checked 'read DXF' { & $cli info $dxf }
Write-Output "Windows CLI smoke passed; sample: $dxf"
