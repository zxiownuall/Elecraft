param([Parameter(Mandatory=$true)][string]$DrawingPath)
$ErrorActionPreference = 'Stop'
$root = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'elecraft'
$exe = Join-Path $root 'target\release\elecraft.exe'
$out = Join-Path $env:TEMP 'elecraft-gui-exercise.json'
$shot = Join-Path $env:TEMP 'elecraft-dxf-gui.png'
$legacy = Join-Path $env:APPDATA 'CADCraft'
function Snapshot([string]$path) {
 if (!(Test-Path $path)) { return @() }
 return @(Get-ChildItem $path -Recurse -File | Sort-Object FullName | ForEach-Object { $_.FullName + ':' + $_.Length + ':' + $_.LastWriteTimeUtc.Ticks })
}
$before = Snapshot $legacy
$port = 49321
$p = Start-Process -FilePath $exe -ArgumentList @('--control',"$port",'--sample') -WorkingDirectory $root -PassThru
$client = $null
$reader = $null
$writer = $null
$record = [ordered]@{session=[Diagnostics.Process]::GetCurrentProcess().SessionId; pid=$p.Id; title=$null; sampleView=$null; zoomView=$null; panView=$null; cmdline=$null; dxfPath=$DrawingPath; dxfTitle=$null; dxfEntities=$null; screenshot=$null; legacyUnchanged=$false; elecraftConfigExists=$false; error=$null}
function Send([int]$id, [string]$method, [hashtable]$params) {
 $writer.WriteLine((@{id=$id; method=$method; params=$params} | ConvertTo-Json -Compress -Depth 8))
 $line = $reader.ReadLine()
 if (!$line) { throw "No reply for $method" }
 $reply = $line | ConvertFrom-Json
 if (!$reply.ok) { throw "Control $method failed: $line" }
 return $reply.result
}
try {
 for ($i=0; $i -lt 30; $i++) {
  Start-Sleep -Seconds 1
  try { $client=[Net.Sockets.TcpClient]::new('127.0.0.1',$port); break } catch { $p.Refresh(); if ($p.HasExited) { throw "GUI exited: $($p.ExitCode)" } }
 }
 if (!$client) { throw 'Control listener did not start' }
 $client.ReceiveTimeout=60000; $client.SendTimeout=60000
 $reader=[IO.StreamReader]::new($client.GetStream())
 $writer=[IO.StreamWriter]::new($client.GetStream()); $writer.AutoFlush=$true
 $p.Refresh(); $record.title=$p.MainWindowTitle
 $initial=Send 1 'ui.inspect' @{}
 $record.sampleView=$initial.view
 $zoom=Send 2 'engine.execute' @{command='zoom.in'; params=@{}}
 $record.zoomView=(Send 3 'ui.inspect' @{}).view
 $pan=Send 4 'engine.execute' @{command='pan.right'; params=@{}}
 $record.panView=(Send 5 'ui.inspect' @{}).view
 $record.cmdline=Send 6 'cmdline.input' @{text='regen'}
 $opened=Send 7 'app.open' @{path=$DrawingPath}
 $drawing=Send 8 'drawing.inspect' @{}
 $record.dxfEntities=$drawing.entitiesCount
 $record.dxfTitle=$drawing.title
 $capture=Send 9 'ui.screenshot' @{path=$shot}
 $record.screenshot=$(if(Test-Path $shot){$shot}else{$null})
 $record.legacyUnchanged=(@(Snapshot $legacy) -join '|') -eq ($before -join '|')
 $record.elecraftConfigExists=Test-Path (Join-Path $env:APPDATA 'Elecraft')
} catch { $record.error=$_.Exception.Message } finally {
 $record | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 $out
 if ($writer) { $writer.Dispose() }; if ($reader) { $reader.Dispose() }; if ($client) { $client.Dispose() }
 if (!$p.HasExited) { Stop-Process -Id $p.Id -ErrorAction SilentlyContinue }
}
if ($record.error) { throw $record.error }
