# -*- coding: utf-8 -*-
"""
生成机体/环境的"表面细节"贴图（程序化，严格可平铺）。
================================================================

为什么不用 Smart UV + 普通贴图：
    这批资产是脚本建模 + Smart UV Project 自动展开的，UV 方向随机。
    把一张有明确方向的贴图贴上去，相邻面会各朝各的方向 → 接缝处撕裂。
    UE 侧用 **三平面投影（WorldAlignedTexture）** 采样，完全绕开 UV，
    所以这里的贴图只要求"可平铺"，不要求任何 UV 约定。

产出（两张，都是 RGB 三通道 —— 三平面投影的输出是 float3，A 通道传不过去）：
    mech_detail.png
        R = 面板结构遮罩  1 = 板面（带大尺度明暗），0 = 缝底
        G = 粗糙度        （油污 / 积垢 / 流痕）
        B = 露底金属      （刮痕，绝大部分为 0）
    mech_detail_n.png    由高度场 Sobel 求梯度得到的法线贴图

★ 这一版相比上一版改了什么（都是实测出来的问题）：
  1. 缝宽 9px→14px。原来 1024 贴图铺 62cm，缝只有 1.2mm，
     在 5 米外**完全低于一个像素**，被 mip 平均掉 → 整机看起来一块平板。
     现在缝宽约 2.5cm（配合 UE 侧 TextureSize=240），远看也能读出"分块"。
  2. 磨损通道原来"到处都亮"，导致全机被 WearTint 拉成惨白。
     现在只保留稀疏刮痕，90% 以上像素接近 0。
  3. R 通道不再是一条恒亮的白板，而是叠了**大尺度明暗起伏**，
     这是远看时唯一能读出"表面不干净"的信息。

可平铺的实现要点：所有噪声都由**整数频率的正弦叠加**合成，
周期正好是 1，所以左右/上下边界天然接得上；网格间距也整除贴图尺寸。
"""
import os
import sys

import numpy as np
from PIL import Image

# ── 分辨率 ──
#
# 4K 铺 1.2m（cube_uv 的 size_m），约 3400 px/m —— 近景看板缝和铆钉都不会糊。
# ⚠️ 所有"按像素写"的参数都必须乘 S，否则 4K 下缝宽还是 16px，
#    在 1.2m 上只有 4.7mm，远看直接消失。
SIZE = 4096
S = SIZE / 1024.0          # 像素尺度因子


def px(v):
    """把"1024 基准下的像素值"换算到当前分辨率。"""
    return max(1, int(round(v * S)))
OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else \
    r"C:\Users\25227\Documents\robot_game\assets\tex"
SEED = 20261014


# ─────────────────────────────────────────────
# 基础工具
# ─────────────────────────────────────────────

def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0 if abs(e1 - e0) > 1e-9 else 1e-9), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def fbm(rng, size, base_freq, octaves, gain=0.5):
    """整数频率正弦叠加 → 严格周期 = 1 → 可平铺。"""
    x = np.arange(size, dtype=np.float32) / size
    out = np.zeros((size, size), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        f = base_freq * (2 ** o)
        for _ in range(3):
            fx = int(rng.integers(1, max(f, 2)))
            fy = int(rng.integers(1, max(f, 2)))
            px, py = rng.random() * 2 * np.pi, rng.random() * 2 * np.pi
            out += amp * np.sin(2 * np.pi * fx * x[:, None] + px) \
                * np.sin(2 * np.pi * fy * x[None, :] + py)
        total += amp * 3
        amp *= gain
    out = out / max(total, 1e-6)
    return (out - out.min()) / max(out.max() - out.min(), 1e-6)


def seam_grid(size, cells, width_px, phase=0.0):
    """可平铺网格缝。返回 0..1 遮罩：缝中心 0，板面 1。"""
    coord = (np.arange(size, dtype=np.float32) + 0.5) / size
    step = 1.0 / cells

    def dist_to_line(c):
        d = np.abs(((c + phase) % step) - step * 0.5)
        return step * 0.5 - d          # 0 在网格线上，step/2 在格子中心

    d = np.minimum(dist_to_line(coord)[:, None], dist_to_line(coord)[None, :])
    half = width_px / size * 0.5
    return smoothstep(0.0, half, d), d


def tileable_gradient(size=None):
    """返回一个"环绕梯度"函数：输入高度图 → (du, dv)。

    用 np.roll 做环绕差分，所以贴图边界处的切线也连续 ——
    否则平铺时法线会在接缝处出现一圈亮边。
    """
    def grad(arr):
        du = (np.roll(arr, -1, axis=1) - np.roll(arr, 1, axis=1)) * 0.5
        dv = (np.roll(arr, -1, axis=0) - np.roll(arr, 1, axis=0)) * 0.5
        return du, dv
    return grad


def shift_noise(size, cx, cy, sigma):
    """环绕的高斯斑（用于局部脏污/补丁）。"""
    xs = (np.arange(size) - cx + size * 0.5) % size - size * 0.5
    ys = (np.arange(size) - cy + size * 0.5) % size - size * 0.5
    r2 = xs[None, :] ** 2 + ys[:, None] ** 2
    return np.exp(-r2 / (2.0 * sigma * sigma))


# ─────────────────────────────────────────────
# 各通道
# ─────────────────────────────────────────────

def build_panel_mask(rng):
    """大板 + 中板 + 细刻线 三层缝，再叠大尺度明暗。"""
    m1, d1 = seam_grid(SIZE, 3, px(16))                  # 主板
    m2, _ = seam_grid(SIZE, 6, px(10), phase=0.5 / 6)    # 分板
    m3, _ = seam_grid(SIZE, 12, px(5), phase=0.25 / 12)  # 细刻线

    # 缝深：主板最深（压到 0），中板最浅到 0.25，刻线最浅到 0.55
    mask = np.minimum(m1, 0.25 + 0.75 * m2)
    mask = np.minimum(mask, 0.55 + 0.45 * m3)

    # 缝底不要太干净：加一点噪声
    n = fbm(rng, SIZE, 10, 3)
    mask = mask * (0.90 + 0.10 * n)

    # ── 大尺度明暗：远看唯一能读出的"表面不干净" ──
    # 三个尺度叠：整体污渍 + 中频斑块 + 细颗粒
    big = fbm(rng, SIZE, 2, 4)
    mid = fbm(rng, SIZE, 5, 4)
    fine = fbm(rng, SIZE, 14, 3)
    grime = 0.55 * big + 0.30 * mid + 0.15 * fine
    grime = (grime - grime.min()) / max(grime.max() - grime.min(), 1e-6)
    # 板面明度在 0.62~1.0 之间起伏（不是纯白）
    plate = 0.62 + 0.38 * grime

    out = mask * plate

    # ── 铆钉：沿主板缝等距分布的小圆点，比板面略暗（凹陷感） ──
    rivet = np.zeros((SIZE, SIZE), np.float32)
    step = SIZE // 3
    for gy in range(3):
        for gx in range(3):
            for (ox, oy) in ((0.5, 0.0), (0.0, 0.5), (1.0, 0.5), (0.5, 1.0)):
                cx = ((gx + ox) * step) % SIZE
                cy = ((gy + oy) * step) % SIZE
                rivet = np.maximum(rivet, shift_noise(SIZE, cx, cy, 5.5 * S))
    out = out * (1.0 - 0.45 * rivet)

    return np.clip(out, 0.0, 1.0), mask


def build_roughness(rng, mask):
    """粗糙度：油污斑 + 竖直流痕 + 缝里积垢。"""
    big = fbm(rng, SIZE, 3, 4)
    grain = fbm(rng, SIZE, 20, 3)
    r = 0.30 + 0.42 * big + 0.12 * grain
    # 缝里更粗糙（积垢）
    r = r + (1.0 - mask) * 0.30
    # 竖直流痕
    streak = fbm(rng, SIZE, 3, 2)
    r += 0.14 * smoothstep(0.60, 0.95, streak)
    # 少量"擦得很亮"的斑（维护过的地方）
    polish = fbm(rng, SIZE, 4, 2)
    r -= 0.16 * smoothstep(0.78, 0.96, polish)
    return np.clip(r, 0.0, 1.0)


def build_height(mask, rng):
    """高度：板面高、缝底低，铆钉略凹，叠细微起伏。"""
    n = fbm(rng, SIZE, 8, 4)
    h = mask * 0.88 + 0.12 * n
    return np.clip(h, 0.0, 1.0)


def build_wear(rng, mask):
    """露底金属：**只保留稀疏刮痕**，90% 以上像素为 0。

    上一版这里有一条"缝边磨亮"（mask≈0.55 处 +0.35），而 mask 的过渡带
    占了很大面积 —— 结果整块装甲都被拉到 0.35 的磨损，再经材质里的
    lerp(BaseColor, WearTint, wear*0.45)，全机被染成惨白米色。
    这次把它降到 0.12 并且只贴着缝线极窄的一圈。
    """
    w = np.zeros((SIZE, SIZE), np.float32)
    yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)

    # 稀疏短刮痕（数量少、细、有方向）
    # 数量按面积缩放会到 700+ 条，全图计算太慢；取 2 倍并加长，
    # 视觉上是"少而明显的深刮痕"，比密而浅更好。
    for _ in range(92):
        cx, cy = rng.random() * SIZE, rng.random() * SIZE
        ang = rng.random() * np.pi
        ln = (30 + rng.random() * 200) * S
        thick = (0.5 + rng.random() * 0.9) * S
        dx, dy = np.cos(ang), np.sin(ang)
        px = ((xx - cx + SIZE * 1.5) % SIZE) - SIZE * 0.5
        py = ((yy - cy + SIZE * 1.5) % SIZE) - SIZE * 0.5
        t = np.clip(px * dx + py * dy, -ln * 0.5, ln * 0.5)
        d = np.sqrt((px - t * dx) ** 2 + (py - t * dy) ** 2)
        w = np.maximum(w, smoothstep(thick, 0.0, d) * (0.45 + 0.55 * rng.random()))

    # 缝线极窄一圈的轻微磨亮
    w = np.maximum(w, smoothstep(0.05, 0.0, np.abs(mask - 0.28)) * 0.12)
    return np.clip(w, 0.0, 1.0)


# ─────────────────────────────────────────────

def stats(name, arr):
    a = arr.ravel()
    print("  %-10s min=%.3f 均值=%.3f p50=%.3f p95=%.3f max=%.3f"
          % (name, a.min(), a.mean(), np.percentile(a, 50),
             np.percentile(a, 95), a.max()))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    rng = np.random.default_rng(SEED)

    mask, seam = build_panel_mask(rng)
    rough = build_roughness(rng, seam)
    height = build_height(mask, rng)
    wear = build_wear(rng, mask)

    print("通道统计：")
    stats("R 面板", mask)
    stats("G 粗糙", rough)
    stats("B 磨损", wear)

    rgba = np.stack([
        np.clip(mask * 255, 0, 255),
        np.clip(rough * 255, 0, 255),
        np.clip(wear * 255, 0, 255),
        np.clip(height * 255, 0, 255),
    ], axis=-1).astype(np.uint8)
    p1 = os.path.join(OUT_DIR, "mech_detail.png")
    Image.fromarray(rgba, "RGBA").save(p1)
    print("写出 %s" % p1)

    # ── 法线 ──
    du = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * 0.5
    dv = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * 0.5
    strength = 2.6
    nx, ny = -du * strength, dv * strength
    nz = np.ones_like(nx)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx / ln, ny / ln, nz / ln
    nrm = np.stack([
        np.clip((nx * 0.5 + 0.5) * 255, 0, 255),
        np.clip((ny * 0.5 + 0.5) * 255, 0, 255),
        np.clip((nz * 0.5 + 0.5) * 255, 0, 255),
    ], axis=-1).astype(np.uint8)
    p2 = os.path.join(OUT_DIR, "mech_detail_n.png")
    Image.fromarray(nrm, "RGB").save(p2)
    print("写出 %s" % p2)

    # ── 预览：4x4 平铺，模拟远看效果 ──
    tile = np.tile(rgba, (4, 4, 1))
    tile = tile[::3, ::3]
    Image.fromarray(tile, "RGBA").convert("RGB").save(
        os.path.join(OUT_DIR, "mech_detail_preview.png"))
    print("完成 %dx%d" % (SIZE, SIZE))


if __name__ == "__main__":
    main()
