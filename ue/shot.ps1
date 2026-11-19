param(
    [string]$Name = "shot",
    [int]$Seconds = 14,
    [int]$Every = 0,
    [switch]$AutoFire,
    [switch]$SkipMenu,
    [string]$Extra = ""
)

# Unattended visual check: run the game for N seconds, grab screenshots at a
# fixed cadence, then quit (AutoQuit).
#
#   ue\shot.ps1 -Name combat -Seconds 40 -Every 3 -AutoFire -SkipMenu
#   ue\shot.ps1 -Name menu -Seconds 20              (main menu)
#   ue\shot.ps1 -Name ui -Seconds 25 -Every 5 -AutoFire -SkipMenu -Extra "-ModdingUI"
#
# Screenshots: ue\Saved\Screenshots\WindowsEditor\ScreenShot*.png
# Log:         ue\shot_<Name>_<HHmmss>.log
#
# ASCII-only on purpose: Windows PowerShell 5.1 reads .ps1 in the system code
# page, so UTF-8 Chinese comments would break parsing.

$ErrorActionPreference = "Stop"
$Engine = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$Project = Join-Path $PSScriptRoot "RobotGame.uproject"
$ShotDir = Join-Path $PSScriptRoot "Saved\Screenshots\WindowsEditor"

if (Test-Path $ShotDir) { Get-ChildItem "$ShotDir\ScreenShot*.png" | Remove-Item -Force }
Get-ChildItem (Join-Path $PSScriptRoot ("shot_" + $Name + "_*.log")) -ErrorAction SilentlyContinue |
    Remove-Item -Force

# Timestamped log name: a leftover process holding the old log would otherwise
# block startup entirely.
$Log = Join-Path $PSScriptRoot ("shot_" + $Name + "_" + (Get-Date -Format "HHmmss") + ".log")

$ArgList = @($Project, "-game", "-windowed", "-resx=1600", "-resy=900")
if ($AutoFire) { $ArgList += "-AutoFire" }
if ($SkipMenu) { $ArgList += "-SkipMenu" }
if ($Every -gt 0) { $ArgList += "-ShotEvery=$Every" }
if ($Extra) { $ArgList += ($Extra -split '\s+' | Where-Object { $_ }) }
$ArgList += "-AutoQuit=$Seconds"
$ArgList += "-abslog=$Log"

Write-Host ("[shot] {0}: {1} s -> {2}" -f $Name, $Seconds, ($ArgList -join " "))
Start-Process -FilePath $Engine -ArgumentList $ArgList | Out-Null

# The editor detaches on launch, so poll the process list by command line.
$Deadline = (Get-Date).AddSeconds($Seconds + 180)
$SawProcess = $false
while ((Get-Date) -lt $Deadline) {
    Start-Sleep -Seconds 2
    $p = Get-CimInstance Win32_Process -Filter "Name = 'UnrealEditor.exe'" -ErrorAction SilentlyContinue |
         Where-Object { $_.CommandLine -like "*$Log*" }
    if ($p) { $SawProcess = $true }
    elseif ($SawProcess) { break }
}
if (-not $SawProcess) {
    Write-Host "[shot] WARNING: never saw the game process start"
}

Start-Sleep -Seconds 1
if (Test-Path $ShotDir) {
    Get-ChildItem "$ShotDir\ScreenShot*.png" | Select-Object Name, Length |
        Format-Table -AutoSize
}
Write-Host "[shot] log: $Log"
