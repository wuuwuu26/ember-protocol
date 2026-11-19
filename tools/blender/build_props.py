"""
余火协议 · 道具与环境套件构建
================================================
生成场景所需的可交互道具、掉落物、以及模块化环境构件。

用法:
    blender --background --python build_props.py -- --out ../../assets/out

分类:
    道具 10 个 · 环境构件 10 个 · 地标 1 个（移动基地「灯塔」外形）
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
# 道具
# ═══════════════════════════════════════════════════════════

def scrap_crate(pal):
    o = []
    W, D, H = 0.70, 0.56, 0.50
    o.append(R.box("crate_body", (W, D, H), (0, 0, H * 0.5), mat=pal.rust, bev=0.014))
    for i in range(3):
        o.append(R.box("crate_band_%d" % (i + 1), (W * 1.03, D * 1.03, 0.045),
                       (0, 0, H * (0.20 + i * 0.30)), mat=pal.steel_light, bev=0.005))
    o.append(R.box("crate_lid", (W * 0.92, D * 0.92, 0.05), (0, 0, H + 0.02),
                   mat=pal.steel, bev=0.006))
    for i, sx in enumerate((-1, 1)):
        o.append(R.box("crate_latch_%d" % (i + 1), (0.07, 0.06, 0.14),
                       (sx * W * 0.30, -D * 0.5 - 0.02, H * 0.86),
                       mat=pal.copper, bev=0.004))
    o += R.greeble("crate_gb", (0, 0, H * 0.5), (W, D, H), 10, 501,
                   pal.greeble_mats(), scale=(0.02, 0.06), depth=(0.006, 0.018),
                   faces=('+X', '-X', '-Y'))
    return o, "废料箱", 0.55


def fuel_barrel(pal):
    o = []
    r, h = 0.26, 0.82
    o.append(R.cyl("barrel_body", r, h, (0, 0, h * 0.5), mat=pal.rust,
                   verts=24, bev=0.010))
    for i in range(3):
        o.append(R.cyl("barrel_ring_%d" % (i + 1), r * 1.06, 0.05,
                       (0, 0, h * (0.22 + i * 0.28)), mat=pal.steel_light,
                       verts=24, bev=0.005))
    o.append(R.cyl("barrel_cap", r * 0.90, 0.05, (0, 0, h + 0.01),
                   mat=pal.steel, verts=24, bev=0.006))
    o.append(R.cyl("barrel_valve", 0.055, 0.10, (r * 0.44, 0, h + 0.06),
                   mat=pal.copper, verts=14, bev=0.004))
    o.append(R.box("barrel_label", (0.20, 0.02, 0.16), (0, -r - 0.005, h * 0.55),
                   mat=pal.accent, bev=0.003))
    return o, "燃料桶", 0.88


def terminal(pal):
    o = []
    o.append(R.box("term_base", (0.50, 0.36, 0.16), (0, 0, 0.08), mat=pal.steel, bev=0.010))
    o.append(R.box("term_body", (0.44, 0.16, 0.60), (0, 0.06, 0.44), mat=pal.steel_light, bev=0.010))
    o.append(R.box("term_screen", (0.36, 0.04, 0.34), (0, -0.03, 0.52),
                   rot=(math.radians(-12), 0, 0), mat=pal.core, bev=0.004))
    o.append(R.box("term_frame", (0.42, 0.05, 0.42), (0, -0.005, 0.52),
                   rot=(math.radians(-12), 0, 0), mat=pal.joint, bev=0.005))
    for i in range(4):
        o.append(R.box("term_key_%d" % (i + 1), (0.30, 0.03, 0.030),
                       (0, -0.12, 0.26 - i * 0.048), mat=pal.joint, bev=0.002))
    o.append(R.cyl("term_antenna", 0.010, 0.24, (0.16, 0.06, 0.82),
                   mat=pal.joint, verts=6, bev=0.002))
    o += R.greeble("term_gb", (0, 0.06, 0.44), (0.44, 0.16, 0.60), 8, 502,
                   pal.greeble_mats(), scale=(0.018, 0.05), depth=(0.005, 0.014),
                   faces=('+X', '-X'))
    return o, "终端", 0.94


def container(pal):
    o = []
    W, D, H = 2.40, 1.00, 1.10
    o.append(R.box("cont_body", (W, D, H), (0, 0, H * 0.5), mat=pal.accent_dark, bev=0.020))
    for i in range(9):
        o.append(R.box("cont_rib_%d" % (i + 1), (0.08, D * 1.02, H * 0.92),
                       (-W * 0.44 + i * W * 0.11, 0, H * 0.5),
                       mat=pal.steel, bev=0.005))
    o.append(R.box("cont_door_l", (W * 0.24, 0.06, H * 0.86), (-W * 0.12, D * 0.5 + 0.03, H * 0.5),
                   mat=pal.steel_light, bev=0.008))
    o.append(R.box("cont_door_r", (W * 0.24, 0.06, H * 0.86), (W * 0.12, D * 0.5 + 0.03, H * 0.5),
                   mat=pal.steel_light, bev=0.008))
    for i in range(4):
        o.append(R.cyl("cont_foot_%d" % (i + 1), 0.09, 0.10,
                       ((-1 + 2 * (i % 2)) * W * 0.42, (-1 + 2 * (i // 2)) * D * 0.34, 0.05),
                       mat=pal.joint, verts=12, bev=0.004))
    return o, "集装箱", 1.10


def pipe_segment(pal):
    o = []
    L = 2.60
    o.append(R.cyl("pipe_main", 0.30, L, (0, 0, 0.32), rot=(0, math.radians(90), 0),
                   mat=pal.steel, verts=24, bev=0.010))
    for i in range(3):
        o.append(R.cyl("pipe_flange_%d" % (i + 1), 0.36, 0.09,
                       (-L * 0.40 + i * L * 0.40, 0, 0.32),
                       rot=(0, math.radians(90), 0), mat=pal.copper, verts=24, bev=0.005))
    for i, sx in enumerate((-1, 1)):
        o.append(R.box("pipe_support_%d" % (i + 1), (0.16, 0.30, 0.34),
                       (sx * L * 0.32, 0, 0.17), mat=pal.joint, bev=0.008))
    o.append(R.cyl("pipe_gauge", 0.085, 0.06, (L * 0.12, 0, 0.63),
                   mat=pal.accent, verts=16, bev=0.004))
    o += R.greeble("pipe_gb", (0, 0, 0.32), (L, 0.60, 0.60), 14, 503,
                   pal.greeble_mats(), scale=(0.03, 0.08), depth=(0.008, 0.02),
                   faces=('+Y', '-Y'))
    return o, "管道段", 0.70


def shelf(pal):
    o = []
    W, D, H = 1.60, 0.60, 2.00
    for i, sx in enumerate((-1, 1)):
        o.append(R.box("shelf_post_%d" % (i + 1), (0.10, 0.10, H),
                       (sx * W * 0.46, 0, H * 0.5), mat=pal.steel, bev=0.006))
    for i in range(4):
        o.append(R.box("shelf_deck_%d" % (i + 1), (W, D, 0.05),
                       (0, 0, 0.30 + i * 0.56), mat=pal.steel_light, bev=0.005))
        for j in range(3):
            o.append(R.box("shelf_brace_%d_%d" % (i + 1, j + 1), (0.05, D * 0.9, 0.14),
                           (-W * 0.30 + j * W * 0.30, 0, 0.20 + i * 0.56),
                           mat=pal.joint, bev=0.004))
    return o, "货架", 2.00


def debris(pal):
    o = []
    rng_boxes = [
        ((0.90, 0.70, 0.30), (0, 0, 0.15), 0.10),
        ((0.55, 0.45, 0.36), (0.45, 0.20, 0.40), -0.28),
        ((0.40, 0.60, 0.22), (-0.42, -0.18, 0.26), 0.44),
        ((0.32, 0.30, 0.30), (0.16, -0.38, 0.52), 0.72),
        ((0.24, 0.50, 0.20), (-0.20, 0.36, 0.62), -0.55),
    ]
    for i, (sz, loc, rot) in enumerate(rng_boxes):
        o.append(R.box("debris_%d" % (i + 1), sz, loc, rot=(0, 0, rot),
                       mat=pal.rust if i % 2 else pal.steel, bev=0.010))
    for i in range(3):
        o.append(R.cyl("debris_pipe_%d" % (i + 1), 0.06, 0.90,
                       (-0.30 + i * 0.30, 0.42, 0.08 + i * 0.10),
                       rot=(math.radians(90), 0, i * 0.5), mat=pal.steel_light,
                       verts=12, bev=0.004))
    o += R.greeble("debris_gb", (0, 0, 0.30), (1.40, 1.20, 0.60), 16, 504,
                   pal.greeble_mats(), scale=(0.03, 0.09), depth=(0.01, 0.03))
    return o, "残骸块", 0.75


def supply_box(pal):
    o = []
    W, D, H = 0.50, 0.40, 0.34
    o.append(R.box("supply_body", (W, D, H), (0, 0, H * 0.5), mat=pal.accent, bev=0.010))
    o.append(R.box("supply_lid", (W * 1.04, D * 1.04, 0.06), (0, 0, H + 0.03),
                   mat=pal.steel_light, bev=0.006))
    o.append(R.box("supply_mark", (0.22, 0.02, 0.10), (0, -D * 0.5 - 0.005, H * 0.5),
                   mat=pal.core, bev=0.003))
    for i, sx in enumerate((-1, 1)):
        o.append(R.box("supply_clip_%d" % (i + 1), (0.06, D * 0.6, 0.10),
                       (sx * W * 0.5, 0, H * 0.6), mat=pal.copper, bev=0.004))
    return o, "补给箱", 0.40


def salvage_pod(pal):
    """回收物容器 —— 敌人部件被拆下后掉落的那个东西。"""
    o = []
    o.append(R.cyl("pod_outer", 0.22, 0.20, (0, 0, 0.10), mat=pal.joint,
                   verts=20, bev=0.008))
    o.append(R.cyl("pod_glow", 0.155, 0.22, (0, 0, 0.11), mat=pal.core,
                   verts=20, bev=0.006))
    for i in range(6):
        a = i * math.pi / 3.0
        o.append(R.box("pod_clamp_%d" % (i + 1), (0.07, 0.03, 0.20),
                       (math.cos(a) * 0.215, math.sin(a) * 0.215, 0.10),
                       rot=(0, 0, a), mat=pal.steel_light, bev=0.004))
    o.append(R.cyl("pod_base", 0.20, 0.04, (0, 0, 0.02), mat=pal.copper,
                   verts=20, bev=0.003))
    return o, "回收容器", 0.24


def beacon(pal):
    o = []
    o.append(R.cyl("beacon_base", 0.28, 0.10, (0, 0, 0.05), mat=pal.steel, verts=20, bev=0.006))
    o.append(R.cyl("beacon_post", 0.075, 1.70, (0, 0, 0.95), mat=pal.steel_light,
                   verts=16, bev=0.005))
    for i in range(3):
        o.append(R.cyl("beacon_ring_%d" % (i + 1), 0.115, 0.05,
                       (0, 0, 0.55 + i * 0.48), mat=pal.accent, verts=18, bev=0.004))
    o.append(R.cyl("beacon_lamp", 0.14, 0.22, (0, 0, 1.88), mat=pal.core,
                   verts=20, bev=0.006))
    o.append(R.cyl("beacon_hood", 0.19, 0.09, (0, 0, 2.02), mat=pal.steel,
                   verts=20, bev=0.005))
    return o, "信标", 2.10


# ═══════════════════════════════════════════════════════════
# 环境构件
# ═══════════════════════════════════════════════════════════

def env_floor(pal):
    o = []
    S = 4.0
    o.append(R.box("floor_slab", (S, S, 0.30), (0, 0, -0.15), mat=pal.steel, bev=0.010))
    o.append(R.box("floor_surface", (S * 0.98, S * 0.98, 0.04), (0, 0, 0.02),
                   mat=pal.steel_light, bev=0.004))
    for i in range(5):
        o.append(R.box("floor_seam_%d" % (i + 1), (S * 0.96, 0.05, 0.025),
                       (0, -S * 0.40 + i * S * 0.20, 0.05), mat=pal.joint, bev=0.002))
    o += R.greeble("floor_gb", (0, 0, 0.05), (S * 0.9, S * 0.9, 0.10), 18, 601,
                   pal.greeble_mats(), scale=(0.05, 0.14), depth=(0.008, 0.022),
                   faces=('+Z',))
    return o, "地板构件", 0.30


def env_wall(pal):
    o = []
    W, H = 4.0, 3.2
    o.append(R.box("wall_body", (W, 0.32, H), (0, 0, H * 0.5), mat=pal.steel, bev=0.014))
    o.append(R.box("wall_panel_a", (W * 0.46, 0.06, H * 0.72),
                   (-W * 0.24, -0.19, H * 0.52), mat=pal.steel_light, bev=0.006))
    o.append(R.box("wall_panel_b", (W * 0.46, 0.06, H * 0.72),
                   (W * 0.24, -0.19, H * 0.52), mat=pal.steel_light, bev=0.006))
    o.extend(R.grille("wall_vent", (W * 0.34, 0.05, H * 0.16),
                      (0, -0.21, H * 0.80), slats=5, mat=pal.joint, axis='Z'))
    for i, sx in enumerate((-1, 1)):
        o.append(R.box("wall_post_%d" % (i + 1), (0.16, 0.44, H),
                       (sx * W * 0.5, 0, H * 0.5), mat=pal.accent, bev=0.010))
    o.append(R.box("wall_rail", (W, 0.40, 0.14), (0, 0, H * 0.30),
                   mat=pal.accent_dark, bev=0.006))
    o += R.greeble("wall_gb", (0, -0.19, H * 0.5), (W * 0.9, 0.06, H * 0.8), 20, 602,
                   pal.greeble_mats(), scale=(0.05, 0.13), depth=(0.008, 0.022),
                   faces=('-Y',))
    return o, "墙体构件", H


def env_pillar(pal):
    o = []
    H = 4.0
    o.append(R.cyl("pillar_core", 0.32, H, (0, 0, H * 0.5), mat=pal.steel,
                   verts=16, bev=0.010))
    for i in range(4):
        o.append(R.box("pillar_fin_%d" % (i + 1), (0.10, 0.34, H * 0.92),
                       (0, 0, H * 0.5), rot=(0, 0, i * math.pi / 4.0),
                       mat=pal.accent, bev=0.006))
    for i in range(3):
        o.append(R.cyl("pillar_ring_%d" % (i + 1), 0.40, 0.10,
                       (0, 0, H * (0.15 + i * 0.35)), mat=pal.copper,
                       verts=20, bev=0.005))
    o.append(R.box("pillar_base", (1.10, 1.10, 0.24), (0, 0, 0.12),
                   mat=pal.joint, bev=0.010))
    o += R.greeble("pillar_gb", (0, 0, H * 0.5), (0.60, 0.60, H * 0.8), 22, 603,
                   pal.greeble_mats(), scale=(0.04, 0.11), depth=(0.008, 0.02),
                   faces=('+X', '-X', '+Y', '-Y'))
    return o, "立柱构件", H


def env_catwalk(pal):
    o = []
    L, W = 4.0, 1.20
    o.append(R.box("walk_deck", (L, W, 0.10), (0, 0, 0), mat=pal.steel_light, bev=0.006))
    for i in range(9):
        o.append(R.box("walk_plank_%d" % (i + 1), (L * 0.98, W * 0.10, 0.03),
                       (0, -W * 0.40 + i * W * 0.10, 0.06), mat=pal.joint, bev=0.002))
    for i, sy in enumerate((-1, 1)):
        o.append(R.box("walk_rail_%d" % (i + 1), (L, 0.06, 0.06),
                       (0, sy * W * 0.5, 1.00), mat=pal.accent, bev=0.004))
        o.append(R.box("walk_rail2_%d" % (i + 1), (L, 0.05, 0.05),
                       (0, sy * W * 0.5, 0.55), mat=pal.accent, bev=0.003))
        for j in range(6):
            o.append(R.box("walk_post_%d_%d" % (i + 1, j + 1), (0.05, 0.05, 1.00),
                           (-L * 0.42 + j * L * 0.17, sy * W * 0.5, 0.50),
                           mat=pal.steel, bev=0.003))
    o.append(R.box("walk_beam", (L, 0.16, 0.22), (0, 0, -0.16), mat=pal.steel, bev=0.006))
    o += R.greeble("walk_gb", (0, 0, -0.16), (L * 0.9, 0.16, 0.22), 14, 604,
                   pal.greeble_mats(), scale=(0.05, 0.12), depth=(0.008, 0.02),
                   faces=('-Z', '+X', '-X'))
    return o, "天桥构件", 1.10


def env_stairs(pal):
    o = []
    n, tw, th, wd = 9, 0.34, 0.24, 1.60
    for i in range(n):
        o.append(R.box("stair_step_%d" % (i + 1), (tw * 1.15, wd, th * 0.42),
                       (-n * tw * 0.5 + i * tw + tw * 0.5, 0,
                        i * th + th * 0.5), mat=pal.steel_light, bev=0.005))
        o.append(R.box("stair_riser_%d" % (i + 1), (tw * 0.30, wd * 0.9, th * 0.62),
                       (-n * tw * 0.5 + i * tw + tw * 0.15, 0,
                        i * th + th * 0.16), mat=pal.joint, bev=0.003))
    for i, sx in enumerate((-1, 1)):
        o.append(R.box("stair_string_%d" % (i + 1), (n * tw, 0.10, 0.30),
                       (0, sx * wd * 0.5, n * th * 0.5), rot=(0, math.radians(-33), 0),
                       mat=pal.accent, bev=0.008))
    return o, "楼梯构件", n * th


def env_doorframe(pal):
    o = []
    W, H = 2.20, 3.00
    o.append(R.box("door_l", (0.26, 0.44, H), (-W * 0.5, 0, H * 0.5), mat=pal.steel, bev=0.010))
    o.append(R.box("door_r", (0.26, 0.44, H), (W * 0.5, 0, H * 0.5), mat=pal.steel, bev=0.010))
    o.append(R.box("door_top", (W + 0.26, 0.44, 0.28), (0, 0, H + 0.14), mat=pal.steel, bev=0.010))
    for i, sx in enumerate((-1, 1)):
        o.append(R.box("door_trim_%d" % (i + 1), (0.10, 0.52, H * 0.92),
                       (sx * (W * 0.5 - 0.13), 0, H * 0.5), mat=pal.accent, bev=0.006))
        o.append(R.cyl("door_light_%d" % (i + 1), 0.05, 0.08,
                       (sx * (W * 0.5 - 0.13), -0.28, H * 0.86),
                       rot=(math.radians(90), 0, 0), mat=pal.core, verts=12, bev=0.003))
    o.extend(R.grille("door_vent", (W * 0.5, 0.05, 0.34), (0, -0.24, H + 0.14),
                      slats=4, mat=pal.joint, axis='Z'))
    return o, "门框构件", H + 0.28


def env_piperun(pal):
    o = []
    L = 4.0
    for i, (r, z, m) in enumerate(((0.20, 0.55, pal.steel),
                                   (0.15, 1.00, pal.steel_light),
                                   (0.13, 1.34, pal.copper))):
        o.append(R.cyl("run_pipe_%d" % (i + 1), r, L, (0, 0, z),
                       rot=(0, math.radians(90), 0), mat=m, verts=18, bev=0.006))
        for j in range(3):
            o.append(R.cyl("run_flange_%d_%d" % (i + 1, j + 1), r * 1.22, 0.07,
                           (-L * 0.33 + j * L * 0.33, 0, z),
                           rot=(0, math.radians(90), 0), mat=pal.joint,
                           verts=18, bev=0.003))
    for i, sx in enumerate((-1, 1)):
        o.append(R.box("run_bracket_%d" % (i + 1), (0.14, 0.24, 1.10),
                       (sx * L * 0.38, 0, 0.60), mat=pal.accent, bev=0.006))
    o.append(R.cyl("run_valve", 0.14, 0.12, (0, -0.10, 0.55),
                   mat=pal.accent_dark, verts=18, bev=0.005))
    return o, "管道组构件", 1.50


def env_platform(pal):
    o = []
    S = 3.2
    o.append(R.box("plat_deck", (S, S, 0.16), (0, 0, 0), mat=pal.steel_light, bev=0.008))
    for i in range(4):
        a = i * math.pi / 2.0
        o.append(R.box("plat_edge_%d" % (i + 1), (S * 0.96, 0.12, 0.22),
                       (math.cos(a) * S * 0.5, math.sin(a) * S * 0.5, -0.04),
                       rot=(0, 0, a), mat=pal.accent, bev=0.005))
    for i, sx in enumerate((-1, 1)):
        for j, sy in enumerate((-1, 1)):
            o.append(R.cyl("plat_leg_%d_%d" % (i + 1, j + 1), 0.13, 2.20,
                           (sx * S * 0.40, sy * S * 0.40, -1.18),
                           mat=pal.steel, verts=16, bev=0.005))
            o.append(R.box("plat_foot_%d_%d" % (i + 1, j + 1), (0.34, 0.34, 0.10),
                           (sx * S * 0.40, sy * S * 0.40, -2.24),
                           mat=pal.joint, bev=0.005))
    o += R.greeble("plat_gb", (0, 0, 0), (S * 0.9, S * 0.9, 0.16), 16, 605,
                   pal.greeble_mats(), scale=(0.05, 0.13), depth=(0.008, 0.02),
                   faces=('+Z',))
    return o, "平台构件", 2.30


def env_gantry(pal):
    o = []
    W, H, D = 4.4, 4.6, 0.30
    for i, sx in enumerate((-1, 1)):
        o.append(R.box("gantry_leg_%d" % (i + 1), (0.28, 0.34, H),
                       (sx * W * 0.46, 0, H * 0.5), mat=pal.steel, bev=0.010))
        o.append(R.box("gantry_foot_%d" % (i + 1), (0.60, 0.70, 0.20),
                       (sx * W * 0.46, 0, 0.10), mat=pal.joint, bev=0.008))
        for j in range(5):
            o.append(R.box("gantry_brace_%d_%d" % (i + 1, j + 1), (0.10, 0.16, 0.90),
                           (sx * (W * 0.46 - 0.30 + j * 0.15), 0, 0.80 + j * 0.90),
                           rot=(0, math.radians(38 * sx), 0), mat=pal.accent, bev=0.005))
    o.append(R.box("gantry_beam", (W * 1.06, D, 0.34), (0, 0, H + 0.17),
                   mat=pal.steel_light, bev=0.010))
    o.append(R.box("gantry_rail", (W, 0.20, 0.14), (0, 0, H - 0.10), mat=pal.copper, bev=0.005))
    for i in range(5):
        o.extend(R.grille("gantry_grille_%d" % (i + 1), (W * 0.14, 0.04, 0.20),
                          (-W * 0.34 + i * W * 0.17, -D * 0.5 - 0.02, H + 0.17),
                          slats=3, mat=pal.joint, axis='Z'))
    return o, "龙门架构件", H + 0.34


# ═══════════════════════════════════════════════════════════
# 地标：移动基地「灯塔」
# ═══════════════════════════════════════════════════════════

def landmark_lighthouse(pal):
    """移动基地外形。六足行走的机械城，是游戏里最大的单体结构。
    这是 blockout 版本 —— 只表达体量与轮廓，细节留给后续迭代。"""
    o = []
    BW, BD, BH = 14.0, 20.0, 9.0
    z = 8.0
    o.append(R.box("base_hull", (BW, BD, BH), (0, 0, z), mat=pal.steel, bev=0.12))
    # 上层建筑
    o.append(R.box("base_upper", (BW * 0.72, BD * 0.62, BH * 0.52),
                   (0, -BD * 0.06, z + BH * 0.5 + BH * 0.26),
                   mat=pal.steel_light, bev=0.08))
    o.append(R.box("base_bridge", (BW * 0.34, BD * 0.20, BH * 0.34),
                   (0, -BD * 0.44, z + BH * 0.5 + BH * 0.52),
                   mat=pal.accent, bev=0.06))
    # 灯塔主塔
    o.append(R.cyl("base_tower", 1.10, 7.0, (0, BD * 0.20, z + BH * 0.5 + 3.5),
                   mat=pal.steel_light, verts=20, bev=0.05))
    o.append(R.cyl("base_tower_lamp", 1.50, 1.10, (0, BD * 0.20, z + BH * 0.5 + 7.4),
                   mat=pal.core, verts=24, bev=0.04))
    o.append(R.cyl("base_tower_hood", 1.85, 0.60, (0, BD * 0.20, z + BH * 0.5 + 8.2),
                   mat=pal.steel, verts=24, bev=0.04))
    # 侧舷
    for i, sx in enumerate((-1, 1)):
        o.append(R.box("base_flank_%d" % (i + 1), (1.20, BD * 0.94, BH * 0.86),
                       (sx * (BW * 0.5 + 0.60), 0, z), mat=pal.accent_dark, bev=0.08))
        for j in range(7):
            o.append(R.box("base_window_%d_%d" % (i + 1, j + 1), (0.10, 1.40, 0.55),
                           (sx * (BW * 0.5 + 1.22), -BD * 0.36 + j * BD * 0.12, z + 1.6),
                           mat=pal.core, bev=0.02))
    # 六足
    for i, sx in enumerate((-1, 1)):
        for j, dy in enumerate((-BD * 0.32, 0.0, BD * 0.32)):
            o.append(R.box("base_leg_%d_%d" % (i + 1, j + 1), (1.60, 1.80, 6.0),
                           (sx * (BW * 0.5 - 1.20), dy, 3.2), mat=pal.steel, bev=0.10))
            o.append(R.cyl("base_knee_%d_%d" % (i + 1, j + 1), 0.90, 1.90,
                           (sx * (BW * 0.5 - 1.20), dy - 0.10, 5.6),
                           rot=(0, math.radians(90), 0), mat=pal.joint,
                           verts=18, bev=0.04))
            o.append(R.box("base_foot_%d_%d" % (i + 1, j + 1), (2.00, 2.80, 0.70),
                           (sx * (BW * 0.5 - 1.20), dy - 0.20, 0.35),
                           mat=pal.joint, bev=0.06))
    o += R.greeble("base_gb", (0, 0, z), (BW, BD, BH), 70, 701,
                   pal.greeble_mats(), scale=(0.30, 0.90), depth=(0.10, 0.28),
                   faces=('+X', '-X', '-Y', '+Z'))
    return o, "移动基地「灯塔」", z + BH * 0.5 + 8.5


# ═══════════════════════════════════════════════════════════
# 目录
# ═══════════════════════════════════════════════════════════

PROPS = [
    ("scrap_crate", scrap_crate), ("fuel_barrel", fuel_barrel),
    ("terminal", terminal), ("container", container),
    ("pipe_segment", pipe_segment), ("shelf", shelf),
    ("debris", debris), ("supply_box", supply_box),
    ("salvage_pod", salvage_pod), ("beacon", beacon),
]

ENV = [
    ("floor", env_floor), ("wall", env_wall), ("pillar", env_pillar),
    ("catwalk", env_catwalk), ("stairs", env_stairs), ("doorframe", env_doorframe),
    ("piperun", env_piperun), ("platform", env_platform), ("gantry", env_gantry),
]


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    out_dir, sheet_only = "./out", False
    i = 0
    while i < len(argv):
        if argv[i] == "--out" and i + 1 < len(argv):
            out_dir = argv[i + 1]; i += 2
        elif argv[i] == "--sheet-only":
            sheet_only = True; i += 1
        else:
            i += 1
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    ACCENT = (0.62, 0.52, 0.34)
    GLOW = (1.00, 0.66, 0.28)

    if not sheet_only:
        print("\n" + "=" * 58)
        print("道具与环境构件：逐个生成")
        print("=" * 58)
        for prefix, items in (("prop", PROPS), ("env", ENV)):
            for code, fn in items:
                R.new_scene()
                pal = R.Palette(ACCENT, GLOW, "prop")
                objs, label, height = fn(pal)
                mesh = R.join_objects(objs, "SM_%s_%s" % (prefix.capitalize(),
                                                          code.replace("_", " ").title().replace(" ", "")))
                R.smart_uv(mesh)
                lods = R.add_lods(mesh, ((0.50, "_LOD1"), (0.22, "_LOD2")))
                tris = R.tri_count(mesh)
                base = os.path.join(out_dir, "%s_%s" % (prefix, code))
                R.save_blend(base + ".blend")
                try:
                    R.export_fbx(base + ".fbx")
                except Exception as e:
                    print("    [FAIL] %s: %s" % (code, e))
                print("  %-8s %-12s %6d tris  高 %.2f m  LOD %s"
                      % (prefix, label, tris, height,
                         "/".join(str(t) for _, t in lods)))

        # 地标单独处理
        print("\n地标...")
        R.new_scene()
        pal = R.Palette(ACCENT, GLOW, "landmark")
        objs, label, height = landmark_lighthouse(pal)
        mesh = R.join_objects(objs, "SM_Landmark_Lighthouse")
        R.smart_uv(mesh)
        # 地标体量最大，LOD 收益最明显
        lods = R.add_lods(mesh, ((0.40, "_LOD1"), (0.15, "_LOD2")))
        base = os.path.join(out_dir, "landmark_lighthouse")
        R.save_blend(base + ".blend")
        try:
            R.export_fbx(base + ".fbx")
        except Exception as e:
            print("    [FAIL] lighthouse: %s" % e)
        print("  landmark %-14s %6d tris  高 %.2f m  LOD %s"
              % (label, R.tri_count(mesh), height,
                 "/".join(str(t) for _, t in lods)))

    # 道具目录图
    print("\n生成道具目录图...")
    R.new_scene()
    pal = R.Palette(ACCENT, GLOW, "prop")
    groups = [fn(pal)[0] for _, fn in PROPS]
    cols = 5
    rows, cw, cd = R.layout_grid(groups, cols, gap=0.55)
    span_x, span_z = cols * cw, rows * cd
    png = os.path.join(out_dir, "sheet_props.png")
    R.setup_render(png, (0, 0, 0), res=1000, wide=True,
                   span=(span_x, span_z), lens=50, flat=True)
    R.render_to(png)
    print("  [ok] sheet_props.png (%d 个道具)" % len(groups))

    # 环境目录图
    print("生成环境目录图...")
    R.new_scene()
    pal = R.Palette(ACCENT, GLOW, "prop")
    groups = [fn(pal)[0] for _, fn in ENV]
    cols = 3
    # 环境构件多为平面（地板、墙、天桥），正面机位下会退化成一条线，
    # 所以这里用 3/4 机位，并且不做等比缩放 —— 保留真实尺寸关系。
    rows, cw, cd = R.layout_grid(groups, cols, gap=1.4, normalize=False)
    span_x, span_z = cols * cw, rows * cd
    png = os.path.join(out_dir, "sheet_env.png")
    R.setup_render(png, (0, 0, 0), res=1000, wide=True,
                   span=(span_x, span_z), lens=50, flat=False)
    R.render_to(png)
    print("  [ok] sheet_env.png (%d 个构件)" % len(groups))

    # 地标
    print("生成地标渲染...")
    R.new_scene()
    pal = R.Palette(ACCENT, GLOW, "landmark")
    objs, label, height = landmark_lighthouse(pal)
    mn, mx = R.world_bounds(objs)
    png = os.path.join(out_dir, "preview_landmark_lighthouse.png")
    R.setup_render(png, (0, 0, (mn[2] + mx[2]) * 0.5), res=1100, wide=True,
                   span=((mx[0] - mn[0]) * 1.05, (mx[2] - mn[2]) * 1.05), lens=50)
    R.render_to(png)
    print("  [ok] preview_landmark_lighthouse.png")
    print("完成。")


if __name__ == "__main__":
    main()
