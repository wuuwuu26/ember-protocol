"""
高级建模能力验证
================================================
用 loft / lathe / sweep / boolean / subdivide / shell 各做一个件，
渲染成一张对比图 —— 确认这些操作在 Blender 5.2 里真的能跑通、
面法线正确、细分不炸面。

用法:
    blender --background --python test_advanced.py -- --out ../../assets/out
"""

import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import bpy          # noqa: E402
import robotlib as R   # noqa: E402


def demo_loft_torso(pal):
    """放样胸腔：腰方 → 收腰 → 胸外扩 → 肩收口。"""
    ob = R.loft("part_torso", [
        ((0, 0, -0.34), 0.24, 0.19, 5.0, 0),
        ((0, 0, -0.18), 0.21, 0.17, 4.2, 0),   # 收腰
        ((0, 0, -0.02), 0.26, 0.20, 3.2, 0),
        ((0, 0,  0.16), 0.32, 0.23, 2.6, 0),   # 胸外扩
        ((0, 0,  0.30), 0.30, 0.21, 2.2, 0),
        ((0, 0,  0.38), 0.24, 0.17, 2.0, 0),   # 肩收口
    ], seg=40, mat=pal.steel)
    return ob


def demo_loft_leg(pal):
    """放样腿甲：截面中心沿一条弧线走 → 顺着大腿弯曲的护壳。"""
    rings = []
    for i in range(7):
        t = i / 6.0
        z = -0.42 + t * 0.84
        # 中心沿抛物线偏移：上端靠后、中段前凸、下端收回
        y = -0.10 * math.sin(t * math.pi)
        rx = 0.15 + 0.05 * math.sin(t * math.pi)
        ry = 0.11 + 0.04 * math.sin(t * math.pi)
        n = 2.4 + t * 2.0
        rings.append(((0, y, z), rx, ry, n, 0))
    return R.loft("demo_leg", rings, seg=32, mat=pal.steel_light)


def demo_lathe_nozzle(pal):
    """旋转体喷口：外壁扩张 + 喉部收缩 + 内壁回折（一个完整的喇叭）。"""
    prof = [
        (0.00, 0.00),   # 内壁起点（极点）
        (0.055, 0.00),
        (0.062, 0.05),
        (0.078, 0.14),  # 喉部收缩
        (0.105, 0.24),
        (0.135, 0.32),  # 出口外扩
        (0.140, 0.34),
        (0.120, 0.34),  # 翻边
        (0.115, 0.28),
        (0.090, 0.18),  # 外壁回落
        (0.075, 0.06),
        (0.070, 0.00),
        (0.00, 0.00),   # 外壁收口到轴
    ]
    return R.lathe("demo_nozzle", prof, seg=40, mat=pal.copper)


def demo_sweep_trim(pal):
    """扫掠护甲包边：方形截面沿一条弧线走。"""
    path = []
    for i in range(9):
        t = i / 8.0
        a = math.radians(-60 + t * 120)
        path.append((0.42 * math.cos(a), -0.30, 0.42 * math.sin(a) + 0.10))
    prof = [(0.022, 0.014), (-0.022, 0.014), (-0.022, -0.014), (0.022, -0.014)]
    return R.sweep("demo_trim", path, prof, mat=pal.accent)


def demo_boolean_vent(pal):
    """布尔散热窗：在一个放样壳体上真挖三个槽。"""
    body = R.loft("demo_vent_body", [
        ((0, 0, -0.20), 0.26, 0.20, 3.0, 0),
        ((0, 0, 0.00), 0.28, 0.22, 3.0, 0),
        ((0, 0, 0.20), 0.26, 0.20, 3.0, 0),
    ], seg=32, mat=pal.steel)
    cutters = []
    for i in range(3):
        # 切刀必须**穿透**壳壁（厚 0.30 从 y=-0.05 伸到 -0.35），
        # 只切到表面的话近看像"划痕"而不是"开窗"
        c = R.box("cut_%d" % i, (0.30, 0.32, 0.030),
                  (0, -0.06, -0.11 + i * 0.11), mat=None, bev=0)
        cutters.append(c)
    R.boolean_cut(body, cutters)
    return body


def demo_lathe_bolt(pal):
    """旋转体螺栓：六角头 + 圆顶（细分后是完美的半球）。"""
    prof = [
        (0.00, 0.000),
        (0.030, 0.000),
        (0.030, 0.020),
        (0.024, 0.032),
        (0.014, 0.040),
        (0.000, 0.044),
    ]
    return R.lathe("demo_bolt", prof, seg=24, mat=pal.copper)


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    out_dir = "./out"
    i = 0
    while i < len(argv):
        if argv[i] == "--out" and i + 1 < len(argv):
            out_dir = argv[i + 1]; i += 2
        else:
            i += 1
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    R.new_scene()
    pal = R.Palette((0.34, 0.62, 0.86), (0.45, 0.90, 1.00), "demo")

    parts = []
    # 第 1 排：放样（胸腔 / 弯腿甲）
    t = demo_loft_torso(pal)
    t.location = (-0.62, 0, 0.44)
    parts.append(t)

    lg = demo_loft_leg(pal)
    lg.location = (0.50, 0, 0.46)
    parts.append(lg)

    # 第 2 排：旋转体喷口 / 扫掠包边 / 布尔散热窗 / 旋转体螺栓
    nz = demo_lathe_nozzle(pal)
    nz.location = (-0.70, 0, -0.32)
    nz.rotation_euler = (math.radians(90), 0, 0)
    parts.append(nz)

    tr = demo_sweep_trim(pal)
    tr.location = (-0.10, 0.10, -0.38)
    parts.append(tr)

    vt = demo_boolean_vent(pal)
    vt.location = (0.34, 0.0, -0.34)
    parts.append(vt)

    bt = demo_lathe_bolt(pal)
    bt.location = (0.72, -0.12, -0.36)
    bt.rotation_euler = (math.radians(90), 0, 0)
    parts.append(bt)

    # 统计
    total = 0
    for p in parts:
        n = R.tri_count(p)
        total += n
        print("  %-22s %6d tris" % (p.name, n))
    print("  合计 %d tris" % total)

    png = os.path.join(out_dir, "demo_advanced.png")
    R.setup_render(png, (0, 0, 0.02), distance=3.75, res=1200, wide=True,
                   lens=62, flat=False)
    R.render_to(png)
    print("  [ok] demo_advanced.png")


if __name__ == "__main__":
    main()
