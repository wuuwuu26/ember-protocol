# -*- coding: utf-8 -*-
"""给机甲碎骸概念图按浅灰背景抠出 alpha，生成 RGBA（第一百一十九轮）。

texgen 的 delight/recenter 依赖 alpha 判断主体（对照 herta_rgba.png 是
71.7% 透明的 RGBA）。ComfyUI 生成的 gen_*.png 是 RGB 浅灰背景，
没有 alpha 会让 texgen 挂死。

复用 texture_project_auto.py 里的 auto_alpha 规则：
背景 = 亮(>0.72) 且低饱和(max-min<0.06)。
"""
import os
import numpy as np
from PIL import Image

IN = r"C:\AI\Hunyuan3D\input"
NAMES = ["mech_torso_wreck", "severed_mech_arm",
         "mech_head_wreck", "armor_debris"]


def auto_alpha(src):
    arr = np.asarray(src.convert("RGB"), dtype=np.float32) / 255.0
    mx = arr.max(2)
    mn = arr.min(2)
    sat = mx - mn
    is_bg = (mx > 0.72) & (sat < 0.06)
    alpha = np.where(is_bg, 0.0, 1.0)
    # 3x3 均值做边缘抗锯齿
    pad = np.pad(alpha, 1, mode="edge")
    acc = np.zeros_like(alpha)
    for dy in range(3):
        for dx in range(3):
            acc += pad[dy:dy + alpha.shape[0], dx:dx + alpha.shape[1]]
    alpha = (acc / 9.0).clip(0, 1)
    rgba = np.dstack([arr, alpha])
    return Image.fromarray((rgba * 255).astype(np.uint8), "RGBA")


for name in NAMES:
    src = os.path.join(IN, "gen_%s.png" % name)
    dst = os.path.join(IN, "gen_%s_rgba.png" % name)
    if not os.path.exists(src):
        print("缺", src)
        continue
    im = Image.open(src).convert("RGB")
    out = auto_alpha(im)
    out.save(dst)
    a = np.asarray(out.getchannel("A"))
    print("%-20s -> %s  透明占比 %.3f" % (
        name, os.path.basename(dst), float((a < 128).mean())))
print("ALPHA_GEN_DONE")
