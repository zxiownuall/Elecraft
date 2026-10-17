$ErrorActionPreference = 'Stop'
$root=Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'elecraft'
$exe=Join-Path $root 'target\release\elecraft.exe'
$cfg=Join-Path $env:APPDATA 'Elecraft'
$legacy=Join-Path $env:APPDATA 'CADCraft'
function Snapshot([string]$path) { if (!(Test-Path $path)) { return @() }; return @(Get-ChildItem $path -Recurse -File | Sort-Object FullName | ForEach-Object { $_.FullName+':'+$_.Length+':'+$_.LastWriteTimeUtc.Ticks }) }
$before=Snapshot $legacy
$out=Join-Path $env:TEMP 'elecraft-gui-reopen.json'
$record=[ordered]@{session=[Diagnostics.Process]::GetCurrentProcess().SessionId; firstTitle=$null; firstClose=$null; secondTitle=$null; secondClose=$null; workspaceJson=$false; elecraftLog=$false; legacyUnchanged=$false; error=$null}
try {
 for ($run=1; $run -le 2; $run++) {
  $p=Start-Process -FilePath $exe -ArgumentList '--sample' -WorkingDirectory $root -PassThru
  for ($i=0; $i -lt 30; $i++) { Start-Sleep -Seconds 1; $p.Refresh(); if($p.HasExited -or $p.MainWindowHandle -ne 0){break} }
  if($p.HasExited -or $p.MainWindowHandle -eq 0){throw "Run $run failed to open GUI"}
  if($run -eq 1){$record.firstTitle=$p.MainWindowTitle}else{$record.secondTitle=$p.MainWindowTitle}
  $sent=$p.CloseMainWindow()
  if(!$sent){throw "Run $run WM_CLOSE refused"}
  $closed=$p.WaitForExit(15000)
  if(!$closed){Stop-Process -Id $p.Id -ErrorAction SilentlyContinue; throw "Run $run did not close normally"}
  if($run -eq 1){$record.firstClose=$p.ExitCode}else{$record.secondClose=$p.ExitCode}
 }
 $record.workspaceJson=Test-Path (Join-Path $cfg 'workspace.json')
 $record.elecraftLog=Test-Path (Join-Path $cfg 'logs\elecraft.log')
 $record.legacyUnchanged=(@(Snapshot $legacy) -join '|') -eq ($before -join '|')
} catch {$record.error=$_.Exception.Message} finally {$record | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 $out}
if($record.error){throw $record.error}
