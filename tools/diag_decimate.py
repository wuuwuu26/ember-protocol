# -*- coding: utf-8 -*-
"""诊断：减面后网格为何变成"点云"。对比面数/总面积/连通分量/退化面比例。"""
import os
import numpy as np
import trimesh

O = r"C:\AI\Hunyuan3D\output"
NAMES = [
    "mech_torso_wreck.glb",
    "mech_torso_wreck_nobg.glb",
    "mech_torso_wreck_lo.glb",
    "mech_torso_wreck_bdec.glb",
    "mech_torso_wreck_texgen_final.glb",
]

for n in NAMES:
    p = os.path.join(O, n)
    if not os.path.exists(p):
        print("%-38s MISSING" % n, flush=True)
        continue
    try:
        m = trimesh.load(p, force="mesh")
        if isinstance(m, trimesh.Scene):
            gs = [g for g in m.geometry.values() if isinstance(g, trimesh.Trimesh)]
            m = trimesh.util.concatenate(gs)
        ta = m.triangles
        cr = np.cross(ta[:, 1] - ta[:, 0], ta[:, 2] - ta[:, 0])
        ar = 0.5 * np.linalg.norm(cr, axis=1)
        deg = float((ar < 1e-12).mean()) * 100
        parts = len(m.split(only_watertight=False))
        print("%-38s faces=%7d area=%9.3f parts=%6d degenerate=%5.1f%%"
              % (n, len(m.faces), m.area, parts, deg), flush=True)
    except Exception as e:
        print("%-38s ERR %s" % (n, str(e)[:70]), flush=True)
print("DIAG_DONE", flush=True)
