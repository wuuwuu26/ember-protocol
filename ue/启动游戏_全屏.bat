@echo off
chcp 936 >nul
title 余火协议 - 全屏模式（输入焦点更可靠）

set "ENGINE=C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
set "PROJECT=%~dp0RobotGame.uproject"

echo.
echo  ============================================================
echo    余火协议 - 全屏模式
echo  ============================================================
echo.
echo    排查记录：-game -windowed 模式下，游戏窗口常常拿不到键盘焦点，
echo    导致按键完全没有反应（日志里 HandleMove 一次都不触发）。
echo    全屏窗口能可靠获得焦点。
echo.
echo    操作：WASD 移动 / 鼠标 转视角 / 左键 射击 / 空格 冲刺 / 1-2-3 换机体
echo    按 Alt+F4 或 Esc 退出
echo.
echo  ============================================================
echo.

if not exist "%ENGINE%" (
    echo  [错误] 找不到引擎: %ENGINE%
    pause
    exit /b 1
)

"%ENGINE%" "%PROJECT%" -game -fullscreen -resx=1920 -resy=1080

if errorlevel 1 (
    echo.
    echo  [退出码 %errorlevel%] 异常退出。
    pause
)
