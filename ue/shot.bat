@echo off
REM Unattended visual check runner.
REM   ue\shot.bat <Name> <Seconds> -Arg1=V -Arg2
REM Example:
REM   ue\shot.bat combat 40 -AutoFire -SkipMenu -ShotEvery=3
REM
REM ASCII-only on purpose (cmd + code page 936 mangles UTF-8).
REM Implementation lives in shot.ps1 (also ASCII-only).

setlocal enabledelayedexpansion
set "NAME=%~1"
if "%NAME%"=="" set "NAME=shot"
set "SECS=%~2"
if "%SECS%"=="" set "SECS=20"
shift
shift

REM Collect the rest into one line. A pair like "-ShotEvery" "3" (cmd splits at
REM '=', ';' and ',') is joined back into "-ShotEvery=3".
set "EXTRA="
:collect
if "%~1"=="" goto run
set "A=%~1"
set "NEXT=%~2"
if not "%NEXT%"=="" (
    echo !A! | findstr /e /c:"=" >nul && (
        set "EXTRA=!EXTRA! !A!!NEXT!"
        shift
        shift
        goto collect
    )
)
set "EXTRA=!EXTRA! !A!"
shift
goto collect

:run
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0shot.ps1" -Name %NAME% -Seconds %SECS% -GameArgs "!EXTRA!"
