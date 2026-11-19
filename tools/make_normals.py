"""从细节贴图生成法线贴图（Sobel / 高度斜坡）。

材质里 NormalTex 是可选的细节法线，有不小的观感提升。
用亮度当高度，Sobel 求梯度，转成切线空间法线（OpenGL/UE 约定：G 向上为正）。
"""
import math
import os

from PIL import Image, ImageFilter

SRC = r"C:\Users\25227\Documents\robot_game\art_src\textures"
FILES = ["tex_mech_armor", "tex_mech_joint", "tex_mech_copper",
         "tex_env_paint", "tex_env_floor", "tex_env_concrete"]
STRENGTH = 2.2


def to_normal(src_path, dst_path, strength=STRENGTH):
    im = Image.open(src_path).convert("L")
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    w, h = im.size
    px = im.load()

    out = Image.new("RGB", (w, h))
    op = out.load()
    for y in range(h):
        ym = (y - 1) % h
        yp = (y + 1) % h
        for x in range(w):
            xm = (x - 1) % w
            xp = (x + 1) % w
            dx = (px[xp, y] - px[xm, y]) / 255.0
            dy = (px[x, yp] - px[x, ym]) / 255.0
            nx = -dx * strength
            ny = -dy * strength
            nz = 1.0
            ln = math.sqrt(nx * nx + ny * ny + nz * nz)
            r = int((nx / ln * 0.5 + 0.5) * 255)
            g = int((ny / ln * 0.5 + 0.5) * 255)
            b = int((nz / ln * 0.5 + 0.5) * 255)
            op[x, y] = (max(0, min(255, r)), max(0, min(255, g)),
                        max(0, min(255, b)))
    out.save(dst_path)
    print("[normal] %s -> %s (%dx%d)" % (os.path.basename(src_path),
                                         os.path.basename(dst_path), w, h))


for name in FILES:
    src = os.path.join(SRC, name + ".png")
    if not os.path.exists(src):
        print("[normal] missing %s" % src)
        continue
    dst = os.path.join(SRC, name + "_N.png")
    to_normal(src, dst)

print("[normal] done")
