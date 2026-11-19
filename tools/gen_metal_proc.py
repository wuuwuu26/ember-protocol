# -*- coding: utf-8 -*-
"""程序化钛合金弹壳贴图（可平铺）—— AI 生图排队时的兜底。

生成：
    bolt_metal.png    BaseColor（深冷灰钛合金 + 车削环纹 + 细划痕）
    bolt_metal_n.png  法线（由同一高度场求导）

坐标约定与网格 UV 对齐：
    U = 绕弹轴一圈，V = 沿弹轴 → 贴图的行方向是弹轴，
    所以"一圈圈车削纹"在贴图里是水平线。
"""
import numpy as np
from PIL import Image

SIZE = 1024
TEX = r"C:\Users\25227\Documents\robot_game\assets\tex"

rng = np.random.default_rng(20261026)
ax = np.linspace(0.0, 2.0 * np.pi, SIZE, endpoint=False)
X, Y = np.meshgrid(ax, ax)


def pnoise(freq, count=20, seed=0):
    r = np.random.default_rng(seed)
    n = np.zeros((SIZE, SIZE), np.float32)
    for _ in range(count):
        fx = int(r.integers(1, freq))
        fy = int(r.integers(1, freq))
        ph = float(r.uniform(0, 2 * np.pi))
        n += float(r.uniform(0.3, 1.0)) * np.sin(fx * X + fy * Y + ph)
    n -= n.min()
    n /= max(n.max(), 1e-6)
    return n


# ── 车削环纹：沿 V（行）的高频亮暗，绕 U 完全一致 ──
v = np.linspace(0.0, 1.0, SIZE, endpoint=False)[:, None]
rings = 0.5 + 0.5 * np.sin(v * 2.0 * np.pi * 110.0)
rings = (rings - 0.5) * 2.0                       # -1..1

# ── 拉丝：沿 U 拉长的各向异性噪声（横向细划痕）──
brushed = pnoise(9, 40, 11) * 0.55 + pnoise(23, 50, 12) * 0.30
# 把噪声在 V 方向压扁，形成沿 U 的丝纹
brushed = np.repeat(brushed[::6, :], 6, axis=0)[:SIZE, :]
brushed = 0.55 + (brushed - brushed.mean()) * 0.9

# ── 宏观斑驳：低频冷热差 ──
macro = pnoise(3, 12, 21)
macro = 0.82 + macro * 0.30

h = np.clip(0.45 + rings * 0.22 + (brushed - 0.55) * 0.55, 0, 1)

# 划痕：随机短线段（在 U 方向，即绕圈方向）
scratch = np.zeros((SIZE, SIZE), np.float32)
for _ in range(260):
    y0 = rng.integers(0, SIZE)
    x0 = rng.integers(0, SIZE)
    ln = rng.integers(8, 70)
    bright = rng.uniform(0.25, 0.8)
    xs = (np.arange(ln) + x0) % SIZE
    yy = (y0 + rng.integers(-1, 2)) % SIZE
    scratch[yy, xs] = np.maximum(scratch[yy, xs], bright)

g = np.clip(0.30 + h * 0.42 + macro * 0.18 + scratch * 0.10, 0, 1)

# 冷色钛合金：蓝灰略偏青
tint = np.array([0.55, 0.62, 0.72], np.float32)
base = tint[None, None, :] * (0.14 + 0.78 * (g ** 1.10))[:, :, None]
base = np.clip(base, 0, 1)
Image.fromarray((base * 255).astype(np.uint8), "RGB").save(
    TEX + r"\bolt_metal.png")

# 法线：环纹 + 划痕
height = np.clip(h * 0.8 + scratch * 0.25, 0, 1)
dx = np.zeros_like(height)
dy = np.zeros_like(height)
dx[:, 1:-1] = (height[:, 2:] - height[:, :-2]) * 0.5
dy[1:-1, :] = (height[2:, :] - height[:-2, :]) * 0.5
strength = 2.4
n = np.dstack((-dx * strength, dy * strength, np.ones_like(height)))
n /= np.linalg.norm(n, axis=2, keepdims=True)
nrm = np.clip((n * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
Image.fromarray(nrm, "RGB").save(TEX + r"\bolt_metal_n.png")

print("procedural metal: mean=%.2f max=%d" % (base.mean(), base.max()))
