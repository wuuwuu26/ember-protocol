# -*- coding: utf-8 -*-
"""诊断 custom_rasterizer_kernel.pyd 的 DLL 依赖（第一百一十九轮）。

STATUS.md 说编译装好了但导入报 "找不到指定的模块"。用 dumpbin/dependencies
找缺失 DLL，先试最省事的 PATH 修法（CUDA bin + MSVC 运行库）。
"""
import os
import glob
import subprocess
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace", line_buffering=True)

VENV = r"C:\AI\Hunyuan3D\venv\Scripts\python.exe"
REPO = r"C:\AI\Hunyuan3D\Hunyuan3D-2-main"

# 1. 找到 .pyd
pyds = glob.glob(os.path.join(REPO, "**", "custom_rasterizer_kernel*.pyd"),
                 recursive=True)
print("=== .pyd 文件 ===")
for p in pyds:
    print(" ", p, os.path.getsize(p))

# 2. 关键 DLL 是否存在
cuda_bin = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin"
print("\n=== CUDA DLL ===")
for d in ("cudart64_12.dll", "cublas64_12.dll", "cublasLt64_12.dll"):
    p = os.path.join(cuda_bin, d)
    print("  %-24s %s" % (d, os.path.exists(p)))

print("\n=== MSVC 运行库（系统）===")
for d in ("vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll"):
    found = glob.glob(r"C:\Windows\System32\\" + d) + glob.glob(
        r"C:\Program Files (x86)\Microsoft Visual Studio\2022\**\\" + d,
        recursive=True)
    print("  %-24s %s" % (d, bool(found)))

# 3. 用 dumpbin 看 .pyd 的依赖（如果有）
print("\n=== 尝试在补好 PATH 后导入 ===")
env = dict(os.environ)
env["PATH"] = cuda_bin + ";" + env.get("PATH", "")
# 找 MSVC redist 目录加进去
for root in glob.glob(r"C:\Program Files (x86)\Microsoft Visual Studio\2022\**\VC\Redist\MSVC\**\x64\Microsoft.VC*.CRT",
                      recursive=True):
    env["PATH"] = root + ";" + env["PATH"]

code = (
    "import sys;"
    "sys.path.insert(0, r'%s');"
    "import custom_rasterizer;"
    "print('IMPORT_OK', custom_rasterizer.__file__)" % REPO
)
r = subprocess.run([VENV, "-c", code], capture_output=True, text=True,
                   encoding="utf-8", errors="replace", env=env)
print("  stdout:", r.stdout.strip()[-300:])
print("  stderr:", r.stderr.strip()[-400:])
print("  returncode:", r.returncode)
print("PROBE_DONE")
