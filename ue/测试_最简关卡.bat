@echo off
chcp 936 >nul
title 最简对照测试

set "ENGINE=C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
set "PROJECT=%~dp0RobotGame.uproject"

echo.
echo  ============================================================
echo    最简对照测试
echo  ============================================================
echo.
echo    这个关卡里只有：
echo      - 一个引擎自带的立方体（10 米宽，压扁当地面）
echo      - 可移动的平行光 + 天光 + 大气
echo      - 出生点
echo.
echo    没有任何我们导入的资产。
echo.
echo    如果这个也全黑  -^> 问题在引擎或显卡驱动，与我们的资产无关
echo    如果这个正常    -^> 问题在我们的关卡或导入的资产上
echo.
echo  ============================================================
echo.

if not exist "%ENGINE%" (
    echo  [错误] 找不到引擎: %ENGINE%
    pause
    exit /b 1
)

"%ENGINE%" "%PROJECT%" -game -windowed -resx=1280 -resy=720 "/Game/RobotGame/Maps/_MinTest"

if errorlevel 1 (
    echo.
    echo  [退出码 %errorlevel%] 异常退出。
    pause
)
