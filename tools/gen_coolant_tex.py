# -*- coding: utf-8 -*-
"""生成冷却液面贴图：高对比水波法线 / 泡沫斑块 / 不规则羽化遮罩。"""
import numpy as np
from PIL import Image

SIZE = 512
OUT = r"C:\Users\25227\Documents\robot_game\assets\tex"

yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
u = xx / SIZE * 2.0 * np.pi
v = yy / SIZE * 2.0 * np.pi

# ── 1. 水波法线（多频叠加，层次更强）──
height = np.zeros((SIZE, SIZE), np.float32)
waves = [
    (1, 1, 0.70, 0.0),
    (2, 1, 0.50, 1.1),
    (1, 3, 0.34, 2.2),
    (3, 2, 0.26, 0.4),
    (4, 3, 0.18, 2.9),
    (2, 6, 0.14, 1.7),
    (7, 4, 0.10, 0.9),
    (5, 9, 0.07, 2.5),
    (9, 13, 0.05, 1.3),
    (13, 7, 0.04, 3.1),
]
for fx, fy, amp, ph in waves:
    height += amp * np.sin(fx * u + fy * v + ph)

gx = np.gradient(height, axis=1)
gy = np.gradient(height, axis=0)
strength = 2.8
n = np.dstack((-gx * strength, -gy * strength, np.ones_like(height)))
n /= np.linalg.norm(n, axis=2, keepdims=True)
normal_rgb = np.clip((n * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
Image.fromarray(normal_rgb, "RGB").save(OUT + r"\coolant_normal.png")

# ── 2. 泡沫斑块（可平铺、气泡感）──
foam = np.zeros((SIZE, SIZE), np.float32)
for fx, fy, amp, ph in [(2, 3, 0.6, 0.2), (5, 2, 0.4, 1.7), (7, 6, 0.3, 2.6),
                        (11, 4, 0.22, 0.9), (13, 11, 0.16, 1.2), (17, 9, 0.12, 2.1)]:
    foam += amp * np.sin(fx * u + fy * v + ph)
foam = (foam - foam.min()) / (foam.max() - foam.min())
foam = np.clip((foam - 0.46) / 0.34, 0, 1)
foam = foam * foam * (3.0 - 2.0 * foam)
foam_img = np.clip(foam * 255.0, 0, 255).astype(np.uint8)
Image.fromarray(foam_img, "L").save(OUT + r"\coolant_foam.png")

# ── 3. 池沿羽化遮罩（更不规则的岸线）──
cx = (SIZE - 1) * 0.5
r = np.sqrt((xx - cx) ** 2 + (yy - cx) ** 2) / (SIZE * 0.5)
shore = np.zeros((SIZE, SIZE), np.float32)
for fx, fy, amp, ph in [(2, 3, 0.045, 0.3), (5, 2, 0.028, 1.9), (3, 7, 0.020, 2.7),
                        (9, 5, 0.012, 0.8), (13, 11, 0.008, 1.4)]:
    shore += amp * np.sin(fx * u + fy * v + ph)
r_eff = r + shore
alpha = np.clip((0.915 - r_eff) / 0.055, 0, 1)
alpha = alpha * alpha * (3.0 - 2.0 * alpha)
alpha_img = np.clip(alpha * 255.0, 0, 255).astype(np.uint8)
Image.fromarray(alpha_img, "L").save(OUT + r"\coolant_opacity.png")

print("coolant textures rebuilt")
