@echo off
chcp 936 >nul
title 余火协议 - 独立运行

set "ENGINE=C:////Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
set "PROJECT=%~dp0RobotGame.uproject"

echo.
echo  ============================================================
echo    余火协议   独立运行
echo  ============================================================
echo.
echo    WASD 移动      鼠标 视角      左键 射击
echo    空格 冲刺      1 2 3 切换机体
echo.
echo    画面左上角显示热量 / 电力 / 废料 / 当前机体
echo    热量涨满会触发过热锁定，武器停用约 2 秒
echo.
echo    首次运行要编译着色器，请等 30-60 秒...
echo  ============================================================
echo.

if not exist "%ENGINE%" (
    echo  [错误] 找不到引擎: %ENGINE%
    echo.
    pause
    exit /b 1
)
if not exist "%PROJECT%" (
    echo  [错误] 找不到工程: %PROJECT%
    echo.
    pause
    exit /b 1
)

"%ENGINE%" "%PROJECT%" -game -windowed -resx=1600 -resy=900

if errorlevel 1 (
    echo.
    echo  [退出码 %errorlevel%] 游戏异常退出。
    pause
)
