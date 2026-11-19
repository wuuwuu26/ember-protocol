# -*- coding: utf-8 -*-
"""测试把 torch/lib 加进 PATH / 用 add_dll_directory 后能否导入 custom_rasterizer。"""
import os
import subprocess
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace", line_buffering=True)

VENV_PY = r"C:\AI\Hunyuan3D\venv\Scripts\python.exe"
VENV_LIB = r"C:\AI\Hunyuan3D\venv\Lib\site-packages\torch\lib"
CUDA_BIN = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin"
REPO = r"C:\AI\Hunyuan3D\Hunyuan3D-2-main"

# 方法 A：PATH 加 torch\lib + cuda
env = dict(os.environ)
env["PATH"] = VENV_LIB + ";" + CUDA_BIN + ";" + env.get("PATH", "")

code = (
    "import os, sys;"
    "sys.path.insert(0, r'%s');"
    "import custom_rasterizer;"
    "print('IMPORT_OK')" % REPO
)

for tag, e in [("PATH+torch+cuda", env)]:
    r = subprocess.run([VENV_PY, "-c", code], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=e)
    print("[%s] rc=%d" % (tag, r.returncode))
    print("  out:", r.stdout.strip()[-200:])
    print("  err:", r.stderr.strip()[-300:])

# 方法 B：Python os.add_dll_directory（先于 import torch）
code_b = (
    "import os;"
    "os.add_dll_directory(r'%s');"
    "os.add_dll_directory(r'%s');"
    "import sys; sys.path.insert(0, r'%s');"
    "import custom_rasterizer;"
    "print('IMPORT_OK_B')" % (VENV_LIB, CUDA_BIN, REPO)
)
r2 = subprocess.run([VENV_PY, "-c", code_b], capture_output=True, text=True,
                    encoding="utf-8", errors="replace")
print("[add_dll_directory] rc=%d" % r2.returncode)
print("  out:", r2.stdout.strip()[-200:])
print("  err:", r2.stderr.strip()[-300:])
print("DLL_FIX_DONE")
