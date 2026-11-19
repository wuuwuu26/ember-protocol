# -*- coding: utf-8 -*-
"""批量把概念图转成 3D 模型（串行，8GB 显存一次只能跑一个）。

用法：
  python tools/hy3d_batch.py airlock crane_arm bunker_vent
"""
import subprocess
import sys
import os
import io
import time

# ⚠️ Windows 控制台默认 GBK，子进程输出含中文/替换字符时 print 会抛
#    UnicodeEncodeError 把整个批处理打断（2026-11-10 踩过：airlock 生成完
#    后脚本崩溃，后面 4 个资产全部没跑）。强制 UTF-8，容错替换。
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace", line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8",
                              errors="replace", line_buffering=True)

HY = r"C:\AI\Hunyuan3D"
PY = os.path.join(HY, "venv", "Scripts", "python.exe")
SCRIPT = os.path.join(HY, "hy3d_asset.py")
IN = os.path.join(HY, "input")

names = sys.argv[1:] or ["airlock", "crane_arm", "bunker_vent"]

for name in names:
    src = os.path.join(IN, "gen_%s.png" % name)
    out = os.path.join(HY, "output", name + ".glb")
    if os.path.exists(out) and os.path.getsize(out) > 100000:
        print("[skip] %s 已存在 %.1f MB" % (name, os.path.getsize(out) / 1048576.0),
              flush=True)
        continue
    if not os.path.exists(src):
        print("[miss] %s 源图不存在" % name, flush=True)
        continue
    print("[3D] === %s ===" % name, flush=True)
    t0 = time.time()
    r = subprocess.run([PY, SCRIPT, "--src", src, "--name", name],
                       cwd=HY, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    el = time.time() - t0
    tail = [l for l in r.stdout.splitlines() if any(
        k in l for k in ("[3D]", "导出", "生成", "顶点", "DONE"))]
    msg = "\n".join(tail[-8:])
    # 双保险：即使编码异常也不能中断批处理
    try:
        print(msg, flush=True)
    except Exception:
        print(msg.encode("ascii", "replace").decode("ascii"), flush=True)
    if os.path.exists(out):
        print("   OK %.1f MB  %.0fs" % (os.path.getsize(out) / 1048576.0, el),
              flush=True)
    else:
        print("   !! 失败 %.0fs\n%s" % (el, r.stderr[-600:]), flush=True)

print("HY3D_BATCH_DONE")
