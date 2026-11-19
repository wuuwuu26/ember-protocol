# -*- coding: utf-8 -*-
"""提取 texgen GLB 的 basecolor 贴图，检查是否有纯黑/异常区域。"""
import os
import numpy as np
from PIL import Image
import trimesh

O = r"C:\AI\Hunyuan3D\output"
DUMP = r"C:\Users\25227\AppData\Local\Temp\opencode"
for n in ["mech_torso_wreck", "severed_mech_arm", "mech_head_wreck", "armor_debris"]:
    p = os.path.join(O, n + "_texgen_final.glb")
    m = trimesh.load(p, force="mesh")
    mat = m.visual.material
    img = getattr(mat, "baseColorTexture", None) or getattr(mat, "image", None)
    if img is None:
        print(n, "no baseColorTexture, mat=", type(mat).__name__,
              [a for a in dir(mat) if "exture" in a or "mage" in a])
        continue
    im = img.convert("RGB")
    a = np.asarray(im).astype(np.float32)
    dark = (a.max(2) < 30).mean() * 100
    verydark = (a.max(2) < 60).mean() * 100
    print("%-20s size=%s 纯黑(<%d)占比=%.2f%% 极暗(<60)占比=%.2f%% 均值=%.0f"
          % (n, im.size, 30, dark, verydark, a.mean()))
    im.save(os.path.join(DUMP, "tex_%s.png" % n))
print("DUMP_DONE")
