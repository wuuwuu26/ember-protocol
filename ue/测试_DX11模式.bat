@echo off
chcp 936 >nul
title 最简关卡 - DX11 模式

set "ENGINE=C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
set "PROJECT=%~dp0RobotGame.uproject"

echo.
echo  ============================================================
echo    最简关卡 - DX11 模式
echo  ============================================================
echo.
echo    UE5 默认用 DX12 / Shader Model 6，这条路径对显卡驱动更敏感。
echo    这里强制改用 DX11，用来判断是不是 DX12 路径的问题。
echo.
echo    如果这个能看见画面  -^> 问题在 DX12 路径，需要更新显卡驱动
echo    如果这个也是黑的    -^> 问题更底层，需要查引擎安装
echo.
echo  ============================================================
echo.

if not exist "%ENGINE%" (
    echo  [错误] 找不到引擎: %ENGINE%
    pause
    exit /b 1
)

"%ENGINE%" "%PROJECT%" -game -windowed -resx=1280 -resy=720 -dx11 -sm5 "/Game/RobotGame/Maps/_MinTest"

if errorlevel 1 (
    echo.
    echo  [退出码 %errorlevel%] 异常退出。
    pause
)
