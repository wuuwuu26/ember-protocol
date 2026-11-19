"""
余火协议 · 装甲板纹理（4K）
================================================
为什么重写：之前的版本生成的是"瓷砖墙" —— 等分网格 + 纯黑缝 + 几乎看不见的螺栓。
真实装甲板在渲染里之所以"像装甲"，靠的是五个视觉信号，缺一个就塌：

  1. **倒角高光（bevel）** —— 板边有一圈 5~10mm 的斜面，斜光打上去是一条亮线。
     ★ 这是最关键的一条。没有倒角，板就是"画在地面上的方格"。
  2. **凹槽有深度** —— 缝底比板面低 8~10mm，AO 自然把缝压暗（不是涂黑）
  3. **每块板独立的明暗** —— 同批材料也有色差，补过漆的明显不同
  4. **螺栓沿缝排布** —— 间距 10cm 左右，往板内缩 2cm
  5. **板面有结构** —— 格栅、圆孔阵列、压筋

通道约定（必须和 ue/Scripts/make_surface_materials.py 一致）：
    R  板面亮度（乘到 BaseColor 上；1.0 = 不改变）
    G  粗糙度（叠加到材质 Roughness）
    B  磨损（朝 WearTint 插值）
    A  高度（材质用它算**凹槽 AO**，并生成法线）

★ 所有尺寸都写成**世界单位**，由 PX_PER_M 换算成像素。
  之前用"1024 基准 × S"的写法，4K 下最小板块变成 660px（0.52m），
  整张图只有 28 块板 —— 这就是"看起来不像装甲"的直接原因。

用法:
    python tools/make_armor_texture.py
"""

import os
import sys

import numpy as np
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from make_detail_texture import SIZE, fbm, smoothstep, shift_noise  # noqa: E402

OUT_DIR = os.path.join(os.path.dirname(_HERE), "assets", "tex")
SEED = 20261024

# ═══════════════════════════════════════════════════════════
# 世界尺度参数（必须和 build_chassis.py 的 cube_uv(size_m=3.2) 一致）
# ═══════════════════════════════════════════════════════════

TILE_M = 3.2                 # 一张贴图铺多少米（= cube_uv 的 size_m）
PX_PER_M = SIZE / TILE_M     # 1280 px/m

PANEL_MIN_M = 0.085          # BSP 最小板块 8.5cm
PANEL_DEPTH = 7              # 递归深度 → 约 128 块，平均 28cm
SEAM_M = 0.022               # 凹槽宽 22mm（12mm 在游戏距离下只有 1~2 像素）
BEVEL_M = 0.016              # 倒角宽 16mm（凹槽外侧）
BOLT_R_M = 0.009             # 螺栓半径 9mm
BOLT_GAP_M = 0.110           # 螺栓间距 11cm
BOLT_INSET_M = 0.020         # 螺栓离缝 2cm（落在板面上）

H_PLATE = 1.00               # 板面高度
H_BEVEL = 0.58               # 倒角高度
H_GROOVE = 0.06              # 槽底高度
NORMAL_STRENGTH = 3.0


def m(v):
    """米 → 像素。"""
    return max(1, int(round(v * PX_PER_M)))


# ═══════════════════════════════════════════════════════════
# 1. BSP 分割 → 不规则装甲板
# ═══════════════════════════════════════════════════════════

def bsp_panels(size, min_px, max_depth, rng):
    """递归二分割，返回 [(x0,y0,x1,y1), ...]。

    每次沿**长边**切，切点在 32%~68% 之间随机 —— 板块大小天然不均匀，
    也不会出现"全是正方形"的呆板排列。
    """
    rects = []

    def split(x0, y0, x1, y1, depth):
        w, h = x1 - x0, y1 - y0
        if depth >= max_depth or (w < min_px * 1.5 and h < min_px * 1.5):
            rects.append((x0, y0, x1, y1))
            return
        if w >= h:
            cut = x0 + int(w * rng.uniform(0.32, 0.68))
            cut = max(x0 + min_px, min(x1 - min_px, cut))
            split(x0, y0, cut, y1, depth + 1)
            split(cut, y0, x1, y1, depth + 1)
        else:
            cut = y0 + int(h * rng.uniform(0.32, 0.68))
            cut = max(y0 + min_px, min(y1 - min_px, cut))
            split(x0, y0, x1, cut, depth + 1)
            split(x0, cut, x1, y1, depth + 1)

    split(0, 0, size, size, 0)
    return rects


def build_panels(size, rng):
    rects = bsp_panels(size, m(PANEL_MIN_M), PANEL_DEPTH, rng)
    label = np.zeros((size, size), np.int32)
    for i, (x0, y0, x1, y1) in enumerate(rects):
        label[y0:y1, x0:x1] = i + 1

    n = len(rects) + 1
    # 每块板的色差：大部分接近 0.86，少数"补过漆"的明显不同
    tone = rng.normal(0.80, 0.090, n).astype(np.float32)
    patch = rng.random(n) < 0.13
    tone[patch] *= rng.uniform(0.82, 0.93, patch.sum())
    tone = np.clip(tone, 0.56, 1.00)
    tone[0] = 0.86

    rough = rng.normal(0.54, 0.06, n).astype(np.float32)
    rough[patch] = rng.uniform(0.36, 0.46, patch.sum())   # 补漆更光滑
    rough = np.clip(rough, 0.30, 0.76)
    return label, tone, rough, rects


# ═══════════════════════════════════════════════════════════
# 2. 缝 / 倒角 / 螺栓 / 板面细节
# ═══════════════════════════════════════════════════════════

def edge_band(label, width_px):
    """label 边界向内/外各扩 width_px//2 → 布尔遮罩。"""
    edge = np.zeros(label.shape, bool)
    for ax in (0, 1):
        edge |= (label != np.roll(label, 1, axis=ax))
        edge |= (label != np.roll(label, -1, axis=ax))
    band = edge.copy()
    for k in range(1, width_px // 2 + 1):
        band |= np.roll(edge, k, axis=0) | np.roll(edge, -k, axis=0)
        band |= np.roll(edge, k, axis=1) | np.roll(edge, -k, axis=1)
    return band


def overlay_panels(size, rects, rng):
    """在部分板上再叠一块小补强板（"板上板"，装甲的层次感来源）。"""
    label2 = np.zeros((size, size), np.int32)
    min_px = m(0.16)
    for idx, (x0, y0, x1, y1) in enumerate(rects):
        if rng.random() > 0.42:
            continue
        w, h = x1 - x0, y1 - y0
        if w < min_px or h < min_px:
            continue
        pw = int(w * rng.uniform(0.36, 0.66))
        ph = int(h * rng.uniform(0.36, 0.66))
        px = x0 + int((w - pw) * rng.uniform(0.15, 0.85))
        py = y0 + int((h - ph) * rng.uniform(0.15, 0.85))
        label2[py:py + ph, px:px + pw] = 1000 + idx
    return label2


def stamp_dot(arr, cx, cy, sigma, value, wrap=True):
    """在 arr 上盖一个高斯圆点（**只算局部窗口**）。

    ⚠️ 不能用 make_detail_texture.shift_noise —— 它每次都建一张
    全尺寸 (4096², float64 = 134MB) 的数组。螺栓要盖上千个，
    上千次 × 134MB 直接把进程撑死（实测被系统 SIGTERM）。
    这里只碰 3σ 见方的小块，开销和贴图尺寸无关。
    """
    rad = int(sigma * 3.0) + 1
    x0, x1 = int(cx) - rad, int(cx) + rad + 1
    y0, y1 = int(cy) - rad, int(cy) + rad + 1
    if not wrap and (x0 < 0 or y0 < 0 or x1 > arr.shape[1] or y1 > arr.shape[0]):
        return
    xs = np.arange(x0, x1) - cx
    ys = np.arange(y0, y1) - cy
    g = np.exp(-(xs[None, :] ** 2 + ys[:, None] ** 2) / (2.0 * sigma * sigma))
    g *= value
    if wrap:
        idx_y = np.arange(y0, y1) % arr.shape[0]
        idx_x = np.arange(x0, x1) % arr.shape[1]
        sub = arr[np.ix_(idx_y, idx_x)]
        np.maximum(sub, g, out=sub)
        arr[np.ix_(idx_y, idx_x)] = sub
    else:
        sub = arr[y0:y1, x0:x1]
        np.maximum(sub, g, out=sub)


def bolts(size, rects, rng):
    """沿每块板四边等距撒螺栓。"""
    b = np.zeros((size, size), np.float32)
    inset = m(BOLT_INSET_M)
    gap = m(BOLT_GAP_M)
    rad = m(BOLT_R_M)
    for (x0, y0, x1, y1) in rects:
        edges = ((x0 + inset, y0 + inset, x1 - inset, y0 + inset),
                 (x0 + inset, y1 - inset, x1 - inset, y1 - inset),
                 (x0 + inset, y0 + inset, x0 + inset, y1 - inset),
                 (x1 - inset, y0 + inset, x1 - inset, y1 - inset))
        for (ax, ay, bx, by) in edges:
            ln = max(abs(bx - ax), abs(by - ay))
            if ln < gap * 1.6:
                continue
            k = max(2, int(ln / gap))
            for i in range(1, k):
                t = i / float(k) + rng.uniform(-0.05, 0.05)
                px = ax + (bx - ax) * t
                py = ay + (by - ay) * t
                stamp_dot(b, px, py, rad * rng.uniform(0.86, 1.14), 1.0)
    return b


def panel_details(size, rects, rng):
    """板面结构：横格栅 / 圆孔阵列 / 压筋。"""
    add = np.zeros((size, size), np.float32)
    min_px = m(0.13)
    for idx, (x0, y0, x1, y1) in enumerate(rects):
        w, h = x1 - x0, y1 - y0
        if w < min_px or h < min_px:
            continue
        roll = rng.random()
        if roll > 0.40:
            continue
        mg = m(0.018)                       # 边距
        if roll < 0.16:
            # 横格栅：一排细槽（散热/减重）
            slat = m(0.006)
            gap = m(0.011)
            y = y0 + mg
            while y < y1 - mg - slat:
                add[y:y + slat, x0 + mg:x1 - mg] = np.maximum(
                    add[y:y + slat, x0 + mg:x1 - mg], 0.60)
                y += slat + gap
        elif roll < 0.30:
            # 圆孔阵列（减重孔 / 紧固点阵列）
            r = m(0.005)
            step = m(0.024)
            yy = y0 + mg + r
            while yy < y1 - mg - r:
                xx = x0 + mg + r
                while xx < x1 - mg - r:
                    stamp_dot(add, xx, yy, r, 0.55)
                    xx += step
                yy += step
        else:
            # 压筋：一条贯穿板的细凸线
            if w > h:
                yc = y0 + h // 2
                add[yc - m(0.004):yc + m(0.004), x0 + mg:x1 - mg] = 0.25
            else:
                xc = x0 + w // 2
                add[y0 + mg:y1 - mg, xc - m(0.004):xc + m(0.004)] = 0.25
    return add


# ═══════════════════════════════════════════════════════════
# 3. 组装
# ═══════════════════════════════════════════════════════════

def scratches(size, rng, count):
    """稀疏刮痕：只在局部窗口内计算（全图算 40 次太慢）。"""
    out = np.zeros((size, size), np.float32)
    for _ in range(count):
        cx, cy = rng.random() * size, rng.random() * size
        ang = rng.random() * np.pi
        ln = m(0.03 + rng.random() * 0.22)
        thick = max(1.0, m(0.0012 + rng.random() * 0.0016))
        dx, dy = np.cos(ang), np.sin(ang)
        # 只算包围盒（留 3 像素余量）
        pad = int(ln * 0.5) + 4
        x0, x1 = max(0, int(cx) - pad), min(size, int(cx) + pad)
        y0, y1 = max(0, int(cy) - pad), min(size, int(cy) + pad)
        if x1 - x0 < 3 or y1 - y0 < 3:
            continue
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        pxx, pyy = xx - cx, yy - cy
        t = np.clip(pxx * dx + pyy * dy, -ln * 0.5, ln * 0.5)
        d = np.sqrt((pxx - t * dx) ** 2 + (pyy - t * dy) ** 2)
        val = smoothstep(thick, 0.0, d) * (0.20 + 0.30 * rng.random())
        np.maximum(out[y0:y1, x0:x1], val, out=out[y0:y1, x0:x1])
    return out


def make(name="mech"):
    rng = np.random.default_rng(SEED)
    label, tone, prough, rects = build_panels(SIZE, rng)
    side = (SIZE * SIZE / max(len(rects), 1)) ** 0.5
    print("  装甲板: %d 块，平均 %.0fpx = %.0fcm"
          % (len(rects), side, side / PX_PER_M * 100))

    # ── 凹槽 + 倒角 ──
    # core = 槽底；cham = 槽外侧的斜面（板自己的边被倒角）
    seam_core = edge_band(label, m(SEAM_M))
    seam_cham = edge_band(label, m(SEAM_M) + 2 * m(BEVEL_M)) & ~seam_core

    # ── 补强板 ──
    label2 = overlay_panels(SIZE, rects, rng)
    over = (label2 > 0).astype(np.float32)
    seam2_core = edge_band(np.where(label2 > 0, label2, 0), m(SEAM_M)) & (label2 > 0)
    seam2_cham = (edge_band(np.where(label2 > 0, label2, 0),
                            m(SEAM_M) + 2 * m(BEVEL_M)) & (label2 > 0)
                  & ~seam2_core)

    bolt = bolts(SIZE, rects, rng)
    detail = panel_details(SIZE, rects, rng)

    # ── R：板面亮度 ──
    tone_map = np.take(tone, label)
    grime = fbm(rng, SIZE, 4, 4)
    grime = (grime - grime.min()) / max(grime.max() - grime.min(), 1e-6)
    panel = tone_map * (0.90 + 0.10 * grime)

    # 倒角高光：★ 装甲"像装甲"的第一信号
    # 斜光打在 10mm 斜面上是一条细亮线，没有它板边就是一条平的黑缝。
    panel = panel * (1.0 + 0.28 * seam_cham)
    panel = panel * (1.0 + 0.20 * seam2_cham)
    # 补强板略亮（更新）+ 自己的缝压暗
    panel = panel * (1.0 + 0.06 * over)
    panel = panel * (1.0 - 0.20 * seam2_core)
    # 板面结构（格栅/圆孔/压筋）
    panel = panel * (1.0 - 0.34 * detail)
    # 螺栓：凸台外圈提亮 + 中心略暗（凹六角）
    panel = panel * (1.0 + 0.12 * bolt)
    panel = panel * (1.0 - 0.18 * smoothstep(0.72, 1.0, bolt))
    # 槽底压暗（R 上给一点，主要靠 AO）
    panel = panel * (1.0 - 0.38 * seam_core)
    panel = np.clip(panel, 0.0, 1.0)

    # ── G：粗糙度 ──
    rough_map = np.take(prough, label)
    grain = fbm(rng, SIZE, 26, 3)
    rough = (rough_map + 0.09 * (grain - 0.5) + 0.16 * seam_core
             - 0.08 * bolt)
    rough = np.clip(rough, 0.0, 1.0)

    # ── A：高度 ──
    # 板面 1.0 → 倒角 0.70 → 槽底 0.16。三级台阶在法线里就是"板厚 + 倒角 + 槽"。
    height = (H_PLATE
              - (H_PLATE - H_BEVEL) * seam_cham.astype(np.float32)
              - (H_BEVEL - H_GROOVE) * seam_core.astype(np.float32))
    height = height + 0.10 * over
    height = height - (H_PLATE - H_BEVEL) * 0.8 * seam2_cham.astype(np.float32)
    height = height - (H_BEVEL - H_GROOVE) * 0.8 * seam2_core.astype(np.float32)
    height = height + 0.09 * bolt - 0.10 * detail
    micro = fbm(rng, SIZE, 52, 3)
    height = np.clip(height + 0.05 * (grain - 0.5) + 0.04 * (micro - 0.5), 0.0, 1.0)

    # ── B：磨损 ──
    # 倒角处最先掉漆（棱角磨损），再叠稀疏刮痕
    wear = (0.42 * seam_cham.astype(np.float32)
            * (0.45 + 0.55 * fbm(rng, SIZE, 18, 2)))
    wear = np.maximum(wear, scratches(SIZE, rng, 42))
    wear = np.clip(wear, 0.0, 1.0)

    rgba = np.stack([
        np.clip(panel * 255, 0, 255),
        np.clip(rough * 255, 0, 255),
        np.clip(wear * 255, 0, 255),
        np.clip(height * 255, 0, 255),
    ], axis=-1).astype(np.uint8)
    p1 = os.path.join(OUT_DIR, "%s_detail.png" % name)
    Image.fromarray(rgba, "RGBA").save(p1)

    # ── 法线 ──
    du = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * 0.5
    dv = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * 0.5
    nx, ny = -du * NORMAL_STRENGTH, dv * NORMAL_STRENGTH
    nz = np.ones_like(nx)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    nrm = np.stack([
        np.clip((nx / ln * 0.5 + 0.5) * 255, 0, 255),
        np.clip((ny / ln * 0.5 + 0.5) * 255, 0, 255),
        np.clip((nz / ln * 0.5 + 0.5) * 255, 0, 255),
    ], axis=-1).astype(np.uint8)
    p2 = os.path.join(OUT_DIR, "%s_detail_n.png" % name)
    Image.fromarray(nrm, "RGB").save(p2)

    print("  板面均值=%.3f 粗糙=%.3f 磨损=%.3f 槽占比=%.1f%%"
          % (panel.mean(), rough.mean(), wear.mean(), seam_core.mean() * 100))
    print("  写出 %s / %s" % (os.path.basename(p1), os.path.basename(p2)))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print("装甲纹理 %dx%d  (%.0f px/m)" % (SIZE, SIZE, PX_PER_M))
    make("mech")


if __name__ == "__main__":
    main()
