# Verify observer invulnerability WITHOUT -GodMode (ASCII-only for PS 5.1).
# The only damage-immunity source must be the runtime bInvulnerable flag.
# Log analysis is done separately in Python (UTF-8 safe).
param([int]$Seconds = 18, [int]$Wait = 320)

$ErrorActionPreference = "Stop"
$Engine = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$Proj  = "C:\Users\25227\Documents\robot_game\ue\RobotGame.uproject"
$Log   = "C:\Users\25227\Documents\robot_game\ue\shot_obsinvul_nogod.log"

if (Test-Path $Log) { Remove-Item $Log -Force }

# Deliberately NO -GodMode
$ArgList = @($Proj, "-game", "-windowed", "-nohighdpi",
             "-resx=1280", "-resy=720", "-SkipMenu", "-ShotMode",
             "-Observer", "-AutoQuit=$Seconds", "-abslog=$Log")

Start-Process -FilePath $Engine -ArgumentList $ArgList
Start-Sleep -Seconds $Wait
Get-Process UnrealEditor -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
Write-Output "DONE log=$Log"
