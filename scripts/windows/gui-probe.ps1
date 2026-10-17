$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class ElecraftWindow {
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT r);
 [DllImport("user32.dll", SetLastError=true)] public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdc, uint flags);
 [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
}
'@
$root = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'elecraft'
$exe = Join-Path $root 'target\release\elecraft.exe'
$result = Join-Path $env:TEMP 'elecraft-gui-probe.json'
$image = Join-Path $env:TEMP 'elecraft-gui-probe.png'
$legacy = Join-Path $env:APPDATA 'CADCraft'
function Snapshot([string]$path) {
 if (!(Test-Path $path)) { return @() }
 return @(Get-ChildItem $path -File -Recurse | ForEach-Object { $_.FullName + ':' + $_.Length + ':' + $_.LastWriteTimeUtc.Ticks })
}
$before = Snapshot $legacy
$p = Start-Process -FilePath $exe -ArgumentList '--sample' -WorkingDirectory $root -PassThru
try {
 $window = 0
 for ($i = 0; $i -lt 30; $i++) {
  Start-Sleep -Seconds 1
  $p.Refresh()
  if ($p.HasExited) { break }
  if ($p.MainWindowHandle -ne 0) { $window = $p.MainWindowHandle; break }
 }
 $info = [ordered]@{ session=[Diagnostics.Process]::GetCurrentProcess().SessionId; pid=$p.Id; exited=$p.HasExited; exitCode=$(if($p.HasExited){$p.ExitCode}else{$null}); title=$p.MainWindowTitle; windowHandle=$window; sample=$true; screenshot=$null; screenshotOk=$false; legacyUnchanged=$false; elecraftConfigExists=$false; error=$null }
 if ($window -ne 0) {
  Start-Sleep -Seconds 3
  $p.Refresh(); $info.title = $p.MainWindowTitle
  $rect = New-Object ElecraftWindow+RECT
  [void][ElecraftWindow]::GetWindowRect($window,[ref]$rect)
  $width=$rect.Right-$rect.Left; $height=$rect.Bottom-$rect.Top
  $info.windowSize = "$width x $height"
  if ($width -gt 0 -and $height -gt 0 -and $width -le 5000 -and $height -le 5000) {
   $bmp=New-Object System.Drawing.Bitmap($width,$height)
   $g=[System.Drawing.Graphics]::FromImage($bmp)
   try { $info.screenshotOk=[ElecraftWindow]::PrintWindow($window,$g.GetHdc(),2) } finally { $g.ReleaseHdc(); $g.Dispose() }
   if ($info.screenshotOk) { $bmp.Save($image,[System.Drawing.Imaging.ImageFormat]::Png); $info.screenshot=$image }
   $bmp.Dispose()
  }
 }
 $info.legacyUnchanged = (@(Snapshot $legacy) -join '|') -eq ($before -join '|')
 $info.elecraftConfigExists = Test-Path (Join-Path $env:APPDATA 'Elecraft')
 $info | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 $result
} catch {
 @{error=$_.Exception.Message; pid=$p.Id} | ConvertTo-Json | Set-Content -Encoding UTF8 $result
 throw
} finally {
 if (!$p.HasExited) { Stop-Process -Id $p.Id -ErrorAction SilentlyContinue }
}
