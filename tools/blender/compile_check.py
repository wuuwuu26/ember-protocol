# -*- coding: utf-8 -*-
"""用 Blender 5.3 逐个语法编译 46 个脚本，找不兼容处。

注意：只做 py_compile（语法层）；运行时 API 需单独跑代表性脚本验证。
用法（在 Blender 里）：blender -b --python compile_check.py
"""
import bpy
import os
import py_compile
import sys

ROOT = r"C:\Users\25227\Documents\robot_game\tools\blender"
files = sorted(f for f in os.listdir(ROOT) if f.endswith(".py"))
ok, fail = [], []
for f in files:
    p = os.path.join(ROOT, f)
    try:
        py_compile.compile(p, doraise=True, cfile=os.path.join(
            r"C:\Users\25227\AppData\Local\Temp\opencode", f + "c"))
        ok.append(f)
    except Exception as e:
        fail.append((f, str(e)[:100]))

print("COMPILE_CHECK ver=%s" % bpy.app.version_string)
print("OK=%d FAIL=%d" % (len(ok), len(fail)))
for f, e in fail:
    print("  FAIL %s : %s" % (f, e))
print("COMPILE_CHECK_DONE")
