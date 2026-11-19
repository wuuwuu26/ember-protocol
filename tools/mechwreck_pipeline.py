# -*- coding: utf-8 -*-
"""第一百一十八轮：4 个机甲碎骸的完整流水线（串行）。

每个资产：
  1) hy3d_asset.py         单图 -> 3D 白模 GLB
  2) hy3d_texture_batch.py 投影贴图 -> *_tex.glb（自动用 find_blender 的 5.3）
  3) show_asset.py         渲染带贴图展示图 -> docs/gen3d_shots/show_<name>.png

⚠️ 3D 生成吃满 8GB 显存，必须串行；每步之间隔几秒让显存释放。
用法：python tools/mechwreck_pipeline.py
"""
import subprocess
import sys
import os
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace", line_buffering=True)

ROOT = r"C:\Users\25227\Documents\robot_game"
HY = r"C:\AI\Hunyuan3D"
PY_HY = os.path.join(HY, "venv", "Scripts", "python.exe")
BLENDER_SCRIPT = os.path.join(ROOT, "tools", "blender", "show_asset.py")
SHOW_DIR = os.path.join(ROOT, "docs", "gen3d_shots")
os.makedirs(SHOW_DIR, exist_ok=True)

NAMES = ["mech_torso_wreck", "severed_mech_arm",
         "mech_head_wreck", "armor_debris"]

# 用 find_blender 定位（5.3）
sys.path.insert(0, os.path.join(ROOT, "tools"))
from find_blender import find_blender
BLENDER = find_blender()


def run(args, cwd, tag, timeout=1800):
    print("  [%s] %s" % (tag, " ".join(str(a) for a in args[:3])), flush=True)
    try:
        r = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"


for name in NAMES:
    glb = os.path.join(HY, "output", name + ".glb")
    tex = os.path.join(HY, "output", name + "_tex.glb")
    show = os.path.join(SHOW_DIR, "show_%s.png" % name)
    src = os.path.join(HY, "input", "gen_%s.png" % name)

    print("════════ %s ════════" % name, flush=True)
    t0 = time.time()

    # 1) 3D 白模
    if not (os.path.exists(glb) and os.path.getsize(glb) > 100000):
        rc, out, err = run([PY_HY, os.path.join(HY, "hy3d_asset.py"),
                            "--src", src, "--name", name], HY, "3D", 1800)
        if os.path.exists(glb):
            print("  3D OK %.1f MB" % (os.path.getsize(glb) / 1048576), flush=True)
        else:
            print("  !! 3D 失败: %s" % (err[-300:] or out[-300:]), flush=True)
            continue
    else:
        print("  3D 已存在，跳过", flush=True)
    time.sleep(3)

    # 2) 投影贴图
    if not (os.path.exists(tex) and os.path.getsize(tex) > 100000):
        rc, out, err = run([sys.executable,
                            os.path.join(ROOT, "tools", "hy3d_texture_batch.py"),
                            name], ROOT, "贴图", 600)
        if os.path.exists(tex):
            print("  贴图 OK %.1f MB" % (os.path.getsize(tex) / 1048576), flush=True)
        else:
            print("  !! 贴图失败: %s" % (err[-300:] or out[-300:]), flush=True)
            continue
    else:
        print("  贴图已存在，跳过", flush=True)
    time.sleep(2)

    # 3) 展示图
    rc, out, err = run([BLENDER, "-b", "--factory-startup",
                        "--python", BLENDER_SCRIPT, "--",
                        tex, show], ROOT, "展示图", 600)
    if os.path.exists(show):
        print("  展示图 OK -> %s" % show, flush=True)
    else:
        print("  !! 展示图失败: %s" % (err[-300:] or out[-300:]), flush=True)

    print("  用时 %.0f 秒" % (time.time() - t0), flush=True)

print("MECHWRECK_PIPELINE_DONE", flush=True)
