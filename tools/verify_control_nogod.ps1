# Control experiment: NO -Observer, NO -GodMode.
# If the mech DOES get defeated here, it proves the observer run's survival
# was caused by the new invulnerability (not by enemies being passive).
# ASCII-only for Windows PowerShell 5.1.
param([int]$Seconds = 22, [int]$Wait = 320)

$ErrorActionPreference = "Stop"
$Engine = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$Proj  = "C:\Users\25227\Documents\robot_game\ue\RobotGame.uproject"
$Log   = "C:\Users\25227\Documents\robot_game\ue\shot_control_nogod.log"

if (Test-Path $Log) { Remove-Item $Log -Force }

# NO -GodMode AND NO -Observer
$ArgList = @($Proj, "-game", "-windowed", "-nohighdpi",
             "-resx=1280", "-resy=720", "-SkipMenu", "-ShotMode",
             "-AutoQuit=$Seconds", "-abslog=$Log")

Start-Process -FilePath $Engine -ArgumentList $ArgList
Start-Sleep -Seconds $Wait
Get-Process UnrealEditor -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
Write-Output "DONE log=$Log"
