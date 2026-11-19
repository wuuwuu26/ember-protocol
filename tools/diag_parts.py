# -*- coding: utf-8 -*-
"""验证：直接对原始白模减面（不经 Blender 往返，保持顶点焊接）是否正常。

并列出 4 个原始白模的连通分量（找出背景大平面/底座盘）。
"""
import os
import numpy as np
import trimesh

O = r"C:\AI\Hunyuan3D\output"
NAMES = ["mech_torso_wreck", "severed_mech_arm", "mech_head_wreck", "armor_debris"]

for n in NAMES:
    p = os.path.join(O, n + ".glb")
    m = trimesh.load(p, force="mesh")
    if isinstance(m, trimesh.Scene):
        gs = [g for g in m.geometry.values() if isinstance(g, trimesh.Trimesh)]
        m = trimesh.util.concatenate(gs)
    parts = m.split(only_watertight=False)
    print("%s: faces=%d area=%.3f parts=%d" % (n, len(m.faces), m.area, len(parts)),
          flush=True)
    parts.sort(key=lambda x: -x.area)
    for i, pp in enumerate(parts[:5]):
        ext = pp.extents
        flat = min(ext) / max(max(ext), 1e-9)
        print("    part%d faces=%7d area=%8.3f extents=(%.2f,%.2f,%.2f) flatness=%.4f"
              % (i, len(pp.faces), pp.area, ext[0], ext[1], ext[2], flat), flush=True)

# ── 直接减面原始躯干（welded）验证 ──
print("\n=== 直接减面原始躯干 → 50000 ===", flush=True)
m = trimesh.load(os.path.join(O, "mech_torso_wreck.glb"), force="mesh")
if isinstance(m, trimesh.Scene):
    gs = [g for g in m.geometry.values() if isinstance(g, trimesh.Trimesh)]
    m = trimesh.util.concatenate(gs)
s = m.simplify_quadric_decimation(face_count=50000)
s.export(os.path.join(O, "test_torso_direct.glb"))
print("减面后 faces=%d area=%.3f parts=%d" % (
    len(s.faces), s.area, len(s.split(only_watertight=False))), flush=True)
print("TEST_DONE", flush=True)
