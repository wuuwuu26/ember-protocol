param(
    [string]$Name = "run",
    [int]$Seconds = 24,
    [int]$Wait = 34,
    [string]$Extra = "",
    [int]$ResX = 1280,
    [int]$ResY = 720
)

# ASCII only: Windows PowerShell 5.1 reads .ps1 in the system code page.
$ErrorActionPreference = "Stop"
$Engine = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$Proj = "C:\Users\25227\Documents\robot_game\ue\RobotGame.uproject"
$ShotDir = "C:\Users\25227\Documents\robot_game\ue\Saved\Screenshots\WindowsEditor"
$Log = "C:\Users\25227\Documents\robot_game\ue\shot_$Name.log"

if (Test-Path $ShotDir) { Get-ChildItem "$ShotDir\ScreenShot*.png" -ErrorAction SilentlyContinue | Remove-Item -Force }
if (Test-Path $Log) { Remove-Item $Log -Force -ErrorAction SilentlyContinue }

$ArgList = @($Proj, "-game", "-windowed", "-nohighdpi", "-resx=$ResX", "-resy=$ResY", "-SkipMenu",
             "-ShotMode", "-GodMode", "-ShotEvery=5",
             "-AutoQuit=$Seconds", "-abslog=$Log")
if ($Extra) { $ArgList += ($Extra -split '\s+' | Where-Object { $_ }) }

Start-Process -FilePath $Engine -ArgumentList $ArgList
Start-Sleep -Seconds $Wait
Get-Process UnrealEditor -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

$shots = Get-ChildItem "$ShotDir\ScreenShot*.png" -ErrorAction SilentlyContinue
Write-Output ("[shot] {0} -> {1} png, log {2}" -f $Name, $shots.Count, $Log)
