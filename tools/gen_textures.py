"""生成无缝细节贴图（角色 + 环境），并自动生成法线贴图。

这些都是"细节层"（DetailTex），材质里按世界坐标平铺采样，
所以必须**无缝可平铺**、无方向性、无文字。

引擎用 krea2（不需要文字排版）。
"""
import os
import sys

sys.path.insert(0, r"C:\Users\25227\Documents\robot_game\tools")
import easyai

OUT = r"C:\Users\25227\Documents\robot_game\art_src\textures"
os.makedirs(OUT, exist_ok=True)

JOBS = [
    # ── 角色：机甲装甲 ──
    ("tex_mech_armor", (
        'seamless tileable texture, weathered mech armor plate, dark gunmetal grey, '
        'fine straight panel seams forming rectangles, small rivets along the seams, '
        'scratches and scuffs, chipped paint at the edges, thin oil grime in the grooves, '
        'flat orthographic top-down view, even diffuse lighting, no shadows, no perspective')),
    ("tex_mech_joint", (
        'seamless tileable texture, dark machined metal for robot joints, black oxide finish, '
        'fine concentric machining marks, faint hydraulic oil staining, tiny surface pitting, '
        'flat orthographic top-down view, even diffuse lighting, no shadows, no perspective')),
    ("tex_mech_copper", (
        'seamless tileable texture, weathered copper and brass plate, warm reddish copper tone, '
        'green verdigris spots in the recesses, fine brushed streaks, dark oxidation edges, '
        'flat orthographic top-down view, even diffuse lighting, no shadows, no perspective')),
    # ── 环境 ──
    ("tex_env_paint", (
        'seamless tileable texture, old painted steel wall, deep teal-grey paint flaking off '
        'in patches, rust bleeding from underneath, fine vertical brush marks, '
        'dirt settled in the flake edges, flat orthographic top-down view, '
        'even diffuse lighting, no shadows, no perspective')),
    ("tex_env_floor", (
        'seamless tileable texture, industrial steel floor plate, diamond tread pattern, '
        'worn smooth in the middle of each plate, dirt and oil in the recesses, '
        'slight rust freckles, flat orthographic top-down view, even diffuse lighting, '
        'no shadows, no perspective')),
    ("tex_env_concrete", (
        'seamless tileable texture, cracked industrial concrete panel, poured concrete surface, '
        'fine aggregate grain, dark oil stains, faint formwork board lines, '
        'flat orthographic top-down view, even diffuse lighting, no shadows, no perspective')),
]


def main():
    ok = 0
    for name, prompt in JOBS:
        out = os.path.join(OUT, name + ".png")
        if os.path.exists(out):
            print("[skip] %s" % name)
            ok += 1
            continue
        p = easyai.generate(
            prompt, out, engine="krea2", ratio="1:1",
            resolution="fast_1k",
            negative="text, letters, watermark, logo, blurry, perspective, "
                     "vignette, lighting gradient, shadows")
        if p:
            ok += 1
    print("[textures] %d / %d" % (ok, len(JOBS)))


main()
