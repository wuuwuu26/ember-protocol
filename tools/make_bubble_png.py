# -*- coding: utf-8 -*-
"""生成真正稀疏的气泡贴图 toxic_bubbles.png（纯标准库，无 PIL 依赖）。

教训：coolant_foam.png 的"刀片"白核是饱和纯白区域，pow/阈值都削不掉，
拿来当气泡会把整池铺满斜向刀片自发光。气泡贴图必须是孤立小圆点。
"""
import math
import random
import struct
import zlib
import os

SIZE = 256
DOTS = 46
random.seed(20261027)

buf = [[0.0] * SIZE for _ in range(SIZE)]

dots = []
for _ in range(DOTS):
    x = random.random() * SIZE
    y = random.random() * SIZE
    r = random.uniform(1.6, 4.2)
    bright = random.uniform(0.55, 1.0)
    dots.append((x, y, r, bright))
    # 环状高光：气泡边缘更亮一点
    dots.append((x, y, r * 0.55, bright * 0.5))

for yy in range(SIZE):
    row = buf[yy]
    for xx in range(SIZE):
        v = 0.0
        for (cx, cy, r, br) in dots:
            dx = xx - cx
            dy = yy - cy
            # 环绕接缝：取最近镜像距离，保证可平铺
            if dx > SIZE / 2:
                dx -= SIZE
            elif dx < -SIZE / 2:
                dx += SIZE
            if dy > SIZE / 2:
                dy -= SIZE
            elif dy < -SIZE / 2:
                dy += SIZE
            d2 = dx * dx + dy * dy
            if d2 < r * r * 4.0:
                d = math.sqrt(d2)
                fall = max(0.0, 1.0 - d / (r * 2.0))
                v = max(v, br * fall * fall)
        row[xx] = v


def chunk(tag, data):
    c = struct.pack(">I", len(data)) + tag + data
    c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return c


raw = b""
for yy in range(SIZE):
    raw += b"\x00"
    for xx in range(SIZE):
        g = int(max(0.0, min(1.0, buf[yy][xx])) * 255)
        raw += bytes((g, g, g))

png = b"\x89PNG\r\n\x1a\n"
# 颜色类型 2 = RGB 真彩（每像素 3 字节）；之前声明灰度却写 3 字节，
# UE 解码报 "bad adaptive filter value"（实测踩坑）。
png += chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0))
png += chunk(b"IDAT", zlib.compress(raw, 9))
png += chunk(b"IEND", b"")

out = os.path.join(os.path.dirname(__file__), "..", "assets", "tex",
                   "toxic_bubbles.png")
out = os.path.normpath(out)
with open(out, "wb") as f:
    f.write(png)
print("BUBBLE_PNG_OK", out, os.path.getsize(out))
