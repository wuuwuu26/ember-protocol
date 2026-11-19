# -*- coding: utf-8 -*-
"""程序化等离子丝贴图（可平铺）。

用途：曳光带的自发光细节。AI 生图排队太慢时先用这张兜底，
视觉上是"白热丝状电弧"，比纯色自发光多一层流动感。
"""
import numpy as np
from PIL import Image

SIZE = 1024
OUT = r"C:\Users\25227\Documents\robot_game\assets\tex\bolt_plasma.png"

rng = np.random.default_rng(20261026)
ax = np.linspace(0.0, 2.0 * np.pi, SIZE, endpoint=False)
X, Y = np.meshgrid(ax, ax)


def noise(freq, count=26):
    n = np.zeros((SIZE, SIZE), np.float32)
    for _ in range(count):
        fx = int(rng.integers(1, freq))
        fy = int(rng.integers(1, freq))
        ph = float(rng.uniform(0, 2 * np.pi))
        amp = float(rng.uniform(0.25, 1.0))
        n += amp * np.sin(fx * X + fy * Y + ph)
    n -= n.min()
    n /= max(n.max(), 1e-6)
    return n


base = noise(5, 30)
warp = noise(3, 18)

# 域扭曲：让丝状结构不是规整的斜纹
dx = (warp - 0.5) * 1.6
dy = (np.roll(warp, 37, axis=0) - 0.5) * 1.6
warped = (np.sin(3.0 * X + 4.0 * Y + dx * 6.0)
          + np.sin(5.0 * X - 3.0 * Y + dy * 6.0)
          + np.sin(8.0 * X + 7.0 * Y + (dx + dy) * 4.0))
warped = (warped - warped.min()) / max(warped.max() - warped.min(), 1e-6)

# 脊线化：只保留细丝
ridge = 1.0 - np.abs(warped * 2.0 - 1.0)
ridge = np.clip(ridge, 0, 1) ** 7.0
ridge2 = 1.0 - np.abs(base * 2.0 - 1.0)
ridge2 = np.clip(ridge2, 0, 1) ** 14.0
fil = np.clip(ridge * 0.85 + ridge2 * 0.6, 0, 1)

# 少量亮核，避免整张都是均匀细线
hot = np.clip((base - 0.62) / 0.30, 0, 1) ** 3.0
fil = np.clip(fil + hot * 0.8, 0, 1)
fil = np.where(fil < 0.06, 0.0, fil)

img = (np.clip(fil, 0, 1) * 255).astype(np.uint8)
Image.fromarray(img, "L").save(OUT)
print("bolt_plasma.png procedural  mean=%.3f  max=%d" % (fil.mean(), img.max()))
