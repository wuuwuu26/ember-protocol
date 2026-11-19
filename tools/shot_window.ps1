param(
    [string]$Name = "winshot",
    [int]$Seconds = 30,
    [int]$At = 12,
    [string]$Extra = ""
)

# Grab the actual game window through DWM (PrintWindow with PW_RENDERFULLCONTENT).
# In-engine PNG readback on this box intermittently produces tiles from stale frames.
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

Add-Type @"
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
public class WinCap2 {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc cb, IntPtr lParam);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT r);
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdc, uint flags);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder s, int n);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
    public static IntPtr FindByPid(uint pid) {
        IntPtr best = IntPtr.Zero; int bestArea = 0;
        EnumWindows((h, l) => {
            uint p; GetWindowThreadProcessId(h, out p);
            if (p != pid || !IsWindowVisible(h)) return true;
            RECT r; GetWindowRect(h, out r);
            int area = (r.Right - r.Left) * (r.Bottom - r.Top);
            if (area > bestArea) { bestArea = area; best = h; }
            return true;
        }, IntPtr.Zero);
        return best;
    }
}
"@

$Engine = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$Proj = "C:\Users\25227\Documents\robot_game\ue\RobotGame.uproject"
$Log = "C:\Users\25227\Documents\robot_game\ue\shot_$Name.log"
$OutDir = "C:\Users\25227\Documents\robot_game\docs\shots\win"
if (!(Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
if (Test-Path $Log) { Remove-Item $Log -Force -ErrorAction SilentlyContinue }

$ArgList = @($Proj, "-game", "-windowed", "-resx=1600", "-resy=900", "-SkipMenu",
             "-GodMode", "-AutoQuit=$Seconds", "-abslog=$Log")
if ($Extra) { $ArgList += ($Extra -split '\s+' | Where-Object { $_ }) }

$proc = Start-Process -FilePath $Engine -ArgumentList $ArgList -PassThru
Start-Sleep -Seconds $At

$hwnd = [IntPtr]::Zero
for ($i = 0; $i -lt 20; $i++) {
    $hwnd = [WinCap2]::FindByPid([uint32]$proc.Id)
    if ($hwnd -ne [IntPtr]::Zero) { break }
    Start-Sleep -Milliseconds 500
}
if ($hwnd -eq [IntPtr]::Zero) { Write-Output "[winshot] no window"; exit 1 }

$rect = New-Object WinCap2+RECT
[WinCap2]::GetWindowRect($hwnd, [ref]$rect) | Out-Null
$w = $rect.Right - $rect.Left
$h = $rect.Bottom - $rect.Top
$bmp = New-Object System.Drawing.Bitmap($w, $h)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$hdc = $g.GetHdc()
$ok = [WinCap2]::PrintWindow($hwnd, $hdc, 2)
$g.ReleaseHdc($hdc)
$g.Dispose()
$path = Join-Path $OutDir ("{0}.png" -f $Name)
$bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()

Get-Process UnrealEditor -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Output ("[winshot] {0} ok={1} ({2}x{3})" -f $path, $ok, $w, $h)
