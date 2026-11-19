# -*- coding: utf-8 -*-
"""生成水柱专用流动条纹贴图 T_Jet_Flow（可 tile，竖向流动）。

T_Toxic_Bub 是黑底稀疏白点（99% 纯黑），当水柱条纹几乎看不见。
这张贴图：横向亮暗条带（V 方向密、U 方向匀）+ 细气泡噪点，
沿 V 滚动（Panner speed_y<0）就读作"往下流的水柱"。

输出 PNG 到 ue/Content 之外，再由 import 脚本导入 UE。
"""
import os
import numpy as np
from PIL import Image

OUT = r"C:\Users\25227\Documents\robot_game\tools\asset_src\T_Jet_Flow.png"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
W = H = 256
rng = np.random.default_rng(7)

u = np.linspace(0, 1, W, endpoint=False)[None, :]
v = np.linspace(0, 1, H, endpoint=False)[:, None]

# 1) 沿 V 的横向条带（多层不同频率正弦叠加，可 tile：频率取整数）
bands = (0.5 + 0.5 * np.sin(2 * np.pi * (9 * v + 0.15 * np.sin(2 * np.pi * 3 * u))))
bands += 0.25 * (0.5 + 0.5 * np.sin(2 * np.pi * (23 * v - 0.1 * np.sin(2 * np.pi * 2 * u))))
bands += 0.15 * (0.5 + 0.5 * np.sin(2 * np.pi * (41 * v)))
bands = bands / bands.max()

# 2) 细密气泡噪点（可 tile 的平滑噪声 + 稀疏亮点）
coarse = rng.random((32, 32)).astype(np.float32)
from PIL import Image as _I
noise = np.asarray(
    _I.fromarray((coarse * 255).astype(np.uint8)).resize(
        (W, H), _I.Resampling.BILINEAR), dtype=np.float32) / 255.0
bubbles = (noise > 0.72).astype(np.float32) * (0.6 + 0.4 * rng.random((H, W)))

# 3) 合成：条带为主 + 气泡提亮，整体偏亮但不全白（保留明暗对比）
g = np.clip(0.25 + 0.62 * bands + 0.35 * bubbles, 0, 1)
# R=G=B（灰度）；轻微偏青由材质 emissive 着色，贴图保持中性
rgb = np.dstack([g, g, g])
img = Image.fromarray((rgb * 255).astype(np.uint8), "RGB")
img.save(OUT)

r = (rgb[:, :, 0] * 255)
print("saved", OUT)
print("R: min %.0f max %.0f mean %.1f std %.1f p10 %.0f p90 %.0f" % (
    r.min(), r.max(), r.mean(), r.std(),
    np.percentile(r, 10), np.percentile(r, 90)))
