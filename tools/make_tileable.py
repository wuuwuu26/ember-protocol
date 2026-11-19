"""把 AI 生成的贴图转成**真正可平铺**的纹理。

问题：模型说 "seamless tileable"，但实际上边缘对不上。
材质按世界坐标平铺（一张覆盖几米），接缝在场景里就是一块块矩形色差。

做法（offset + 交叉淡入，经典可平铺算法）：
    1. 把图平移半张（np.roll），此时**原来的边缘跑到了画面中央**；
    2. 用一张中心为 1、边缘为 0 的余弦窗，把原图和平移图按窗混合：
           out = orig * w + shifted * (1 - w)
       边缘处 out ≈ shifted，而 shifted 在边缘是原图的中心区域 —— 连续；
       同时因为 shifted 是环绕平移，out 的左右/上下边界天然相接。
    3. 结果可无缝平铺，代价是中心区域略微柔化（细节层无所谓）。
"""
import os

import numpy as np
from PIL import Image

SRC = r"C:\Users\25227\Documents\robot_game\art_src\textures"
FILES = ["tex_mech_armor", "tex_mech_joint", "tex_mech_copper",
         "tex_env_paint", "tex_env_floor", "tex_env_concrete"]


def make_tileable(src, dst, power=0.75):
    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(np.float32) / 255.0
    h, w, _ = a.shape

    shifted = np.roll(a, (h // 2, w // 2), axis=(0, 1))

    # 归一化坐标 -> 中心为 1、边缘为 0 的窗
    yy = np.linspace(0, 1, h, endpoint=False)[:, None]
    xx = np.linspace(0, 1, w, endpoint=False)[None, :]
    win = (np.sin(np.pi * xx) ** power) * (np.sin(np.pi * yy) ** power)
    win = win[:, :, None]

    out = a * win + shifted * (1.0 - win)
    out = np.clip(out, 0.0, 1.0)
    Image.fromarray((out * 255).round().astype(np.uint8)).save(dst)
    print("[tileable] %s -> %s" % (os.path.basename(src), os.path.basename(dst)))


for name in FILES:
    src = os.path.join(SRC, name + ".png")
    if not os.path.exists(src):
        print("[tileable] missing %s" % src)
        continue
    dst = os.path.join(SRC, name + "_tile.png")
    make_tileable(src, dst)
    os.replace(dst, src)

print("[tileable] done")
