# -*- coding: utf-8 -*-
"""第一百一十九轮：4 个机甲碎骸的 texgen 高质量贴图批量流水线（串行）。

每个资产：
  1) clean_bg_planes.py   删背景大平面（Blender，幂等）
  2) simplify_for_texgen  减面到 5 万（关键：UV 展开 330s->3s）
  3) texgen_staged.py     官方 texgen PBR 多视图贴图（1024，约 5.7 分钟）
  4) show_asset.py        带贴图展示图

⚠️ 必须串行（8GB 显存），跑前 ComfyUI 已停。
⚠️ 结果 _texgen_final.glb 供 UE 导入。
"""
import subprocess
import sys
import os
import io
import time
import shutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace", line_buffering=True)

ROOT = r"C:\Users\25227\Documents\robot_game"
HY = r"C:\AI\Hunyuan3D"
OUT = os.path.join(HY, "output")
IN = os.path.join(HY, "input")
PY_HY = os.path.join(HY, "venv", "Scripts", "python.exe")
SHOW_DIR = os.path.join(ROOT, "docs", "gen3d_shots")
os.makedirs(SHOW_DIR, exist_ok=True)

sys.path.insert(0, os.path.join(ROOT, "tools"))
from find_blender import find_blender
BLENDER = find_blender()

CLEAN = os.path.join(ROOT, "tools", "blender", "clean_bg_planes.py")
SIMPLIFY = os.path.join(HY, "simplify_for_texgen.py")
TEXGEN = os.path.join(HY, "texgen_staged.py")
SHOW = os.path.join(ROOT, "tools", "blender", "show_asset.py")
LOG_DIR = os.path.join(HY, "output")

NAMES = ["mech_torso_wreck", "severed_mech_arm",
         "mech_head_wreck", "armor_debris"]


def run(args, cwd, tag, timeout=1200):
    print("  [%s]" % tag, flush=True)
    try:
        r = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"


for name in NAMES:
    white = os.path.join(OUT, name + ".glb")
    rgba = os.path.join(IN, "gen_%s_rgba.png" % name)
    nobg = os.path.join(OUT, name + "_nobg.glb")
    lo = os.path.join(OUT, name + "_lo.glb")
    final = os.path.join(OUT, name + "_texgen_final.glb")
    show = os.path.join(SHOW_DIR, "show_%s_texgen.png" % name)

    if not os.path.exists(white) or not os.path.exists(rgba):
        print("%s 缺白模/RGBA，跳过" % name, flush=True)
        continue
    print("════════ %s ════════" % name, flush=True)
    t0 = time.time()

    # 1) 清背景平面（幂等：没杂散面的资产也会输出一个等价文件）
    rc, o, e = run([BLENDER, "-b", "--factory-startup", "--python", CLEAN,
                    "--", white, nobg], ROOT, "清背景", 600)
    if not os.path.exists(nobg):
        print("  清背景失败，用原白模", (e or o)[-200:], flush=True)
        shutil.copy(white, nobg)

    # 2) 减面到 5 万
    rc, o, e = run([PY_HY, SIMPLIFY, nobg, lo, "--faces", "50000"],
                   HY, "减面", 300)
    if not os.path.exists(lo):
        print("  减面失败，跳过", (e or o)[-200:], flush=True)
        continue
    print("  %s" % [l for l in o.splitlines() if "输出:" in l], flush=True)
    time.sleep(2)

    # 3) texgen
    rc, o, e = run([PY_HY, TEXGEN, "--mesh", lo, "--image", rgba,
                    "--out", final, "--res", "1024"],
                   HY, "texgen", 1200)
    if os.path.exists(final):
        stages = [l.strip() for l in o.splitlines()
                  if any(k in l for k in ("delight ", "uv_wrap", "diffusion ",
                                          "bake ", "inpaint ", "导出", "总耗时"))]
        print("  texgen OK %.1f MB" % (os.path.getsize(final)/1048576), flush=True)
        for s in stages:
            print("    " + s, flush=True)
    else:
        print("  texgen 失败", (e or o)[-300:], flush=True)
        continue
    time.sleep(2)

    # 4) 展示图
    rc, o, e = run([BLENDER, "-b", "--factory-startup", "--python", SHOW,
                    "--", final, show], ROOT, "展示图", 600)
    print("  展示图 %s" % ("OK" if os.path.exists(show) else "失败"), flush=True)
    print("  用时 %.0f 秒" % (time.time()-t0), flush=True)

print("TEXGEN_BATCH_DONE", flush=True)
