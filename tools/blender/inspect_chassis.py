"""
机体多视角检查
================================================
把同一台机体从 6 个角度各渲染一张，用来找"从某个角度才看得见"的缺陷：
穿模、缝隙、翘边、断开的部件。

单看一张 3/4 视角很容易漏掉问题 —— 之前脚掉到地上、护膝翘边，
都是换了角度才暴露的。

用法:
    blender --background --python inspect_chassis.py -- --chassis medium
"""

import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import bpy          # noqa: E402
import robotlib as R   # noqa: E402
import build_chassis as BC   # noqa: E402

# (名字, 方位角°, 仰角°, 距离倍数)
VIEWS = [
    ("front", 0, 6, 1.00),
    ("side", 90, 4, 1.00),
    ("back", 180, 6, 1.00),
    ("q34", 38, 14, 1.00),
    ("low", 25, -14, 1.05),     # 仰视：看腿内侧、裙甲下沿
    ("top", 30, 52, 1.15),      # 俯视：看肩甲、头顶
]


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    variant = "medium"
    out_dir = "./out"
    i = 0
    while i < len(argv):
        if argv[i] == "--chassis" and i + 1 < len(argv):
            variant = argv[i + 1]; i += 2
        elif argv[i] == "--out" and i + 1 < len(argv):
            out_dir = argv[i + 1]; i += 2
        else:
            i += 1
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    P = BC.variant_params(variant)

    for name, az, el, dist_k in VIEWS:
        R.new_scene()
        pal = R.Palette(P["accent"], P["glow"], P["code"])
        A = BC.build(P, pal)
        objs = A.all
        # 合并成一个网格，避免每件单独渲染时 z-fighting
        mn, mx = R.world_bounds(objs)
        height = mx[2] - mn[2]
        R.join_objects(objs, "INSPECT")

        png = os.path.join(out_dir, "inspect_%s_%s.png" % (variant, name))
        # 相机手动定位：从 azimuth/elevation 绕机体中心
        dist = 6.4 * dist_k
        a = math.radians(az)
        e = math.radians(el)
        cx = dist * math.cos(e) * math.sin(a)
        cy = -dist * math.cos(e) * math.cos(a)
        cz = height * 0.48 + dist * math.sin(e)

        # lens 45 / 距离 6.4 → 可见高度约 2.9m，正好框住 2.7m 的机体
        # （之前 lens 70 只看到 1.2m，整个下半身都在画面外）
        R.setup_render(png, (0, 0, height * 0.48), distance=dist,
                       res=760, lens=45, flat=False)
        cam = bpy.context.scene.camera
        if cam:
            cam.location = (cx, cy, cz)
            # 让它重新对准目标
            bpy.context.view_layer.update()
        R.render_to(png)
        print("  [ok] %s" % os.path.basename(png))


if __name__ == "__main__":
    main()
