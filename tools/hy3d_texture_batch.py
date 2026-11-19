# -*- coding: utf-8 -*-
"""批量给 Hunyuan3D 资产做投影贴图（第一百一十轮）。

对 C:\\AI\\Hunyuan3D\\output\\<name>.glb + input\\gen_<name>.png
-> 输出 <name>_tex.glb（含 2048 投影贴图）

用法：python tools/hy3d_texture_batch.py airlock crane_arm ...
"""
import subprocess
import sys
import os
import io
import time

# 从共享模块自动定位 Blender（按版本从高到低，装了 5.3 就自动用 5.3）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from find_blender import find_blender

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace", line_buffering=True)

BLENDER = find_blender()
SCRIPT = r"C:\AI\Hunyuan3D\texture_project_auto.py"
OUT = r"C:\AI\Hunyuan3D\output"
IN = r"C:\AI\Hunyuan3D\input"

names = sys.argv[1:] or ["pipe_junction", "airlock", "crane_arm",
                         "bunker_vent", "mech_core", "generator"]

for name in names:
    mesh = os.path.join(OUT, name + ".glb")
    image = os.path.join(IN, "gen_%s.png" % name)
    dest = os.path.join(OUT, name + "_tex.glb")
    if not os.path.exists(mesh):
        print("[miss] %s 模型不存在" % name, flush=True)
        continue
    if not os.path.exists(image):
        print("[miss] %s 参考图不存在" % name, flush=True)
        continue
    if os.path.exists(dest) and os.path.getsize(dest) > 100000:
        print("[skip] %s_tex.glb 已存在 %.1f MB" %
              (name, os.path.getsize(dest) / 1048576.0), flush=True)
        continue
    print("[tex] === %s ===" % name, flush=True)
    t0 = time.time()
    r = subprocess.run(
        [BLENDER, "-b", "--factory-startup", "--python", SCRIPT, "--",
         "--mesh", mesh, "--image", image, "--out", dest],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    el = time.time() - t0
    if os.path.exists(dest):
        print("   OK %.1f MB  %.0fs" % (os.path.getsize(dest) / 1048576.0, el),
              flush=True)
    else:
        tail = (r.stdout or "")[-500:] + (r.stderr or "")[-300:]
        print("   !! 失败 %.0fs\n%s" % (el, tail), flush=True)

print("HY3D_TEXTURE_BATCH_DONE")
