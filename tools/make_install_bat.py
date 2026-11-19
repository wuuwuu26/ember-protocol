# -*- coding: utf-8 -*-
"""生成"卸载 5.2 + 安装 5.3"的提权批处理（第一百一十七轮）。

用 Start-Process -Verb RunAs 一次性执行，避免多次 UAC 弹窗。
每步输出日志到临时目录，便于安装后核查。
"""
import os

TEMP = r"C:\Users\25227\AppData\Local\Temp\opencode"
MSI = os.path.join(TEMP, "blender53.msi")
LOG = os.path.join(TEMP, "blender_install.log")
OLD_GUID = "{4B0BC91B-29A6-4B8C-A60B-6154FD3AE3AD}"

bat = r"""@echo off
chcp 65001 >nul
set LOG={log}
echo ==== Blender 覆盖安装 %DATE% %TIME% ==== > "%LOG%"

echo [1/3] 清理探测残留 >> "%LOG%"
del /f /q "C:\Program Files\_opencode_elev_probe.txt" >> "%LOG%" 2>&1

echo [2/3] 卸载 Blender 5.2.2 (MSI {guid}) >> "%LOG%"
MsiExec.exe /X{guid} /qn /L*V "{temp}\blender_uninstall_msi.log" >> "%LOG%" 2>&1
echo    卸载退出码 %ERRORLEVEL% >> "%LOG%"

echo [3/3] 安装 Blender 5.3.0 (MSI) >> "%LOG%"
MsiExec.exe /I "{msi}" /qn /L*V "{temp}\blender_install_msi.log" >> "%LOG%" 2>&1
echo    安装退出码 %ERRORLEVEL% >> "%LOG%"

echo ==== DONE ==== >> "%LOG%"
""".format(log=LOG, guid=OLD_GUID, temp=TEMP, msi=MSI)

path = os.path.join(TEMP, "do_blender_install.bat")
with open(path, "w", encoding="utf-8") as f:
    f.write(bat)
print(path)
