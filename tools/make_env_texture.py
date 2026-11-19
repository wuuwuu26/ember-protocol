# -*- coding: utf-8 -*-
"""
生成环境的"表面细节"贴图（程序化，可平铺）。
================================================================

和机体的 mech_detail.png 同一套思路（三平面投影 + 可平铺），
但参数按**大尺度工业建筑**调：
    · 板更大、缝更宽 —— 环境贴图在屏幕上覆盖的面积比机体大一个量级，
      用机体的 4x4 密网格铺到 400cm 的地板上会变成一片噪点
    · 锈迹更多、油污更重 —— 地板/墙是长期暴露的
    · 铆钉更大更疏

产出：
    env_detail.png    R=板缝遮罩  G=粗糙度  B=磨损露底  A=高度（存档）
    env_detail_n.png  Sobel 求梯度的法线贴图

⚠️ 磨损放 B 而不是 A：UE 三平面（WorldAlignedTexture）只输出 RGB，
   A 通道传不过去（机体贴图曾因此编译失败）。

用法: python tools/make_env_texture.py [输出目录]
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_detail_texture import (  # noqa: E402
    SIZE, fbm, smoothstep, tileable_gradient)

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else \
    r"C:\Users\25227\Documents\robot_game\assets\tex"
SEED = 77712345


def seam(cells, width_px, phase=0.0):
    """可平铺网格缝：返回 (缝遮罩 1=板面, 到缝线的距离场)。"""
    coord = (np.arange(SIZE, dtype=np.float32) + 0.5) / SIZE
    step = 1.0 / cells

    def dist_to_line(c):
        d = np.abs(((c + phase) % step) - step * 0.5)
        return step * 0.5 - d

    d = np.minimum(dist_to_line(coord)[:, None], dist_to_line(coord)[None, :])
    half = width_px / SIZE * 0.5
    return smoothstep(0.0, half, d), d


def build_plate_mask(rng):
    """三层板缝：2x2 巨型板 + 4x4 中板 + 8x8 细刻线。"""
    m1, _ = seam(2, 18)
    m2, _ = seam(4, 10, phase=0.5 / 4)
    m3, _ = seam(8, 4, phase=0.25 / 8)

    mask = m1
    mask = np.minimum(mask, 0.30 + 0.70 * m2)
    mask = np.minimum(mask, 0.62 + 0.38 * m3)

    # 缝底加噪声，避免"刀切一样干净"
    mask = mask * (0.88 + 0.12 * fbm(rng, SIZE, 6, 3))

    # 大铆钉：2x2 网格的每条边上排一排
    rivet = np.zeros((SIZE, SIZE), np.float32)
    step = SIZE // 2
    per_edge = 5
    for gy in range(2):
        for gx in range(2):
            for k in range(per_edge):
                f = (k + 0.5) / per_edge
                for (ox, oy) in ((f, 0.055), (f, 0.945), (0.055, f), (0.945, f)):
                    cx = (gx + ox) * step
                    cy = (gy + oy) * step
                    rr = 9.0
                    xs = (np.arange(SIZE) - cx + SIZE * 0.5) % SIZE - SIZE * 0.5
                    ys = (np.arange(SIZE) - cy + SIZE * 0.5) % SIZE - SIZE * 0.5
                    r2 = xs[None, :] ** 2 + ys[:, None] ** 2
                    rivet = np.maximum(rivet, smoothstep(rr * rr, 0.0, r2) * 0.30)
    return np.clip(mask + rivet, 0.0, 1.0)


def build_roughness(rng, mask):
    """粗糙度：大块锈蚀 + 水泥灰 + 细颗粒；缝里积垢最粗糙。"""
    rust = fbm(rng, SIZE, 2, 5)
    grime = fbm(rng, SIZE, 5, 4)
    grain = fbm(rng, SIZE, 20, 3)
    r = 0.42 + 0.34 * grime + 0.16 * grain + 0.22 * smoothstep(0.45, 0.9, rust)
    r = r + (1.0 - mask) * 0.40
    # 雨水冲刷的竖向流痕
    streak = fbm(rng, SIZE, 1, 3)
    r += 0.12 * smoothstep(0.5, 0.95, streak)
    return np.clip(r, 0.0, 1.0)


def build_height(rng, mask):
    h = mask * 0.8 + 0.2 * fbm(rng, SIZE, 4, 4)
    return np.clip(h, 0.0, 1.0)


def build_wear(rng, mask):
    """磨损：大面积漆皮剥落 + 长刮痕 + 缝边磨亮。"""
    peel = fbm(rng, SIZE, 3, 4)
    w = smoothstep(0.62, 0.92, peel) * 0.7

    yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    for _ in range(70):
        cx, cy = rng.random() * SIZE, rng.random() * SIZE
        ang = rng.random() * np.pi
        ln = 80 + rng.random() * 500
        thick = 0.8 + rng.random() * 1.8
        dx, dy = np.cos(ang), np.sin(ang)
        px = ((xx - cx + SIZE * 1.5) % SIZE) - SIZE * 0.5
        py = ((yy - cy + SIZE * 1.5) % SIZE) - SIZE * 0.5
        t = np.clip(px * dx + py * dy, -ln * 0.5, ln * 0.5)
        d = np.sqrt((px - t * dx) ** 2 + (py - t * dy) ** 2)
        w = np.maximum(w, smoothstep(thick, 0.0, d) * (0.45 + 0.45 * rng.random()))

    w = np.maximum(w, smoothstep(0.14, 0.0, np.abs(mask - 0.5)) * 0.40)
    return np.clip(w, 0.0, 1.0)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    rng = np.random.default_rng(SEED)

    mask = build_plate_mask(rng)
    rough = build_roughness(rng, mask)
    height = build_height(rng, mask)
    wear = build_wear(rng, mask)

    rgba = np.stack([
        np.clip(mask * 255, 0, 255),
        np.clip(rough * 255, 0, 255),
        np.clip(wear * 255, 0, 255),      # 磨损在 B（材质要用的通道必须在 RGB 里）
        np.clip(height * 255, 0, 255),    # 高度存档在 A
    ], axis=-1).astype(np.uint8)
    p1 = os.path.join(OUT_DIR, "env_detail.png")
    Image.fromarray(rgba, "RGBA").save(p1)
    print("写出 %s" % p1)

    grad = tileable_gradient(SIZE)
    du, dv = grad(height)
    strength = 3.8
    nx = -du * strength
    ny = dv * strength
    nz = np.ones_like(nx)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx / ln, ny / ln, nz / ln
    nrm = np.stack([
        np.clip((nx * 0.5 + 0.5) * 255, 0, 255),
        np.clip((ny * 0.5 + 0.5) * 255, 0, 255),
        np.clip((nz * 0.5 + 0.5) * 255, 0, 255),
    ], axis=-1).astype(np.uint8)
    p2 = os.path.join(OUT_DIR, "env_detail_n.png")
    Image.fromarray(nrm, "RGB").save(p2)
    print("写出 %s" % p2)

    tile = np.tile(rgba[::4, ::4], (2, 2, 1))
    Image.fromarray(tile, "RGBA").convert("RGB").save(
        os.path.join(OUT_DIR, "env_detail_preview.png"))
    print("完成：%dx%d 环境细节四通道" % (SIZE, SIZE))


main()
