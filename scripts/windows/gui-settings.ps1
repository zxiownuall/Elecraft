$ErrorActionPreference='Stop'
$root=Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'elecraft'
$exe=Join-Path $root 'target\release\elecraft.exe'
$cfg=Join-Path $env:APPDATA 'Elecraft\workspace.json'
$legacy=Join-Path $env:APPDATA 'CADCraft'
function Snapshot([string]$p) { if(!(Test-Path $p)){return @()}; return @(Get-ChildItem $p -Recurse -File | Sort-Object FullName | ForEach-Object {$_.FullName+':'+$_.Length+':'+$_.LastWriteTimeUtc.Ticks}) }
$before=Snapshot $legacy
$record=[ordered]@{session=[Diagnostics.Process]::GetCurrentProcess().SessionId; firstSet=$null; savedAfterFirst=$false; restoredOnReopen=$null; reset=$null; finalFile=$false; legacyUnchanged=$false; error=$null}
function Exchange($writer,$reader,[int]$id,[string]$method,[hashtable]$params) {
 $writer.WriteLine((@{id=$id;method=$method;params=$params}|ConvertTo-Json -Compress -Depth 8))
 $line=$reader.ReadLine(); if(!$line){throw "No reply: $method"}
 $reply=$line|ConvertFrom-Json; if(!$reply.ok){throw "Rejected $method : $line"}; return $reply.result
}
try {
 for($run=1;$run -le 2;$run++) {
  $port=49330+$run
  $p=Start-Process -FilePath $exe -ArgumentList @('--control',"$port",'--sample') -WorkingDirectory $root -PassThru
  $client=$null; $writer=$null; $reader=$null
  try {
   for($i=0;$i -lt 30;$i++){Start-Sleep -Seconds 1; try{$client=[Net.Sockets.TcpClient]::new('127.0.0.1',$port);break}catch{$p.Refresh();if($p.HasExited){throw "Exited $($p.ExitCode)"}}}
   if(!$client){throw "No control listener on run $run"}
   $client.ReceiveTimeout=60000; $reader=[IO.StreamReader]::new($client.GetStream()); $writer=[IO.StreamWriter]::new($client.GetStream()); $writer.AutoFlush=$true
   if($run -eq 1){$record.firstSet=(Exchange $writer $reader 1 'ui.set' @{showToolbar=$false}).showToolbar}
   else {$record.restoredOnReopen=(Exchange $writer $reader 1 'ui.inspect' @{}).ui.showToolbar; $record.reset=(Exchange $writer $reader 2 'ui.set' @{showToolbar=$true}).showToolbar}
   [void](Exchange $writer $reader 3 'app.quit' @{})
   if(!$p.WaitForExit(15000)){throw "Quit timeout on run $run"}
  } finally {if($writer){$writer.Dispose()};if($reader){$reader.Dispose()};if($client){$client.Dispose()};if(!$p.HasExited){Stop-Process -Id $p.Id -ErrorAction SilentlyContinue}}
  if($run -eq 1){$record.savedAfterFirst=Test-Path $cfg}
 }
 $record.finalFile=Test-Path $cfg
 $record.legacyUnchanged=(@(Snapshot $legacy)-join '|') -eq ($before-join '|')
} catch {$record.error=$_.Exception.Message} finally {$record|ConvertTo-Json -Depth 6|Set-Content -Encoding UTF8 (Join-Path $env:TEMP 'elecraft-gui-settings.json')}
if($record.error){throw $record.error}
