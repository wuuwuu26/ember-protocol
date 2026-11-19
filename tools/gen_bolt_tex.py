# -*- coding: utf-8 -*-
"""
弹丸贴图 —— 调用本地 Krea 2 Turbo 生成，然后做游戏用的后处理。

两张图：
    1. T_BoltMetal   深色拉丝钛合金（弹壳 BaseColor）
    2. T_BoltPlasma  白热等离子丝（曳光带自发光，材质里按阵营染色）

后处理是必须的：生图模型给的是"照片"，带高光、带环境色；
PBR 的 BaseColor 只需要**去光照的固有色**，否则金属会被高光洗成塑料。
"""
import io
import json
import os
import sys
import time
import urllib.request

import numpy as np
from PIL import Image

API = "http://127.0.0.1:7860/api/generate"
OUTPUT_DIR = r"C:\AI\EasyAI\outputs"
TEX = r"C:\Users\25227\Documents\robot_game\assets\tex"
SIZE = 1024


def gen(prompt, name, style="raw", steps=8):
    payload = {
        "mode": "text2image",
        "prompt": prompt,
        "style": style,
        "ratio": "1:1",
        "resolution_mode": "fast_1k",
        "denoise": 0.65,
        "custom_steps": steps,
        "enable_second_pass": False,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API, data=data,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    print("[Krea2] 生成 %s ..." % name)
    with urllib.request.urlopen(req, timeout=600) as resp:
        res = json.loads(resp.read().decode("utf-8"))
    print("[Krea2] 返回 %.1fs: %s" % (time.time() - t0,
                                     {k: res.get(k) for k in
                                      ("success", "image_url", "media_url",
                                       "elapsed", "model_used")}))
    if not res.get("success"):
        raise RuntimeError("生成失败: %s" % res)

    url = res.get("image_url") or res.get("media_url") or ""
    raw = None
    if os.path.isfile(url):
        raw = url
    else:
        cand = os.path.join(OUTPUT_DIR, os.path.basename(url))
        if os.path.isfile(cand):
            raw = cand
        elif url.startswith("http"):
            raw = os.path.join(TEX, "_raw_%s.png" % name)
            urllib.request.urlretrieve(url, raw)
    if not raw:
        raise RuntimeError("找不到生成图: %s" % url)
    print("[Krea2] 原图 %s" % raw)
    return raw


def load_square(path):
    im = Image.open(path).convert("RGB")
    if im.size != (SIZE, SIZE):
        im = im.resize((SIZE, SIZE), Image.LANCZOS)
    return im


def sobel_normal(height, strength=2.0):
    h = height.astype(np.float32)
    dx = np.zeros_like(h)
    dy = np.zeros_like(h)
    dx[:, 1:-1] = (h[:, 2:] - h[:, :-2]) * 0.5
    dy[1:-1, :] = (h[2:, :] - h[:-2, :]) * 0.5
    n = np.dstack((-dx * strength, dy * strength, np.ones_like(h)))
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return np.clip((n * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)


def make_metal(raw):
    im = load_square(raw)
    rgb = np.asarray(im, np.float32) / 255.0
    g = (0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1]
         + 0.0722 * rgb[:, :, 2])

    # 去光照：拉平整体曝光，只保留纹理的相对明暗
    lo, hi = np.percentile(g, 3), np.percentile(g, 97)
    g = np.clip((g - lo) / max(hi - lo, 1e-4), 0, 1)
    g = np.clip((g - 0.5) * 1.22 + 0.5, 0, 1)

    # 叠加车削细纹（沿着弹轴 = 贴图 V = 行方向），3mm 一道
    yy = np.arange(SIZE, dtype=np.float32)[:, None]
    rings = 0.5 + 0.5 * np.sin(yy / SIZE * 2.0 * np.pi * 96.0)
    rings = (rings - 0.5) * 2.0            # -1..1
    g = np.clip(g + rings * 0.035, 0, 1)

    # 冷色钛合金：金属的 BaseColor 就是反射率，别压得太黑
    tint = np.array([0.60, 0.66, 0.74], np.float32)
    base = tint[None, None, :] * (0.12 + 0.86 * (g ** 1.12))[:, :, None]
    base = np.clip(base, 0, 1)
    Image.fromarray((base * 255).astype(np.uint8), "RGB").save(
        os.path.join(TEX, "bolt_metal.png"))

    # 法线：金属细纹 + 车削环
    h = np.clip(g * 0.75 + rings * 0.08, 0, 1)
    nrm = sobel_normal(h, strength=1.9)
    Image.fromarray(nrm, "RGB").save(os.path.join(TEX, "bolt_metal_n.png"))

    print("[tex] bolt_metal.png / bolt_metal_n.png  (mean=%.2f)" % base.mean())


def make_plasma(raw):
    rgb = np.asarray(load_square(raw), np.float32) / 255.0
    g = (0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1]
         + 0.0722 * rgb[:, :, 2])
    lo, hi = np.percentile(g, 8), np.percentile(g, 99.5)
    g = np.clip((g - lo) / max(hi - lo, 1e-4), 0, 1)
    # 拉出丝状高光，暗部压到纯黑（自发光贴图不该有灰底）
    g = np.clip(g ** 0.85, 0, 1)
    g = np.where(g < 0.10, 0.0, g)
    Image.fromarray((g * 255).astype(np.uint8), "L").save(
        os.path.join(TEX, "bolt_plasma.png"))
    print("[tex] bolt_plasma.png  (mean=%.2f)" % g.mean())


if __name__ == "__main__":
    os.makedirs(TEX, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    raw_metal = gen(
        "seamless tileable PBR albedo texture, dark brushed titanium, "
        "fine lathe-turned circumferential machining grooves, subtle micro "
        "scratches, cold steel blue grey military ordnance metal, perfectly "
        "flat even lighting, no shadows, no highlights, no reflections, "
        "orthographic top down macro photograph, extremely fine detail",
        "bolt_metal")
    make_metal(raw_metal)

    raw_plasma = gen(
        "seamless tileable texture, white hot plasma arcs and energy "
        "filaments on pure black background, thin electric tendrils, "
        "ionized gas, high contrast monochrome, scientific macro photograph, "
        "no objects, no text, glowing gas detail",
        "bolt_plasma")
    make_plasma(raw_plasma)
    print("BOLT_TEX_DONE")
