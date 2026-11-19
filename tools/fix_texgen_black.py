# -*- coding: utf-8 -*-
"""修复 texgen basecolor 的"黑洞"（第一百一十九轮）。

问题：Hunyuan3D texgen 多视图扩散只在 6 个视角可见面生成贴图，
高复杂度碎骸的自遮挡面烘焙不到 → UV 贴图里 25~36% 是纯黑，
UE 里表现为装甲上的黑斑（Blender 固定灯光恰好没照到，看不出来）。

修复：把 basecolor 中"极暗且低饱和"的区域判为未烘焙空洞，
用 cv2.inpaint 从邻近有效像素扩散填充，再导回 GLB。

用法：venv\\\\python fix_texgen_black.py
"""
import os
import numpy as np
import trimesh
from PIL import Image

O = r"C:\AI\Hunyuan3D\output"
NAMES = ["mech_torso_wreck", "severed_mech_arm", "mech_head_wreck", "armor_debris"]

try:
    import cv2
    HAS_CV2 = True
except Exception:
    HAS_CV2 = False
    print("!! cv2 不可用，用 PIL/NumPy 近似填充")


def fix_image(img):
    rgb = np.asarray(img.convert("RGB")).astype(np.uint8)
    mx = rgb.max(2)
    mn = rgb.min(2)
    # 未烘焙空洞：极暗（<48）。用宽松阈值一次吃掉黑边过渡，
    # 但保留"有意设计"的深色部件（那些通常带颜色/高光，不是纯黑）。
    # 这里额外要求低饱和，避免误伤暗色金属/青绿件。
    hole = (mx < 48) & ((mx - mn) < 40)
    # 再吃掉零星暗点（形态学闭运算的补集交给 inpaint）
    mask = (hole.astype(np.uint8) * 255)
    if HAS_CV2:
        # 稍微膨胀 mask，覆盖黑区边缘的半黑过渡像素
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.dilate(mask, k, iterations=1)
        out = cv2.inpaint(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), mask,
                          7, cv2.INPAINT_TELEA)
        out = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
    else:
        # 近似：黑区填邻域均值（迭代扩散）
        out = rgb.astype(np.float32)
        valid = ~hole
        # 用整体中位色兜底（简单但足够去掉纯黑）
        med = np.median(rgb[valid], axis=0) if valid.any() else np.array([200, 200, 200])
        out[hole] = med
        out = out.clip(0, 255).astype(np.uint8)
    return Image.fromarray(out), float(hole.mean())


for n in NAMES:
    src = os.path.join(O, n + "_texgen_final.glb")
    dst = os.path.join(O, n + "_texgen_fixed.glb")
    m = trimesh.load(src, force="mesh")
    if isinstance(m, trimesh.Scene):
        gs = [g for g in m.geometry.values() if isinstance(g, trimesh.Trimesh)]
        m = trimesh.util.concatenate(gs)
    mat = m.visual.material
    img = mat.baseColorTexture
    if img is None:
        print("%-20s 无贴图，跳过" % n)
        continue
    fixed, ratio = fix_image(img)
    mat.baseColorTexture = fixed
    # 保留 UV
    m.export(dst)
    a = np.asarray(fixed.convert("RGB")).astype(np.float32)
    print("%-20s 修复 %.1f%% 黑区 -> 纯黑占比 %.2f%% 均值 %.0f  %.1f MB"
          % (n, ratio * 100, (a.max(2) < 30).mean() * 100, a.mean(),
             os.path.getsize(dst) / 1048576.0))
    # 存修复后贴图供查看
    fixed.save(r"C:\Users\25227\AppData\Local\Temp\opencode\fixed_%s.png" % n)
print("FIX_DONE")
