"""
余火协议 · 竞技场围墙
================================================
生成"真实的墙"——不是一块贴了面板的方板，而是有基座、有扶壁、有压顶、
有管线、有警示漆带、有铆钉的工业围墙。

用法:
    blender --background --python build_walls.py -- --out ../../assets/out

产出（原点都在**底面中心**，方便在关卡里直接按地面高度摆放）:
    SM_Wall_Segment   400 x 60 x 380 cm  标准段
    SM_Wall_Corner     90 x 90 x 400 cm  转角柱
    SM_Wall_Gate      600 x 60 x 420 cm  带门洞的段（预留，暂未使用）

设计要点（为什么这样建）:
  1. **三段式剖面**：基座（内收）→ 墙体（垂直）→ 压顶（外挑 + 圆角）。
     一条墙如果从头到脚一个厚度，远看就是一块板；三段式才有"建筑"的重量感。
  2. **扶壁（buttress）**：每 100cm 一道，向外倾斜 4°。这是最便宜也最有效的
     "这堵墙很厚"的暗示 —— 也是给玩家看的"不可翻越"信号。
  3. **压顶外挑 6cm + 圆角**：真实围墙一定有压顶，它同时解决了墙顶的硬边
     （低模最刺眼的直线之一）。
  4. **管线 + 支架**：沿墙顶走一根主管，每段两个管卡。工业感来自"有人维护过"。
  5. **警示漆带**：底部 40cm 高的安全色带，和场景里的安全黄统一。
"""
import bpy
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import robotlib as R   # noqa: E402


def build_segment(pal, W=4.0, T=0.42, H=3.8):
    o = []

    # ── 基座：比墙体厚，内收一个台阶 ──
    o.append(R.prism("wall_plinth", (W, T * 1.35, 0.26), (0, 0, 0.13),
                     top=(1.0, 0.94), bottom=(1.0, 1.0),
                     mat=pal.steel, bev=0.02, segments=3))

    # ── 墙体主面 ──
    o.append(R.prism("wall_body", (W * 0.995, T, H - 0.52),
                     (0, 0, 0.26 + (H - 0.52) * 0.5),
                     top=(1.0, 0.98), bottom=(1.0, 1.0),
                     mat=pal.steel, bev=0.018, segments=3))

    # ── 正面凹板（两块，中间留竖缝）──
    for i, sx in enumerate((-1.0, 1.0)):
        o.append(R.prism("wall_panel_%d" % (i + 1),
                         (W * 0.44, 0.06, H - 1.15),
                         (sx * W * 0.235, -T * 0.5 - 0.005, 1.72),
                         mat=pal.steel_light, bev=0.02, segments=3))
        # 凹板上的横向压条
        for k in range(3):
            o.append(R.box("wall_panelbar_%d_%d" % (i + 1, k + 1),
                           (W * 0.42, 0.03, 0.045),
                           (sx * W * 0.235, -T * 0.5 - 0.035,
                            1.05 + k * 0.62),
                           mat=pal.joint, bev=0.008))

    # ── 扶壁：每 100cm 一道，外倾 4°（"翻不过去"的视觉暗示）──
    for i, bx in enumerate((-1.5, -0.5, 0.5, 1.5)):
        o.append(R.prism("wall_buttress_%d" % (i + 1),
                         (0.26, 0.34, H - 0.30),
                         (bx, -T * 0.5 - 0.10, (H - 0.30) * 0.5 + 0.26),
                         rot=(math.radians(-4.0), 0, 0),
                         top=(0.72, 0.62), bottom=(1.0, 1.0),
                         mat=pal.steel_light, bev=0.016, segments=3))
        # 扶壁底脚
        o.append(R.prism("wall_buttfoot_%d" % (i + 1),
                         (0.34, 0.46, 0.16),
                         (bx, -T * 0.5 - 0.14, 0.30),
                         top=(0.9, 0.9), bottom=(1.0, 1.0),
                         mat=pal.joint, bev=0.012))

    # ── 警示漆带（底部 40cm）──
    o.append(R.prism("wall_hazard", (W * 0.997, 0.05, 0.40),
                     (0, -T * 0.5 - 0.012, 0.72),
                     mat=pal.accent, bev=0.008))

    # ── 压顶：外挑 + 圆角 ──
    o.append(R.rounded_box("wall_cap", (W * 1.03, T * 1.30, 0.18),
                           (0, 0, H - 0.09),
                           mat=pal.steel_light, radius=0.045, segments=4))
    o.append(R.rounded_box("wall_cap_lip", (W * 1.02, T * 1.42, 0.06),
                           (0, 0, H - 0.20),
                           mat=pal.joint, radius=0.025, segments=3))

    # ── 墙顶管线：主管 + 两个管卡 ──
    o.append(R.cyl("wall_pipe", 0.065, W * 0.94,
                   (0, T * 0.30, H + 0.10), rot=(0, math.radians(90), 0),
                   mat=pal.copper, verts=18, bev=0.006))
    for i, bx in enumerate((-W * 0.30, W * 0.30)):
        o.append(R.box("wall_pipeclamp_%d" % (i + 1), (0.06, 0.10, 0.16),
                       (bx, T * 0.30, H + 0.02), mat=pal.joint, bev=0.006))
    # 管卡螺栓
    o.extend(R.bolt_ring("wall_pipebolt", (0, T * 0.30, H + 0.02), 0.0, 1,
                         pal.copper, axis='Z', r=0.012, depth=0.02))

    # ── 侧面接缝盖板（相邻两段之间的缝）──
    for i, sx in enumerate((-1.0, 1.0)):
        o.append(R.prism("wall_seam_%d" % (i + 1), (0.10, T * 1.06, H - 0.55),
                         (sx * (W * 0.5 - 0.02), 0, 1.75),
                         mat=pal.joint, bev=0.010))

    # ── 铆钉阵列：面板四角 ──
    for sx in (-1.0, 1.0):
        for sz in (0.0, 1.0):
            o.extend(R.bolt_ring("wall_bolt_%d_%d" % (int(sx), int(sz)),
                                 (sx * W * 0.44, -T * 0.5 - 0.03,
                                  1.05 + sz * 1.55),
                                 0.0, 1, pal.copper, axis='Y',
                                 r=0.016, depth=0.02))

    # ── 墙面小细节：通风格栅 + 检修口 ──
    o.extend(R.grille("wall_vent", (0.7, 0.03, 0.36),
                      (W * 0.28, -T * 0.5 - 0.03, H - 0.75), slats=5,
                      mat=pal.joint, axis='Z'))
    o.append(R.rounded_box("wall_hatch", (0.62, 0.05, 0.80),
                           (-W * 0.28, -T * 0.5 - 0.03, 1.35),
                           mat=pal.steel, radius=0.03, segments=3))
    o.append(R.torus("wall_hatchring", 0.055, 0.014,
                     (-W * 0.28 - 0.24, -T * 0.5 - 0.06, 1.55),
                     rot=(math.radians(90), 0, 0), mat=pal.copper,
                     major_seg=18, minor_seg=6))
    return o


def build_corner(pal, S=0.9, H=4.0):
    o = []
    o.append(R.prism("corner_plinth", (S, S, 0.26), (0, 0, 0.13),
                     top=(1.0, 1.0), bottom=(1.06, 1.06),
                     mat=pal.steel, bev=0.02, segments=3))
    o.append(R.prism("corner_body", (S * 0.86, S * 0.86, H - 0.60),
                     (0, 0, 0.26 + (H - 0.60) * 0.5),
                     top=(0.96, 0.96), bottom=(1.0, 1.0),
                     mat=pal.steel, bev=0.03, segments=4))
    # 转角柱：圆柱包角（把 90° 的硬角变成圆角）
    o.append(R.cyl("corner_column", S * 0.30, H - 0.55,
                   (-S * 0.30, -S * 0.30, 0.26 + (H - 0.55) * 0.5),
                   mat=pal.steel_light, verts=24, bev=0.02, segments=3))
    o.append(R.rounded_box("corner_cap", (S * 1.02, S * 1.02, 0.18),
                           (0, 0, H - 0.09),
                           mat=pal.steel_light, radius=0.05, segments=4))
    # 警示带
    o.append(R.prism("corner_hazard", (S * 0.88, S * 0.88, 0.40),
                     (0, 0, 0.72), mat=pal.accent, bev=0.008))
    # 顶部红色警示灯（自发光件）
    o.append(R.cyl("corner_lampbase", 0.09, 0.06, (0, 0, H + 0.03),
                   mat=pal.joint, verts=16, bev=0.006))
    o.append(R.sphere("corner_lamp", 0.075, (0, 0, H + 0.12),
                      mat=pal.core, segments=18, rings=12))
    return o


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    out_dir = "../../assets/out"
    i = 0
    while i < len(argv):
        if argv[i] == "--out" and i + 1 < len(argv):
            out_dir = argv[i + 1]; i += 2
        else:
            i += 1
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    # 墙面用"冷灰钢"，识别色用安全黄（和场景统一）
    pal = R.Palette((0.52, 0.34, 0.06), (1.0, 0.55, 0.15), "wall")

    jobs = ["SM_Wall_Segment", "SM_Wall_Corner"]

    for name in jobs:
        R.new_scene()
        pal = R.Palette((0.52, 0.34, 0.06), (1.0, 0.55, 0.15), "wall")
        objs = (build_segment(pal) if name.endswith("Segment")
                else build_corner(pal))
        mesh = R.join_objects(objs, name)
        tris = R.tri_count(mesh)
        mn, mx = R.world_bounds([mesh])
        print("%-18s 三角面 %6d  尺寸 %.2f x %.2f x %.2f m"
              % (name, tris, mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2]))
        base = os.path.join(out_dir, name.lower())
        R.save_blend(base + ".blend")
        R.export_fbx(base + ".fbx")
        print("  [ok] %s.fbx" % name.lower())

    print("围墙资产完成")


if __name__ == "__main__":
    main()
