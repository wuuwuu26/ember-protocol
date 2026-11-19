# -*- coding: utf-8 -*-
"""生成一张各向同性的水面涟漪法线贴图（纯标准库，无第三方依赖）。

为什么自己生成：手头唯一的法线贴图 T_Coolant_N 是沿对角线排布的条纹，
所有高光被拉成同一方向的平行长条 —— 水面上看起来像"拉丝金属"（r35 实测）。

为什么是 48 个波、频率 4..26：14 个波、频率 2..13 时，最低的几个波在贴图
里形成几个大格子，平铺到水面上就是一层规则的菱形网格（r56/r57 实测，近景
像针织布）。改成数量多、频带高、每个波的坡度贡献接近相等（振幅 ∝ 1/f^0.9）
之后，低频格点消失，剩下的是各向同性的细碎粼光。

频率取整数，保证 512×512 无缝平铺；整体坡度按图像内的最大梯度归一化，
波数变化时不需要重新调增益。
"""
import math
import random
import struct
import zlib

SIZE = 512
OUT = r"C:\Users\25227\Documents\robot_game\assets\tex\water_ripple_n.png"
TARGET_MAX_SLOPE = 1.15

random.seed(20261028)

WAVES = []
for _ in range(48):
    ang = random.uniform(0.0, 2.0 * math.pi)
    f = random.uniform(4.0, 26.0)
    kx = int(round(math.cos(ang) * f))
    ky = int(round(math.sin(ang) * f))
    if kx == 0 and ky == 0:
        kx = 5
    freq = math.hypot(kx, ky)
    # 每个波对坡度的贡献大致相等，避免低频压过高频形成格点
    amp = random.uniform(0.6, 1.0) / (freq ** 0.9)
    ph = random.uniform(0.0, 2.0 * math.pi)
    WAVES.append((kx, ky, amp, ph))


def gradient(x, y):
    u = x / float(SIZE) * 2.0 * math.pi
    v = y / float(SIZE) * 2.0 * math.pi
    gx = 0.0
    gy = 0.0
    for kx, ky, amp, ph in WAVES:
        c = math.cos(kx * u + ky * v + ph) * amp
        gx += c * kx
        gy += c * ky
    return gx, gy


# 第一遍：找最大坡度，做归一化
peak = 1e-6
for y in range(0, SIZE, 4):
    for x in range(0, SIZE, 4):
        gx, gy = gradient(x, y)
        peak = max(peak, math.hypot(gx, gy))
SLOPE = TARGET_MAX_SLOPE / peak

rows = []
for y in range(SIZE):
    row = bytearray([0])  # PNG 过滤器：None
    for x in range(SIZE):
        gx, gy = gradient(x, y)
        nx = -gx * SLOPE
        ny = -gy * SLOPE
        nz = 1.0
        inv = 1.0 / math.sqrt(nx * nx + ny * ny + nz * nz)
        row.append(int(round((nx * inv * 0.5 + 0.5) * 255.0)))
        row.append(int(round((ny * inv * 0.5 + 0.5) * 255.0)))
        row.append(int(round((nz * inv * 0.5 + 0.5) * 255.0)))
    rows.append(bytes(row))

raw = b"".join(rows)


def chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


png = (b"\x89PNG\r\n\x1a\n"
       + chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(raw, 9))
       + chunk(b"IEND", b""))

with open(OUT, "wb") as f:
    f.write(png)

print("water_ripple_n.png %dx%d bytes=%d waves=%d"
      % (SIZE, SIZE, len(png), len(WAVES)))
