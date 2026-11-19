"""
余火协议 · 多套 4K 表面纹理生成
================================================
之前的 detail / env 两张图是"机体"和"地面"专用的。场景里还有涂装钢板、
锈蚀废料、混凝土、细密金属 —— 全用同一张纹理，近看就是"贴了同一张壁纸"。

本脚本参数化生成多套，每套输出：
    <name>_detail.png    RGBA = (面板遮罩, 粗糙度, 磨损, 高度)
    <name>_detail_n.png  法线（从高度图环绕差分）

预设（都用 4096）:
    paint     涂装钢板 —— 大板缝少、板面平、有掉漆斑
    concrete  混凝土   —— 细密分格、颗粒粗、有积水渍
    rust      锈蚀金属 —— 斑驳锈斑、起皮、深坑

复用 make_detail_texture 的 fbm / seam_grid / smoothstep / shift_noise /
tileable_gradient，保证噪声语言和机体纹理一致。

用法:
    python tools/make_surface_set.py            # 全部
    python tools/make_surface_set.py paint      # 只做一种
"""

import os
import sys

import numpy as np
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from make_detail_texture import (      # noqa: E402
    SIZE, S, px, fbm, smoothstep, seam_grid, shift_noise, tileable_gradient)

OUT_DIR = os.path.join(os.path.dirname(_HERE), "assets", "tex")


# ═══════════════════════════════════════════════════════════
# 预设
# ═══════════════════════════════════════════════════════════

PRESETS = {
    # 涂装钢板：墙、集装箱、外壳
    "paint": dict(
        cells=2, seam_px=px(14), sub_cells=4, sub_px=px(6),
        plate_lo=0.72, plate_hi=1.00,      # 板面起伏小（喷漆后是平的）
        grime=0.55, rivet=0.0,             # 少污渍、不撒铆钉
        rough_base=0.38, rough_var=0.26,
        chip=0.55,                         # 掉漆强度
        chip_scale=7,
        height_amt=0.72,
        seed=7101,
    ),
    # 混凝土：地面、基座
    "concrete": dict(
        cells=4, seam_px=px(9), sub_cells=8, sub_px=px(4),
        plate_lo=0.55, plate_hi=0.95,
        grime=1.00, rivet=0.0,
        rough_base=0.62, rough_var=0.34,
        chip=0.18,                         # 少量露骨料
        chip_scale=12,
        height_amt=0.60,
        seed=7202,
    ),
    # 锈蚀金属：废料堆、管道、旧构件
    "rust": dict(
        cells=3, seam_px=px(11), sub_cells=6, sub_px=px(5),
        plate_lo=0.42, plate_hi=0.92,
        grime=1.30, rivet=1.0,
        rough_base=0.68, rough_var=0.30,
        chip=1.00,                         # 大量起皮
        chip_scale=5,
        height_amt=0.85,
        seed=7303,
    ),
}


# ═══════════════════════════════════════════════════════════
# 通道构建
# ═══════════════════════════════════════════════════════════

def build(preset, rng):
    cells = preset["cells"]
    sub = preset["sub_cells"]

    m1, _ = seam_grid(SIZE, cells, preset["seam_px"])
    m2, _ = seam_grid(SIZE, sub, preset["sub_px"], phase=0.5 / sub)
    mask = np.minimum(m1, 0.30 + 0.70 * m2)

    n = fbm(rng, SIZE, 9, 3)
    mask = mask * (0.92 + 0.08 * n)

    # 板面明暗：大尺度污渍 + 中频斑块
    big = fbm(rng, SIZE, 2, 4)
    mid = fbm(rng, SIZE, 6, 4)
    grime = 0.62 * big + 0.38 * mid
    grime = (grime - grime.min()) / max(grime.max() - grime.min(), 1e-6)
    grime = np.clip(grime * preset["grime"], 0.0, 1.0)
    lo, hi = preset["plate_lo"], preset["plate_hi"]
    plate = lo + (hi - lo) * (1.0 - grime)

    panel = mask * plate

    # 铆钉（只给需要金属感的预设）
    if preset["rivet"] > 0.01:
        rivet = np.zeros((SIZE, SIZE), np.float32)
        step = SIZE // cells
        for gy in range(cells):
            for gx in range(cells):
                for (ox, oy) in ((0.5, 0.0), (0.0, 0.5), (1.0, 0.5), (0.5, 1.0)):
                    cx = ((gx + ox) * step) % SIZE
                    cy = ((gy + oy) * step) % SIZE
                    rivet = np.maximum(rivet, shift_noise(SIZE, cx, cy, 5.5 * S))
        panel = panel * (1.0 - 0.42 * preset["rivet"] * rivet)

    # 掉漆 / 起皮：低频斑块阈值化（比随机点更像真实的漆面剥落）
    chip_n = fbm(rng, SIZE, preset["chip_scale"], 3)
    chip = smoothstep(0.62, 0.86, chip_n) * preset["chip"]
    # 掉漆处露出更暗的底材
    panel = panel * (1.0 - 0.38 * chip)

    # 粗糙度
    g = fbm(rng, SIZE, 18, 3)
    rough = preset["rough_base"] + preset["rough_var"] * big + 0.10 * g
    rough = rough + (1.0 - mask) * 0.28          # 缝里积垢
    rough = rough + 0.30 * chip                  # 掉漆处更粗糙
    rough = np.clip(rough, 0.0, 1.0)

    # 高度
    h = fbm(rng, SIZE, 8, 4)
    height = mask * preset["height_amt"] + 0.28 * h
    height = height - 0.30 * chip
    height = np.clip(height, 0.0, 1.0)

    # 磨损（B 通道）：掉漆区 + 稀疏刮痕
    wear = np.clip(chip * 0.85, 0.0, 1.0)
    yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    for _ in range(40):
        cx, cy = rng.random() * SIZE, rng.random() * SIZE
        ang = rng.random() * np.pi
        ln = (25 + rng.random() * 160) * S
        thick = (0.5 + rng.random() * 0.8) * S
        dx, dy = np.cos(ang), np.sin(ang)
        pxx = ((xx - cx + SIZE * 1.5) % SIZE) - SIZE * 0.5
        pyy = ((yy - cy + SIZE * 1.5) % SIZE) - SIZE * 0.5
        t = np.clip(pxx * dx + pyy * dy, -ln * 0.5, ln * 0.5)
        d = np.sqrt((pxx - t * dx) ** 2 + (pyy - t * dy) ** 2)
        wear = np.maximum(wear, smoothstep(thick, 0.0, d) * (0.4 + 0.5 * rng.random()))

    return panel, rough, wear, height, mask


def make(name, preset):
    rng = np.random.default_rng(preset["seed"])
    panel, rough, wear, height, mask = build(preset, rng)

    rgba = np.stack([
        np.clip(panel * 255, 0, 255),
        np.clip(rough * 255, 0, 255),
        np.clip(wear * 255, 0, 255),
        np.clip(height * 255, 0, 255),
    ], axis=-1).astype(np.uint8)
    p1 = os.path.join(OUT_DIR, "%s_detail.png" % name)
    Image.fromarray(rgba, "RGBA").save(p1)

    grad = tileable_gradient(SIZE)
    du, dv = grad(height)
    strength = 3.4
    nx, ny = -du * strength, dv * strength
    nz = np.ones_like(nx)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    nrm = np.stack([
        np.clip((nx / ln * 0.5 + 0.5) * 255, 0, 255),
        np.clip((ny / ln * 0.5 + 0.5) * 255, 0, 255),
        np.clip((nz / ln * 0.5 + 0.5) * 255, 0, 255),
    ], axis=-1).astype(np.uint8)
    p2 = os.path.join(OUT_DIR, "%s_detail_n.png" % name)
    Image.fromarray(nrm, "RGB").save(p2)

    print("  %-10s 面板均值=%.3f 粗糙均值=%.3f 磨损均值=%.3f → %s"
          % (name, panel.mean(), rough.mean(), wear.mean(),
             os.path.basename(p1)))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    want = sys.argv[1:] or list(PRESETS.keys())
    print("生成 %d 套 4K 表面纹理（%d×%d）" % (len(want), SIZE, SIZE))
    for name in want:
        if name not in PRESETS:
            print("  ❌ 未知预设 %s" % name)
            continue
        make(name, PRESETS[name])
    print("完成。")


if __name__ == "__main__":
    main()
