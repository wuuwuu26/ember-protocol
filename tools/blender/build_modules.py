"""
余火协议 · 模块库构建
================================================
生成可换装模块。每个模块都带统一的标准挂载接口，
视觉上就能读出"这东西是可互换的"。

用法:
    blender --background --python build_modules.py -- --out ../../assets/out
    blender --background --python build_modules.py -- --sheet-only   # 只出目录图

分类（共 22 个）:
    头部 3 · 核心 3 · 武器臂 5 · 推进器 4 · 背包 4 · 辅助 3
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
# 标准挂载接口 —— 所有模块共用
# ═══════════════════════════════════════════════════════════

def mount(pal, z=0.0, radius=0.085, height=0.055, bolts=6, prefix="mount"):
    """标准接口：法兰盘 + 定位环 + 螺栓阵列。
    这是模块系统的视觉锚点 —— 玩家看到它就明白"能拆下来换"。"""
    out = []
    out.append(R.cyl("%s_plate" % prefix, radius, height, (0, 0, z + height * 0.5),
                     mat=pal.steel_light, verts=20, bev=0.004))
    out.append(R.cyl("%s_ring" % prefix, radius * 0.66, height * 1.5,
                     (0, 0, z + height * 0.75), mat=pal.joint, verts=20, bev=0.003))
    for i in range(bolts):
        a = i * 2.0 * math.pi / bolts
        out.append(R.cyl("%s_bolt_%02d" % (prefix, i + 1), radius * 0.10, height * 0.9,
                         (math.cos(a) * radius * 0.82, math.sin(a) * radius * 0.82,
                          z + height * 0.7),
                         mat=pal.copper, verts=6, bev=0.0015))
    return out


# ═══════════════════════════════════════════════════════════
# 头部
# ═══════════════════════════════════════════════════════════

def head_scout(pal):
    o = mount(pal, prefix="head_mount")
    W, D, H = 0.30, 0.32, 0.26
    z = 0.055
    o.append(R.box("head_shell", (W, D, H), (0, 0, z + H * 0.5), mat=pal.steel, bev=0.012))
    o.append(R.box("head_visor", (W * 0.82, 0.035, H * 0.30),
                   (0, -D * 0.5 - 0.015, z + H * 0.62), mat=pal.visor, bev=0.004))
    o.append(R.box("head_brow", (W * 0.92, 0.05, H * 0.16),
                   (0, -D * 0.5 - 0.03, z + H * 0.88), mat=pal.accent, bev=0.006))
    o.append(R.cyl("head_lens", 0.035, 0.06, (0, -D * 0.5 - 0.02, z + H * 0.30),
                   rot=(math.radians(90), 0, 0), mat=pal.core, verts=16, bev=0.004))
    for s, sx in (("L", -1), ("R", 1)):
        o.append(R.cyl("head_ear_%s" % s, 0.048, 0.045,
                       (sx * W * 0.55, 0, z + H * 0.55),
                       rot=(0, math.radians(90), 0), mat=pal.copper, verts=14, bev=0.004))
    o.append(R.cyl("head_antenna", 0.010, 0.30, (W * 0.30, D * 0.22, z + H + 0.14),
                   mat=pal.joint, verts=8, bev=0.002))
    o.append(R.cyl("head_antenna_tip", 0.017, 0.035, (W * 0.30, D * 0.22, z + H + 0.30),
                   mat=pal.core, verts=10, bev=0.002))
    o += R.greeble("head_gb", (0, 0, z + H * 0.5), (W, D, H), 12, 301,
                   pal.greeble_mats(), faces=('+X', '-X', '+Z'))
    return o


def head_standard(pal):
    o = mount(pal, prefix="head_mount")
    W, D, H = 0.34, 0.36, 0.30
    z = 0.055
    o.append(R.box("head_shell", (W, D, H), (0, 0, z + H * 0.5), mat=pal.steel, bev=0.012))
    o.append(R.box("head_crown", (W * 0.74, D * 0.84, H * 0.22),
                   (0, -0.01, z + H * 1.05), mat=pal.steel_light, bev=0.008))
    o.append(R.box("head_visor", (W * 0.80, 0.04, H * 0.26),
                   (0, -D * 0.5 - 0.018, z + H * 0.60), mat=pal.visor, bev=0.004))
    o.append(R.box("head_brow", (W * 0.94, 0.06, H * 0.18),
                   (0, -D * 0.5 - 0.035, z + H * 0.84), mat=pal.accent, bev=0.006))
    o.extend(R.grille("head_mouth", (W * 0.46, 0.035, H * 0.22),
                      (0, -D * 0.5 - 0.022, z + H * 0.24), slats=4, mat=pal.joint, axis='Z'))
    for s, sx in (("L", -1), ("R", 1)):
        o.append(R.cyl("head_ear_%s" % s, 0.055, 0.05,
                       (sx * W * 0.52, 0, z + H * 0.52),
                       rot=(0, math.radians(90), 0), mat=pal.copper, verts=14, bev=0.004))
        o.append(R.cyl("head_earring_%s" % s, 0.068, 0.02,
                       (sx * W * 0.60, 0, z + H * 0.52),
                       rot=(0, math.radians(90), 0), mat=pal.joint, verts=14, bev=0.002))
    o += R.greeble("head_gb", (0, 0, z + H * 0.5), (W, D, H), 16, 302,
                   pal.greeble_mats(), faces=('+X', '-X', '+Z', '-Y'))
    return o


def head_heavy(pal):
    o = mount(pal, radius=0.095, prefix="head_mount")
    W, D, H = 0.40, 0.42, 0.32
    z = 0.055
    o.append(R.box("head_shell", (W, D, H), (0, 0, z + H * 0.5), mat=pal.steel, bev=0.012))
    # 重装头：两侧加厚装甲
    for s, sx in (("L", -1), ("R", 1)):
        o.append(R.box("head_cheek_%s" % s, (W * 0.20, D * 0.90, H * 0.78),
                       (sx * W * 0.56, 0, z + H * 0.48), mat=pal.accent, bev=0.010))
    o.append(R.box("head_visor_slit", (W * 0.52, 0.035, H * 0.11),
                   (0, -D * 0.5 - 0.016, z + H * 0.62), mat=pal.visor, bev=0.003))
    o.append(R.box("head_brow", (W * 0.98, 0.07, H * 0.24),
                   (0, -D * 0.5 - 0.04, z + H * 0.86), mat=pal.accent, bev=0.008))
    o.extend(R.grille("head_mouth", (W * 0.52, 0.04, H * 0.26),
                      (0, -D * 0.5 - 0.026, z + H * 0.24), slats=5, mat=pal.joint, axis='Z'))
    o.append(R.cyl("head_sensor", 0.042, 0.05, (0, -D * 0.5 - 0.02, z + H * 0.38),
                   rot=(math.radians(90), 0, 0), mat=pal.core, verts=16, bev=0.004))
    o += R.greeble("head_gb", (0, 0, z + H * 0.5), (W, D, H), 22, 303,
                   pal.greeble_mats(), faces=('+X', '-X', '+Z'))
    return o


# ═══════════════════════════════════════════════════════════
# 核心
# ═══════════════════════════════════════════════════════════

def _core_base(pal, R0):
    o = mount(pal, prefix="core_mount")
    o.append(R.cyl("core_housing", R0, 0.10, (0, 0, 0.055 + 0.05),
                   mat=pal.joint, verts=28, bev=0.005))
    return o


def core_standard(pal):
    o = _core_base(pal, 0.115)
    o.append(R.cyl("core_cell", 0.078, 0.11, (0, 0, 0.16), mat=pal.core,
                   verts=24, bev=0.004))
    o.append(R.cyl("core_cage", 0.098, 0.13, (0, 0, 0.16), mat=pal.copper,
                   verts=8, bev=0.003))
    for i in range(6):
        a = i * math.pi / 3.0
        o.append(R.cyl("core_pin_%02d" % (i + 1), 0.011, 0.14,
                       (math.cos(a) * 0.098, math.sin(a) * 0.098, 0.16),
                       mat=pal.steel_light, verts=6, bev=0.002))
    return o


def core_output(pal):
    """高输出核心：更大、更多散热片，暗示高电力上限与高热量。"""
    o = _core_base(pal, 0.135)
    o.append(R.cyl("core_cell", 0.092, 0.15, (0, 0, 0.18), mat=pal.core,
                   verts=24, bev=0.004))
    o.append(R.cyl("core_cage", 0.118, 0.17, (0, 0, 0.18), mat=pal.copper,
                   verts=10, bev=0.003))
    for i in range(8):
        a = i * math.pi / 4.0
        o.append(R.box("core_fin_%02d" % (i + 1), (0.05, 0.014, 0.16),
                       (math.cos(a) * 0.132, math.sin(a) * 0.132, 0.18),
                       rot=(0, 0, a), mat=pal.accent, bev=0.003))
    return o


def core_thermal(pal):
    """高散热核心：矮胖，外圈大散热环。"""
    o = _core_base(pal, 0.145)
    o.append(R.cyl("core_cell", 0.070, 0.12, (0, 0, 0.15), mat=pal.core,
                   verts=24, bev=0.004))
    for i in range(3):
        o.append(R.cyl("core_ring_%d" % (i + 1), 0.115 + i * 0.022, 0.018,
                       (0, 0, 0.115 + i * 0.045), mat=pal.accent, verts=28, bev=0.003))
    for i in range(10):
        a = i * math.pi / 5.0
        o.append(R.box("core_blade_%02d" % (i + 1), (0.055, 0.010, 0.10),
                       (math.cos(a) * 0.155, math.sin(a) * 0.155, 0.15),
                       rot=(0, 0, a), mat=pal.steel_light, bev=0.002))
    return o


# ═══════════════════════════════════════════════════════════
# 武器臂
# ═══════════════════════════════════════════════════════════

def _arm_base(pal, W, D, H):
    """手臂通用骨架：肩接口 + 上臂 + 肘 + 前臂。"""
    o = mount(pal, radius=0.075, prefix="arm_mount")
    z = 0.055
    o.append(R.box("arm_upper", (W, D, H), (0, 0, z + H * 0.5), mat=pal.steel, bev=0.011))
    o.append(R.box("arm_upperband", (W * 1.14, D * 0.92, H * 0.16),
                   (0, 0, z + H * 0.74), mat=pal.accent, bev=0.005))
    elbow_z = z + H + 0.03
    o.append(R.cyl("arm_elbow", W * 0.46, W * 0.92, (0, 0, elbow_z),
                   rot=(0, math.radians(90), 0), mat=pal.joint, verts=16, bev=0.005))
    return o, elbow_z + 0.03


def arm_mining(pal):
    """采矿臂：钻头 + 液压撑杆。"""
    o, z = _arm_base(pal, 0.20, 0.22, 0.34)
    o.append(R.box("arm_fore", (0.18, 0.20, 0.30), (0, 0, z + 0.15),
                   mat=pal.steel, bev=0.011))
    o.extend(R.piston("arm_pist",
                      (0.11, 0.06, z - 0.02), (0.11, 0.06, z + 0.24),
                      0.026, pal.steel_light, pal.copper))
    o.append(R.cone("arm_drill", 0.085, 0.005, 0.30, (0, -0.19, z + 0.16),
                    rot=(math.radians(-90), 0, 0), mat=pal.steel_light, verts=14, bev=0.003))
    o.append(R.cyl("arm_drillbase", 0.098, 0.07, (0, -0.06, z + 0.16),
                   rot=(math.radians(90), 0, 0), mat=pal.accent, verts=18, bev=0.004))
    for i in range(4):
        a = i * math.pi / 2.0
        o.append(R.box("arm_drillfin_%d" % (i + 1), (0.022, 0.14, 0.022),
                       (math.cos(a) * 0.10, -0.14, z + 0.16 + math.sin(a) * 0.10),
                       mat=pal.copper, bev=0.002))
    o += R.greeble("arm_gb", (0, 0, z + 0.15), (0.18, 0.20, 0.30), 10, 311,
                   pal.greeble_mats(), faces=('+X', '-X'))
    return o


def arm_cannon(pal):
    """加农臂：粗炮管 + 制退器 + 弹鼓。"""
    o, z = _arm_base(pal, 0.22, 0.24, 0.34)
    o.append(R.box("arm_fore", (0.20, 0.22, 0.30), (0, 0, z + 0.15),
                   mat=pal.steel, bev=0.011))
    o.append(R.cyl("arm_barrel", 0.062, 0.46, (0, -0.30, z + 0.16),
                   rot=(math.radians(90), 0, 0), mat=pal.steel_light, verts=20, bev=0.005))
    o.append(R.cyl("arm_barrelring", 0.075, 0.05, (0, -0.14, z + 0.16),
                   rot=(math.radians(90), 0, 0), mat=pal.accent, verts=20, bev=0.004))
    for i in range(3):
        o.append(R.cyl("arm_brake_%d" % (i + 1), 0.082, 0.022,
                       (0, -0.44 - i * 0.05, z + 0.16),
                       rot=(math.radians(90), 0, 0), mat=pal.joint, verts=20, bev=0.002))
    o.append(R.cyl("arm_drum", 0.095, 0.10, (0.10, 0.06, z + 0.14),
                   rot=(0, math.radians(90), 0), mat=pal.accent_dark, verts=18, bev=0.005))
    o.extend(R.grille("arm_vent", (0.03, 0.14, 0.16), (-0.10, 0.02, z + 0.16),
                      slats=4, mat=pal.joint, axis='Z'))
    return o


def arm_shield(pal):
    """盾臂：大盾面 + 观察缝。"""
    o, z = _arm_base(pal, 0.18, 0.20, 0.32)
    o.append(R.box("arm_fore", (0.16, 0.18, 0.26), (0, 0, z + 0.13),
                   mat=pal.steel, bev=0.010))
    # 盾面三层
    for i, (sc, off, m) in enumerate(((1.00, 0.00, pal.accent),
                                      (0.82, 0.05, pal.accent_dark),
                                      (0.56, 0.09, pal.steel_light))):
        o.append(R.box("arm_shield_%d" % (i + 1),
                       (0.34 * sc, 0.05, 0.56 * sc),
                       (0, -0.14 - off, z + 0.20), mat=m, bev=0.010))
    o.append(R.box("arm_shield_slit", (0.22, 0.03, 0.045),
                   (0, -0.245, z + 0.36), mat=pal.visor, bev=0.003))
    for i in range(4):
        o.append(R.cyl("arm_shieldbolt_%d" % (i + 1), 0.014, 0.05,
                       (-0.12 + i * 0.08, -0.20, z + 0.02),
                       rot=(math.radians(90), 0, 0), mat=pal.copper, verts=6, bev=0.002))
    return o


def arm_grapple(pal):
    """钩索臂：绞盘 + 发射筒 + 钩爪。"""
    o, z = _arm_base(pal, 0.18, 0.20, 0.32)
    o.append(R.box("arm_fore", (0.16, 0.18, 0.26), (0, 0, z + 0.13),
                   mat=pal.steel, bev=0.010))
    o.append(R.cyl("arm_winch", 0.075, 0.07, (0.09, 0.02, z + 0.12),
                   rot=(0, math.radians(90), 0), mat=pal.accent, verts=18, bev=0.005))
    o.append(R.cyl("arm_launcher", 0.048, 0.26, (0, -0.20, z + 0.14),
                   rot=(math.radians(90), 0, 0), mat=pal.steel_light, verts=16, bev=0.004))
    for i in range(3):
        a = i * 2.0 * math.pi / 3.0
        o.append(R.box("arm_hook_%d" % (i + 1), (0.020, 0.12, 0.020),
                       (math.cos(a) * 0.055, -0.36, z + 0.14 + math.sin(a) * 0.055),
                       rot=(math.radians(-28), 0, a), mat=pal.copper, bev=0.002))
    o += R.greeble("arm_gb", (0, 0, z + 0.13), (0.16, 0.18, 0.26), 8, 312,
                   pal.greeble_mats(), faces=('+X', '-X'))
    return o


def arm_welder(pal):
    """焊枪臂：细长喷枪 + 气瓶 + 线缆。"""
    o, z = _arm_base(pal, 0.17, 0.19, 0.30)
    o.append(R.box("arm_fore", (0.15, 0.17, 0.24), (0, 0, z + 0.12),
                   mat=pal.steel, bev=0.010))
    o.append(R.cyl("arm_torch", 0.026, 0.30, (0, -0.22, z + 0.13),
                   rot=(math.radians(90), 0, 0), mat=pal.copper, verts=12, bev=0.003))
    o.append(R.cyl("arm_torchtip", 0.016, 0.06, (0, -0.39, z + 0.13),
                   rot=(math.radians(90), 0, 0), mat=pal.core, verts=10, bev=0.002))
    for i, sx in enumerate((-1, 1)):
        o.append(R.cyl("arm_tank_%d" % (i + 1), 0.038, 0.20,
                       (sx * 0.075, 0.06, z + 0.12),
                       mat=pal.accent, verts=16, bev=0.004))
    o.append(R.cable("arm_hose",
                     [(0.075, 0.06, z + 0.22), (0.10, -0.02, z + 0.16),
                      (0.02, -0.16, z + 0.13)], 0.012, pal.joint))
    return o


# ═══════════════════════════════════════════════════════════
# 推进器
# ═══════════════════════════════════════════════════════════

def _thruster_base(pal, W, D, H):
    o = mount(pal, radius=0.10, prefix="thr_mount")
    z = 0.055
    o.append(R.box("thr_body", (W, D, H), (0, 0, z + H * 0.5), mat=pal.steel, bev=0.013))
    return o, z


def thruster_standard(pal):
    o, z = _thruster_base(pal, 0.30, 0.36, 0.80)
    H = 0.80
    o.append(R.cyl("thr_knee", 0.115, 0.31, (0, -0.03, z + H * 0.78),
                   rot=(0, math.radians(90), 0), mat=pal.joint, verts=18, bev=0.006))
    for i in range(4):
        o.append(R.box("thr_fin_%d" % (i + 1), (0.33, 0.046, 0.54),
                       (0, 0.18 + 0.015 + i * 0.081, z + H * 0.5),
                       mat=pal.accent, bev=0.004))
    o.extend(R.grille("thr_vent", (0.22, 0.03, 0.30), (0, -0.19, z + H * 0.42),
                      slats=5, mat=pal.joint, axis='Z'))
    o.append(R.box("thr_foot", (0.38, 0.58, 0.20), (0, -0.06, z - 0.06),
                   mat=pal.joint, bev=0.014))
    o.append(R.box("thr_toe", (0.34, 0.15, 0.12), (0, -0.32, z - 0.10),
                   mat=pal.steel_light, bev=0.010))
    o += R.greeble("thr_gb", (0, 0, z + H * 0.5), (0.30, 0.36, H), 14, 321,
                   pal.greeble_mats(), faces=('+X', '-X', '-Y'))
    return o


def thruster_rapid(pal):
    """高速推进器：细长 + 尾部喷口。"""
    o, z = _thruster_base(pal, 0.24, 0.30, 0.78)
    H = 0.78
    o.append(R.cyl("thr_nozzle", 0.095, 0.14, (0, 0.20, z + H * 0.72),
                   rot=(math.radians(90), 0, 0), mat=pal.copper, verts=18, bev=0.005))
    o.append(R.cyl("thr_nozzle_in", 0.070, 0.05, (0, 0.28, z + H * 0.72),
                   rot=(math.radians(90), 0, 0), mat=pal.core, verts=18, bev=0.003))
    o.append(R.cyl("thr_knee", 0.098, 0.25, (0, -0.03, z + H * 0.78),
                   rot=(0, math.radians(90), 0), mat=pal.joint, verts=16, bev=0.005))
    for i in range(3):
        o.append(R.box("thr_fin_%d" % (i + 1), (0.26, 0.036, 0.46),
                       (0, 0.15 + 0.012 + i * 0.062, z + H * 0.42),
                       mat=pal.accent, bev=0.003))
    o.append(R.box("thr_foot", (0.30, 0.52, 0.16), (0, -0.06, z - 0.05),
                   mat=pal.joint, bev=0.012))
    return o


def thruster_quad(pal):
    """重型四足：宽厚 + 双活塞 + 大脚掌。"""
    o, z = _thruster_base(pal, 0.44, 0.50, 0.78)
    H = 0.78
    for sx in (-1, 1):
        o.extend(R.piston("thr_pist_%d" % (sx + 2),
                          (sx * 0.19, -0.20, z + H * 0.30),
                          (sx * 0.19, -0.20, z + H * 0.72),
                          0.030, pal.steel_light, pal.copper))
    o.append(R.cyl("thr_knee", 0.165, 0.44, (0, -0.03, z + H * 0.80),
                   rot=(0, math.radians(90), 0), mat=pal.joint, verts=20, bev=0.007))
    for i in range(2):
        o.append(R.box("thr_fin_%d" % (i + 1), (0.48, 0.060, 0.50),
                       (0, 0.26 + 0.02 + i * 0.105, z + H * 0.46),
                       mat=pal.accent, bev=0.005))
    o.append(R.box("thr_foot", (0.54, 0.78, 0.26), (0, -0.08, z - 0.09),
                   mat=pal.joint, bev=0.016))
    o.append(R.box("thr_toe", (0.48, 0.20, 0.16), (0, -0.44, z - 0.14),
                   mat=pal.steel_light, bev=0.012))
    o += R.greeble("thr_gb", (0, 0, z + H * 0.5), (0.44, 0.50, H), 16, 322,
                   pal.greeble_mats(), faces=('+X', '-X'))
    return o


def thruster_magnetic(pal):
    """磁吸攀爬足：末端电磁盘 + 多关节。"""
    o, z = _thruster_base(pal, 0.28, 0.34, 0.76)
    H = 0.76
    o.append(R.cyl("thr_knee", 0.108, 0.29, (0, -0.03, z + H * 0.76),
                   rot=(0, math.radians(90), 0), mat=pal.joint, verts=18, bev=0.005))
    for i in range(3):
        o.append(R.box("thr_fin_%d" % (i + 1), (0.30, 0.042, 0.50),
                       (0, 0.17 + 0.014 + i * 0.074, z + H * 0.48),
                       mat=pal.accent, bev=0.003))
    # 电磁盘
    o.append(R.cyl("thr_pad", 0.165, 0.045, (0, -0.02, z - 0.03),
                   mat=pal.copper, verts=28, bev=0.005))
    o.append(R.cyl("thr_pad_core", 0.115, 0.030, (0, -0.02, z - 0.055),
                   mat=pal.core, verts=24, bev=0.003))
    for i in range(6):
        a = i * math.pi / 3.0
        o.append(R.box("thr_pad_coil_%d" % (i + 1), (0.070, 0.030, 0.020),
                       (math.cos(a) * 0.125, math.sin(a) * 0.125 - 0.02, z - 0.01),
                       rot=(0, 0, a), mat=pal.joint, bev=0.002))
    return o


# ═══════════════════════════════════════════════════════════
# 背包
# ═══════════════════════════════════════════════════════════

def _pack_base(pal, W, D, H):
    o = mount(pal, radius=0.095, prefix="pack_mount")
    z = 0.055
    o.append(R.box("pack_body", (W, D, H), (0, 0, z + H * 0.5), mat=pal.steel, bev=0.013))
    o.append(R.box("pack_plate", (W * 0.74, 0.05, H * 0.64),
                   (0, D * 0.5 + 0.02, z + H * 0.5), mat=pal.accent, bev=0.008))
    return o, z


def pack_ammo(pal):
    o, z = _pack_base(pal, 0.52, 0.26, 0.46)
    H = 0.46
    for i in range(3):
        o.append(R.box("pack_cell_%d" % (i + 1), (0.14, 0.20, 0.30),
                       (-0.15 + i * 0.15, -0.05, z + H * 0.55),
                       mat=pal.accent_dark, bev=0.008))
        o.append(R.cyl("pack_cellcap_%d" % (i + 1), 0.048, 0.05,
                       (-0.15 + i * 0.15, -0.05, z + H * 0.55 + 0.17),
                       mat=pal.copper, verts=14, bev=0.003))
    o.extend(R.grille("pack_vent", (0.40, 0.03, 0.24), (0, 0.15, z + H * 0.30),
                      slats=4, mat=pal.joint, axis='Z'))
    return o


def pack_thermal(pal):
    """散热背包：大鳍片阵列。"""
    o, z = _pack_base(pal, 0.54, 0.26, 0.48)
    H = 0.48
    for i in range(7):
        o.append(R.box("pack_fin_%d" % (i + 1), (0.46, 0.030, 0.34),
                       (0, -0.10 + i * 0.055, z + H * 0.52),
                       mat=pal.accent, bev=0.003))
    o.append(R.cyl("pack_pump", 0.052, 0.20, (0.20, 0.10, z + H * 0.30),
                   rot=(0, math.radians(90), 0), mat=pal.copper, verts=14, bev=0.004))
    return o


def pack_sensor(pal):
    """传感器背包：雷达盘 + 天线阵列。"""
    o, z = _pack_base(pal, 0.50, 0.24, 0.44)
    H = 0.44
    o.append(R.cyl("pack_dish", 0.17, 0.028, (0, 0.02, z + H + 0.06),
                   mat=pal.steel_light, verts=28, bev=0.004))
    o.append(R.cyl("pack_dishhub", 0.045, 0.06, (0, 0.02, z + H + 0.05),
                   mat=pal.copper, verts=14, bev=0.003))
    for i in range(4):
        a = i * math.pi / 2.0
        o.append(R.cyl("pack_mast_%d" % (i + 1), 0.009, 0.22,
                       (math.cos(a) * 0.16, math.sin(a) * 0.16 + 0.02, z + H + 0.14),
                       mat=pal.joint, verts=6, bev=0.002))
    for i in range(3):
        o.append(R.box("pack_rack_%d" % (i + 1), (0.34, 0.16, 0.05),
                       (0, 0.10, z + 0.10 + i * 0.09), mat=pal.accent_dark, bev=0.004))
    return o


def pack_battery(pal):
    """电池背包：大容量电芯 + 粗电缆。"""
    o, z = _pack_base(pal, 0.50, 0.28, 0.46)
    H = 0.46
    for i, sx in enumerate((-1, 1)):
        o.append(R.cyl("pack_batt_%d" % (i + 1), 0.088, 0.34,
                       (sx * 0.13, -0.03, z + H * 0.52),
                       mat=pal.accent, verts=20, bev=0.006))
        o.append(R.cyl("pack_battcap_%d" % (i + 1), 0.098, 0.04,
                       (sx * 0.13, -0.03, z + H * 0.52 + 0.18),
                       mat=pal.copper, verts=20, bev=0.003))
    for i, sx in enumerate((-1, 1)):
        o.append(R.cable("pack_cable_%d" % (i + 1),
                         [(sx * 0.13, -0.03, z + H * 0.30),
                          (sx * 0.20, -0.14, z + H * 0.12),
                          (sx * 0.14, -0.20, z + 0.02)], 0.018, pal.joint))
    o += R.greeble("pack_gb", (0, 0, z + H * 0.5), (0.50, 0.28, H), 12, 331,
                   pal.greeble_mats(), faces=('+X', '-X', '-Y'))
    return o


# ═══════════════════════════════════════════════════════════
# 辅助
# ═══════════════════════════════════════════════════════════

def aux_radar(pal):
    o = mount(pal, radius=0.07, prefix="aux_mount")
    z = 0.055
    o.append(R.box("aux_body", (0.24, 0.22, 0.20), (0, 0, z + 0.10),
                   mat=pal.steel, bev=0.010))
    o.append(R.cyl("aux_dish", 0.105, 0.022, (0, 0, z + 0.24),
                   rot=(math.radians(-18), 0, 0), mat=pal.steel_light,
                   verts=24, bev=0.004))
    o.append(R.cyl("aux_dishhub", 0.028, 0.05, (0, 0.01, z + 0.23),
                   rot=(math.radians(-18), 0, 0), mat=pal.copper,
                   verts=12, bev=0.003))
    o.append(R.cyl("aux_rod", 0.008, 0.18, (0.09, 0.06, z + 0.24),
                   mat=pal.joint, verts=6, bev=0.002))
    return o


def aux_shield(pal):
    """护盾发生器：环形发射器 + 发光核心。"""
    o = mount(pal, radius=0.07, prefix="aux_mount")
    z = 0.055
    o.append(R.box("aux_body", (0.24, 0.22, 0.18), (0, 0, z + 0.09),
                   mat=pal.steel, bev=0.010))
    for i in range(3):
        o.append(R.cyl("aux_ring_%d" % (i + 1), 0.115 - i * 0.018, 0.016,
                       (0, 0, z + 0.20 + i * 0.032), mat=pal.copper,
                       verts=26, bev=0.003))
    o.append(R.cyl("aux_emit", 0.055, 0.05, (0, 0, z + 0.20),
                   mat=pal.core, verts=20, bev=0.003))
    for i in range(8):
        a = i * math.pi / 4.0
        o.append(R.box("aux_node_%d" % (i + 1), (0.030, 0.016, 0.09),
                       (math.cos(a) * 0.118, math.sin(a) * 0.118, z + 0.22),
                       rot=(0, 0, a), mat=pal.accent, bev=0.002))
    return o


def aux_repair(pal):
    """维修臂：多关节小臂 + 焊头 + 备件架。"""
    o = mount(pal, radius=0.07, prefix="aux_mount")
    z = 0.055
    o.append(R.box("aux_body", (0.22, 0.20, 0.18), (0, 0, z + 0.09),
                   mat=pal.steel, bev=0.010))
    o.append(R.cyl("aux_joint1", 0.045, 0.09, (0, 0, z + 0.21),
                   rot=(0, math.radians(90), 0), mat=pal.joint, verts=14, bev=0.003))
    o.append(R.box("aux_seg1", (0.05, 0.05, 0.22), (0, 0.02, z + 0.30),
                   mat=pal.steel_light, bev=0.006))
    o.append(R.cyl("aux_joint2", 0.032, 0.07, (0, 0.06, z + 0.41),
                   rot=(0, math.radians(90), 0), mat=pal.joint, verts=12, bev=0.003))
    o.append(R.box("aux_seg2", (0.04, 0.04, 0.16), (0, 0.14, z + 0.46),
                   rot=(math.radians(-42), 0, 0), mat=pal.steel_light, bev=0.005))
    o.append(R.cyl("aux_tool", 0.018, 0.07, (0, 0.24, z + 0.52),
                   rot=(math.radians(-42), 0, 0), mat=pal.copper, verts=10, bev=0.002))
    for i in range(3):
        o.append(R.box("aux_tray_%d" % (i + 1), (0.20, 0.06, 0.030),
                       (0, -0.11, z + 0.06 + i * 0.055), mat=pal.accent, bev=0.003))
    return o


# ═══════════════════════════════════════════════════════════
# 目录
# ═══════════════════════════════════════════════════════════

CATALOG = [
    ("head", "head_scout", "侦察头", head_scout),
    ("head", "head_standard", "标准头", head_standard),
    ("head", "head_heavy", "重装头", head_heavy),
    ("core", "core_standard", "标准核心", core_standard),
    ("core", "core_output", "高输出核心", core_output),
    ("core", "core_thermal", "高散热核心", core_thermal),
    ("arm", "arm_mining", "采矿臂", arm_mining),
    ("arm", "arm_cannon", "加农臂", arm_cannon),
    ("arm", "arm_shield", "盾臂", arm_shield),
    ("arm", "arm_grapple", "钩索臂", arm_grapple),
    ("arm", "arm_welder", "焊枪臂", arm_welder),
    ("thruster", "thruster_standard", "标准推进器", thruster_standard),
    ("thruster", "thruster_rapid", "高速推进器", thruster_rapid),
    ("thruster", "thruster_quad", "重型四足", thruster_quad),
    ("thruster", "thruster_magnetic", "磁吸攀爬足", thruster_magnetic),
    ("pack", "pack_ammo", "弹药背包", pack_ammo),
    ("pack", "pack_thermal", "散热背包", pack_thermal),
    ("pack", "pack_sensor", "传感器背包", pack_sensor),
    ("pack", "pack_battery", "电池背包", pack_battery),
    ("aux", "aux_radar", "雷达", aux_radar),
    ("aux", "aux_shield", "护盾发生器", aux_shield),
    ("aux", "aux_repair", "维修臂", aux_repair),
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

    pal = R.Palette((0.26, 0.54, 0.82), (0.52, 0.45, 0.92), "module")

    if not sheet_only:
        print("\n" + "=" * 58)
        print("模块库：逐个生成")
        print("=" * 58)
        for cat, code, label, fn in CATALOG:
            R.new_scene()
            pal = R.Palette((0.26, 0.54, 0.82), (0.52, 0.45, 0.92), "module")
            objs = fn(pal)
            mesh = R.join_objects(objs, "SM_Module_%s" % code.replace("_", " ").title().replace(" ", ""))
            R.smart_uv(mesh)
            lods = R.add_lods(mesh, ((0.50, "_LOD1"), (0.22, "_LOD2")))
            tris = R.tri_count(mesh)
            base = os.path.join(out_dir, "module_%s" % code)
            R.save_blend(base + ".blend")
            try:
                R.export_fbx(base + ".fbx")
            except Exception as e:
                print("    [FAIL] %s: %s" % (code, e))
            print("  %-10s %-14s %5d tris   LOD %s"
                  % (cat, label, tris, "/".join(str(t) for _, t in lods)))

    # 目录图
    print("\n生成模块目录图...")
    R.new_scene()
    pal = R.Palette((0.26, 0.54, 0.82), (0.52, 0.45, 0.92), "module")
    groups = []
    for cat, code, label, fn in CATALOG:
        groups.append(fn(pal))
    cols = 6
    rows, cw, cd = R.layout_grid(groups, cols, gap=0.42)
    span_x, span_z = cols * cw, rows * cd
    png = os.path.join(out_dir, "sheet_modules.png")
    R.setup_render(png, (0, 0, 0), res=1000, wide=True,
                   span=(span_x, span_z), lens=50, flat=True)
    R.render_to(png)
    print("  [ok] sheet_modules.png  (%d 个模块, %d 列 x %d 行)" % (len(groups), cols, rows))
    print("完成。")


if __name__ == "__main__":
    main()
