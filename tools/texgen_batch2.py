# -*- coding: utf-8 -*-
"""第一百一十九轮修正版：机甲碎骸 texgen 高质量贴图批量流水线。

⚠️ 关键教训（第一百一十九轮踩的坑）：
   clean_bg_planes.py 走 Blender GLB 导入/导出会把顶点按面拆分
   （565316 面 -> 557984 个独立连通块），之后任何减面都变成"点云"。
   所以清理和减面必须全程在 trimesh 里做，保持顶点焊接。

流程（每个资产）：
  1) 读原始白模（welded）
  2) 删背景平面：split 成连通块，丢弃"极扁且面积占比大"的块
  3) 减面到 5 万（trimesh quadric，welded 时面积几乎无损）
  4) texgen_staged.py 官方 PBR 多视图贴图（1024，约 6 分钟）
  5) show_asset.py 带贴图展示图

⚠️ 必须串行（8GB 显存）；跑前 ComfyUI 要停。
"""
import os
import sys
import io
import time
import subprocess

import numpy as np
import trimesh

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace", line_buffering=True)

# ── 单实例锁：8GB 显存下绝不能有两个 texgen 并行 ──
LOCK = os.path.join(os.environ.get("TEMP", "."), "opencode", "texgen_batch2.lock")
os.makedirs(os.path.dirname(LOCK), exist_ok=True)
if os.path.exists(LOCK):
    try:
        old = int(open(LOCK).read().strip())
    except Exception:
        old = 0
    alive = False
    if old:
        try:
            import subprocess as _sp
            _r = _sp.run(["tasklist", "/FI", "PID eq %d" % old, "/NH"],
                         capture_output=True, text=True)
            alive = str(old) in (_r.stdout or "")
        except Exception:
            alive = False
    if alive:
        print("另一个 texgen 批量实例在跑（PID %d），本实例退出。" % old, flush=True)
        sys.exit(0)
open(LOCK, "w").write(str(os.getpid()))

import atexit
atexit.register(lambda: os.path.exists(LOCK) and os.remove(LOCK))

ROOT = r"C:\Users\25227\Documents\robot_game"
HY = r"C:\AI\Hunyuan3D"
OUT = os.path.join(HY, "output")
IN = os.path.join(HY, "input")
PY_HY = os.path.join(HY, "venv", "Scripts", "python.exe")
TEXGEN = os.path.join(HY, "texgen_staged.py")
SHOW_DIR = os.path.join(ROOT, "docs", "gen3d_shots")
os.makedirs(SHOW_DIR, exist_ok=True)

sys.path.insert(0, os.path.join(ROOT, "tools"))
from find_blender import find_blender
BLENDER = find_blender()
SHOW = os.path.join(ROOT, "tools", "blender", "show_asset.py")

NAMES = ["mech_torso_wreck", "severed_mech_arm",
         "mech_head_wreck", "armor_debris"]

TARGET_FACES = 50000
FLAT_RATIO = 0.02     # 最薄边/最长边 小于此值视为"平板"
AREA_SHARE = 0.15     # 且面积占总面积 15% 以上才删


def load_welded(path):
    m = trimesh.load(path, force="mesh")
    if isinstance(m, trimesh.Scene):
        gs = [g for g in m.geometry.values() if isinstance(g, trimesh.Trimesh)]
        m = trimesh.util.concatenate(gs)
    return m


def drop_bg_planes(mesh):
    """删掉极扁且面积大的连通块（单图生成的白背景板/地面伪影）。"""
    total = mesh.area
    parts = mesh.split(only_watertight=False)
    if len(parts) <= 1:
        return mesh, 0
    keep = []
    dropped = 0
    for p in parts:
        ext = p.extents
        flat = min(ext) / max(max(ext), 1e-9)
        if flat < FLAT_RATIO and p.area / max(total, 1e-9) > AREA_SHARE:
            dropped += 1
            print("    丢弃平面块: 面%d 面积%.2f 尺寸(%.2f,%.2f,%.2f)"
                  % (len(p.faces), p.area, ext[0], ext[1], ext[2]), flush=True)
        else:
            keep.append(p)
    if not keep:
        return mesh, 0
    out = trimesh.util.concatenate(keep) if len(keep) > 1 else keep[0]
    return out, dropped


def decimate(mesh, target=TARGET_FACES):
    if len(mesh.faces) <= target:
        return mesh
    s = mesh.simplify_quadric_decimation(face_count=target)
    return s if (s is not None and len(s.faces) > 0) else mesh


def run(args, cwd, timeout):
    try:
        r = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"


for name in NAMES:
    src = os.path.join(OUT, name + ".glb")
    rgba = os.path.join(IN, "gen_%s_rgba.png" % name)
    lo = os.path.join(OUT, name + "_tex_lo.glb")
    final = os.path.join(OUT, name + "_texgen_final.glb")
    show = os.path.join(SHOW_DIR, "show_%s_texgen.png" % name)

    if not os.path.exists(src) or not os.path.exists(rgba):
        print("%s 缺白模/RGBA，跳过" % name, flush=True)
        continue

    print("════════ %s ════════" % name, flush=True)
    t0 = time.time()

    # 1) 读 + 清背景平面
    mesh = load_welded(src)
    print("  原始: 面%d 面积%.2f 块%d" % (
        len(mesh.faces), mesh.area,
        len(mesh.split(only_watertight=False))), flush=True)
    mesh, dropped = drop_bg_planes(mesh)
    if dropped:
        print("  清理后: 面%d 面积%.2f" % (len(mesh.faces), mesh.area), flush=True)

    # 2) 减面
    before_area = mesh.area
    mesh = decimate(mesh)
    print("  减面后: 面%d 面积%.2f (原始面积%.2f, 保留%.1f%%)" % (
        len(mesh.faces), mesh.area, before_area,
        100.0 * mesh.area / max(before_area, 1e-9)), flush=True)
    if mesh.area < before_area * 0.7:
        print("  !! 面积塌缩超过 30%%，几何可能被破坏，跳过该资产", flush=True)
        continue
    mesh.export(lo)
    print("  写出 %s %.1f MB" % (os.path.basename(lo),
                                os.path.getsize(lo) / 1048576.0), flush=True)

    # 3) texgen
    rc, o, e = run([PY_HY, TEXGEN, "--mesh", lo, "--image", rgba,
                    "--out", final, "--res", "1024"], HY, 1800)
    if not os.path.exists(final):
        print("  texgen 失败: %s" % (e or o)[-400:], flush=True)
        continue
    print("  texgen OK %.1f MB" % (os.path.getsize(final) / 1048576.0), flush=True)
    for l in o.splitlines():
        s = l.strip()
        if any(k in s for k in ("delight ", "uv_wrap", "diffusion ", "bake ",
                                "inpaint ", "总耗时")):
            print("    " + s, flush=True)

    # 4) 展示图
    rc, o, e = run([BLENDER, "-b", "--factory-startup", "--python", SHOW,
                    "--", final, show], ROOT, 900)
    print("  展示图 %s" % ("OK" if os.path.exists(show) else "失败"), flush=True)
    print("  用时 %.0f 秒" % (time.time() - t0), flush=True)

print("TEXGEN_BATCH2_DONE", flush=True)
