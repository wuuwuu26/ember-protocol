"""
余火协议 · 场外远景（背景剪影）
================================================
场地四周被 3.8m 高的围墙挡住，墙外是空的 —— 抬头只能看到一片黑天。
真实场景里，围墙外一定有别的建筑（烟囱、桁架、储罐），
它们在夜景里是**剪影**，不需要细节，但能立刻建立"这是个大工业区"的空间感。

三种资产（原点都在底面中心，方便按地面高度直接摆）:
    SM_BG_Stack    烟囱塔   ~34m
    SM_BG_Gantry   桁架塔   ~26m
    SM_BG_Silo     储罐群   ~18m

用法:
    blender --background --python build_backdrop.py -- --out ../../assets/out
"""

import bpy
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import robotlib as R   # noqa: E402


# ═══════════════════════════════════════════════════════════
# 1. 烟囱塔 —— 远景里最典型的剪影
# ═══════════════════════════════════════════════════════════

def build_stack(pal):
    o = []
    H = 34.0
    # 底座
    o.append(R.cyl("bg_base", 3.2, 2.4, (0, 0, 1.2), mat=pal.steel,
                   verts=20, bev=0.10, segments=2))
    # 塔身：下粗上细（用两段圆柱，不是一根等径管）
    o.append(R.cyl("bg_shaft_lo", 2.30, 14.0, (0, 0, 9.4), mat=pal.steel,
                   verts=24, bev=0.08, segments=2))
    o.append(R.cyl("bg_shaft_hi", 1.70, 12.0, (0, 0, 22.4), mat=pal.steel,
                   verts=24, bev=0.08, segments=2))
    # 收口 + 顶部环
    o.append(R.cyl("bg_throat", 1.30, 5.0, (0, 0, 30.9), mat=pal.steel_light,
                   verts=22, bev=0.06, segments=2))
    for i, (rr, zz) in enumerate(((1.75, 28.4), (1.36, 33.2))):
        o.append(R.torus("bg_band_%d" % (i + 1), rr, 0.12, (0, 0, zz),
                         mat=pal.copper, major_seg=28, minor_seg=8))
    # 检修梯：一圈圈半环（远看就是横向条纹，够了）
    for i in range(9):
        z = 4.0 + i * 3.0
        r = 2.30 - (z - 4.0) * 0.035
        o.append(R.torus("bg_ladder_%d" % (i + 1), r + 0.16, 0.07,
                         (0, 0, z), mat=pal.joint,
                         major_seg=24, minor_seg=6))
    # 航空警示灯（自发光小球，远景里的唯一亮点）
    o.append(R.sphere("bg_beacon", 0.30, (0, 0, 33.7), mat=pal.core,
                      segments=14, rings=10))
    # 侧挂管道
    for s, sx in (("L", -1), ("R", 1)):
        o.append(R.cyl("bg_pipe_%s" % s, 0.22, 26.0,
                       (sx * 2.05, 0, 16.0), mat=pal.steel_light,
                       verts=12, bev=0.02, segments=1))
    return o


# ═══════════════════════════════════════════════════════════
# 2. 桁架塔 —— 细高的骨架感
# ═══════════════════════════════════════════════════════════

def build_gantry(pal):
    o = []
    H = 26.0
    legs = 4.2
    for i in range(4):
        a = math.pi * 0.25 + i * math.pi * 0.5
        x, y = math.cos(a) * legs, math.sin(a) * legs
        o.append(R.cyl("bg_leg_%d" % (i + 1), 0.26, H, (x, y, H * 0.5),
                       mat=pal.steel, verts=12, bev=0.03, segments=1))
        # 斜撑：每 4m 一道，交替方向
        for k in range(6):
            z0 = 2.0 + k * 4.0
            o.append(R.cyl("bg_brace_%d_%d" % (i + 1, k + 1), 0.10, 5.2,
                           (x * 0.82, y * 0.82, z0 + 2.0),
                           rot=(math.radians(18) * (1 if k % 2 else -1),
                                math.radians(18), 0),
                           mat=pal.steel_light, verts=8, bev=0.01,
                           segments=1))
    # 横撑环
    for k in range(5):
        z = 3.0 + k * 5.0
        o.append(R.torus("bg_ring_%d" % (k + 1), legs * 0.98, 0.09, (0, 0, z),
                         mat=pal.joint, major_seg=20, minor_seg=6))
    # 顶部平台 + 塔尖
    o.append(R.cyl("bg_deck", legs * 1.25, 0.35, (0, 0, H), mat=pal.steel,
                   verts=20, bev=0.04, segments=1))
    o.append(R.cyl("bg_mast", 0.14, 6.0, (0, 0, H + 3.0), mat=pal.steel_light,
                   verts=10, bev=0.01, segments=1))
    o.append(R.sphere("bg_beacon", 0.26, (0, 0, H + 6.2), mat=pal.core,
                      segments=12, rings=8))
    # 平台上的设备箱
    o.append(R.box("bg_cabinet", (2.2, 1.6, 1.8), (1.4, 0, H + 1.1),
                   mat=pal.steel_light, bev=0.06, segments=2))
    return o


# ═══════════════════════════════════════════════════════════
# 3. 储罐群 —— 大圆球 + 管道
# ═══════════════════════════════════════════════════════════

def build_silo(pal):
    o = []
    # 主球罐
    R0 = 6.4
    cz = 9.6
    o.append(R.sphere("bg_tank", R0, (0, 0, cz), mat=pal.steel,
                      segments=28, rings=18))
    # 赤道加强带 + 上下极带
    for i, (rr, zz) in enumerate(((R0 * 1.005, cz),
                                  (R0 * 0.86, cz + R0 * 0.50),
                                  (R0 * 0.86, cz - R0 * 0.50))):
        o.append(R.torus("bg_belt_%d" % (i + 1), rr, 0.16, (0, 0, zz),
                         mat=pal.copper, major_seg=32, minor_seg=8))
    # 支腿（六条）
    for i in range(6):
        a = i * math.pi / 3.0
        lx, ly = math.cos(a) * R0 * 0.72, math.sin(a) * R0 * 0.72
        o.append(R.cyl("bg_stand_%d" % (i + 1), 0.30, cz - R0 * 0.55,
                       (lx, ly, (cz - R0 * 0.55) * 0.5), mat=pal.steel,
                       verts=12, bev=0.03, segments=1))
    # 顶部人孔 + 警示灯
    o.append(R.cyl("bg_hatch", 0.9, 1.0, (0, 0, cz + R0 + 0.3),
                   mat=pal.steel_light, verts=16, bev=0.05, segments=2))
    o.append(R.sphere("bg_beacon", 0.24, (0, 0, cz + R0 + 0.95),
                      mat=pal.core, segments=12, rings=8))
    # 侧挂管廊：一根主管 + 两个弯头
    o.append(R.cyl("bg_main_pipe", 0.42, 16.0, (R0 + 2.2, 0, 3.4),
                   rot=(math.radians(90), 0, 0), mat=pal.steel_light,
                   verts=14, bev=0.03, segments=1))
    for i, sy in enumerate((-7.4, 7.4)):
        o.append(R.torus("bg_elbow_%d" % (i + 1), 0.62, 0.12,
                         (R0 + 2.2, sy, 3.9), rot=(0, math.radians(90), 0),
                         mat=pal.copper, major_seg=18, minor_seg=6))
    # 旁边的立式小罐（两个），让轮廓不单调
    for i, (sx, sy, rr, hh) in enumerate(((-R0 - 3.4, -3.0, 1.9, 8.0),
                                          (-R0 - 3.0, 3.6, 1.5, 6.4))):
        o.append(R.cyl("bg_vessel_%d" % (i + 1), rr, hh, (sx, sy, hh * 0.5),
                       mat=pal.steel, verts=18, bev=0.06, segments=2))
        o.append(R.ellipsoid("bg_vesselcap_%d" % (i + 1), (rr, rr, rr * 0.5),
                             (sx, sy, hh), mat=pal.steel_light,
                             segments=20, rings=12, cut_below=0.0))
    return o


CATALOG = [
    ("SM_BG_Stack", build_stack),
    ("SM_BG_Gantry", build_gantry),
    ("SM_BG_Silo", build_silo),
]


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

    print("\n" + "=" * 58)
    print("场外远景：逐个生成")
    print("=" * 58)
    for name, fn in CATALOG:
        R.new_scene()
        # 远景只用中性灰钢，不需要识别色
        pal = R.Palette((0.10, 0.11, 0.13), (1.0, 0.35, 0.18), "bg")
        objs = fn(pal)
        mesh = R.join_objects(objs, name)
        R.cube_uv(mesh, size_m=4.0)      # 远景尺度大，UV 密度相应放大
        tris = R.tri_count(mesh)
        mn, mx = R.world_bounds([mesh])
        base = os.path.join(out_dir, name)
        R.save_blend(base + ".blend")
        R.export_fbx(base + ".fbx")
        print("  %-16s %6d tris  高 %.1f m" % (name, tris, mx[2] - mn[2]))
    print("完成。")


if __name__ == "__main__":
    main()
