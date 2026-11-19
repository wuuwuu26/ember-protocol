@echo off
REM 用 UBT 跑一次完整的"生成工程 + UHT"，只为了让新文件进入编译列表。
REM
REM 背景：本机的 UBA 被系统权限拒绝（见 tools/build_ue.sh 顶部注释），
REM 所以 Build.bat 的**编译阶段**必然失败；但 UHT 与 .rsp 生成都发生在
REM 编译之前，只要它们成功，tools/build_ue.sh 就能接手编译链接。
REM
REM 用法：双击本文件，或在 Git Bash 里：
REM   cmd //c ue\regen_uht.bat
REM 然后跑 tools/build_ue.sh。

set "ENGINE=C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat"
set "PROJECT=%~dp0RobotGame.uproject"
set "LOG=%~dp0regen_uht.log"

echo [regen_uht] 运行 UBT（预计 1-3 分钟，末尾的编译失败是预期的）...
call "%ENGINE%" RobotGameEditor Win64 Development -Project="%PROJECT%" -NoUBA -WaitMutex > "%LOG%" 2>&1

echo [regen_uht] 查看 build_ue.sh 需要的 .rsp 是否已更新：
dir /b "%~dp0Intermediate\Build\Win64\x64\UnrealEditor\Development\RobotGame\*.cpp.obj.rsp" 2>nul | find /c /v "" >nul
echo [regen_uht] 日志：%LOG%
echo [regen_uht] 接下来执行： bash tools/build_ue.sh
