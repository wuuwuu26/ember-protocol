"""
余火协议 · 机体构建（v4 · 结构重做）
================================================
生成三种玩家机体，带骨架绑定、UV 展开、三级 LOD。

用法:
    blender --background --python build_chassis.py -- --chassis medium --out ../../assets/out
    blender --background --python build_chassis.py -- --chassis all

v4 相对 v3 的改动（为什么重做）
────────────────────────────────────────────────
v3 的问题不是"细节不够多"，而是**结构没有读出来**：
  · 所有主块都是轴对齐的方盒子 → 剪影是一摞纸箱，加再多 greeble 也没用
  · 小腿散热鳍挂在体外 5cm 一排 → 侧面看像一片脱落的梳子
  · 腿长只占身高 38%（人约 50%）→ 站姿又矮又墩
  · 关节只有圆柱，没有"包住关节的护甲"，动起来像积木在转

v4 的做法：
  1. **梯形棱柱（prism）** 代替方盒做主结构：胸腔上宽下窄、大腿上粗下细、
     肩甲外张、小腿前倾 —— 剪影先对，细节才有意义
  2. **骨架 / 装甲两层**：深色内骨架永远比装甲板小一圈，装甲板之间有缝，
     侧面能看见里面的液压杆和线束 —— 这是"机械感"的来源
  3. **散热器收进壳体**：鳍片落在凹陷的框里，不再外挂
  4. **腿加长到身高的 42%**，膝盖抬高，脚拆成跟/掌/趾三段
  5. 关节全部加"护甲罩"（knee cap / ankle guard / elbow cowl），
     转动时不会露出穿帮的接缝

骨骼划分与 v3 完全一致（程序化动画按名字找骨骼），只是关节位置随比例移动。
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
# 机型参数
# ═══════════════════════════════════════════════════════════
#
# 比例原则（改之前先看）：
#   · 腿长（髋→踝）应占身高 40~45%。v3 只有 38%，所以"墩"。
#   · 肩宽（含肩甲）≈ 2.4 × 躯干宽。窄了手臂会埋进躯干，宽了像衣架。
#   · 胸腔高度 ≈ 躯干高 × 0.7，腹部留出 0.3 做"收腰"。
#   · 脚长 ≈ 0.55 × 小腿长 —— 太短会显得站不稳，太长像鸭掌。

def variant_params(v):
    if v == "light":
        return dict(
            name="轻型侦察", code="light",
            accent=(0.16, 0.62, 0.55), glow=(0.30, 0.95, 0.82),
            torso=(0.50, 0.36, 0.48), pelvis=(0.40, 0.32, 0.26),
            head=(0.27, 0.30, 0.26), shoulder=(0.22, 0.30, 0.24),
            upper_arm=(0.15, 0.17, 0.38), forearm=(0.14, 0.16, 0.36),
            thigh=(0.21, 0.26, 0.44), shin=(0.19, 0.24, 0.56),
            foot=(0.26, 0.50, 0.22), backpack=(0.34, 0.20, 0.38),
            z_torso=1.76, z_pelvis=1.44, z_head=2.20, z_shoulder=1.94,
            z_upper=1.78, z_fore=1.36, z_thigh=1.12, z_shin=0.60,
            z_foot=0.13, z_backpack=1.86,
            x_shoulder=0.40, x_arm=0.56, x_leg=0.21,
            fin_count=4, fin_scale=1.0, greeble=90,
            height_note="约 2.55 m",
        )
    if v == "heavy":
        return dict(
            name="重型攻坚", code="heavy",
            accent=(0.80, 0.44, 0.12), glow=(1.0, 0.62, 0.22),
            torso=(0.80, 0.54, 0.58), pelvis=(0.62, 0.46, 0.30),
            head=(0.32, 0.34, 0.26), shoulder=(0.36, 0.44, 0.30),
            upper_arm=(0.26, 0.28, 0.42), forearm=(0.25, 0.27, 0.42),
            thigh=(0.36, 0.40, 0.44), shin=(0.33, 0.36, 0.54),
            foot=(0.42, 0.62, 0.24), backpack=(0.58, 0.28, 0.50),
            z_torso=1.66, z_pelvis=1.34, z_head=2.10, z_shoulder=1.84,
            z_upper=1.68, z_fore=1.26, z_thigh=1.02, z_shin=0.54,
            z_foot=0.13, z_backpack=1.74,
            x_shoulder=0.54, x_arm=0.74, x_leg=0.30,
            fin_count=3, fin_scale=0.8, greeble=120,
            height_note="约 2.45 m",
        )
    return dict(
        name="中型通用", code="medium",
        accent=(0.24, 0.48, 0.78), glow=(0.52, 0.62, 0.95),
        torso=(0.62, 0.44, 0.52), pelvis=(0.46, 0.38, 0.28),
        head=(0.29, 0.32, 0.28), shoulder=(0.28, 0.36, 0.26),
        upper_arm=(0.19, 0.21, 0.40), forearm=(0.18, 0.20, 0.40),
        thigh=(0.27, 0.32, 0.44), shin=(0.24, 0.28, 0.58),
        foot=(0.32, 0.56, 0.24), backpack=(0.44, 0.24, 0.44),
        z_torso=1.78, z_pelvis=1.42, z_head=2.22, z_shoulder=1.96,
        z_upper=1.80, z_fore=1.34, z_thigh=1.12, z_shin=0.60,
        z_foot=0.13, z_backpack=1.88,
        x_shoulder=0.48, x_arm=0.68, x_leg=0.26,
        fin_count=4, fin_scale=1.0, greeble=105,
        height_note="约 2.60 m",
    )


# ═══════════════════════════════════════════════════════════
# 组装器
# ═══════════════════════════════════════════════════════════

class Assembler(object):
    """收集部件并按骨骼归类。部件保持独立，直到最后一步才合并。"""

    def __init__(self, pal, z_range=(0.0, 2.6)):
        self.pal = pal
        self.by_bone = {}      # bone -> [obj]
        self.all = []
        self.z_range = z_range

    def tone_for(self, ob):
        """给部件算一个"表面色阶"，写进顶点色。

        两个来源叠加：
          1. 部件名的哈希 → 相邻装甲板之间有细微明暗差（0.86—1.12）
          2. 世界高度 → 越靠下越暗（积灰 / 油污 / 磨损，最多压到 0.84）
        """
        import zlib
        h = (zlib.crc32(ob.name.encode("utf-8")) & 0xFFFF) / 65535.0
        t = 0.88 + 0.22 * h
        z0, z1 = self.z_range
        z = ob.matrix_world.translation.z
        f = min(max((z - z0) / max(z1 - z0, 0.001), 0.0), 1.0)
        t *= 0.84 + 0.16 * f
        return (t, t, t)

    def add(self, objs, bone):
        if objs is None:
            return []
        if not isinstance(objs, (list, tuple)):
            objs = [objs]
        objs = [o for o in objs if o is not None]
        for ob in objs:
            if hasattr(ob.data, "loops") and len(ob.data.loops) > 0:
                R.assign_vcol(ob, self.tone_for(ob))
        self.by_bone.setdefault(bone, []).extend(objs)
        self.all.extend(objs)
        return objs

    def bone_center(self, bone):
        objs = self.by_bone.get(bone, [])
        if not objs:
            return (0, 0, 0)
        mn, mx = R.world_bounds(objs)
        return ((mn[0] + mx[0]) * 0.5, (mn[1] + mx[1]) * 0.5,
                (mn[2] + mx[2]) * 0.5)

    def bone_size(self, bone):
        objs = self.by_bone.get(bone, [])
        if not objs:
            return (0.1, 0.1, 0.1)
        mn, mx = R.world_bounds(objs)
        return (max(mx[0] - mn[0], 0.05), max(mx[1] - mn[1], 0.05),
                max(mx[2] - mn[2], 0.05))


# ═══════════════════════════════════════════════════════════
# 部件构建
# ═══════════════════════════════════════════════════════════

def build_pelvis(A, P, pal):
    PW, PD, PH = P["pelvis"]
    zP = P["z_pelvis"]
    xL = P["x_leg"]

    # 内骨架（深色，比装甲小一圈）
    A.add(R.prism("pelvis_frame", (PW * 0.74, PD * 0.78, PH * 0.92),
                  (0, 0, zP), top=(1.02, 1.0), bottom=(0.78, 0.86),
                  mat=pal.frame, bev=0.012), "pelvis")
    # 装甲裙（上宽下窄）
    A.add(R.prism("pelvis_armor", (PW, PD, PH * 0.78),
                  (0, 0, zP + PH * 0.06), top=(1.0, 1.0),
                  bottom=(0.74, 0.82), mat=pal.steel, bev=0.016), "pelvis")
    # 腰环
    A.add(R.torus("pelvis_waistring", PW * 0.30, 0.030,
                  (0, 0, zP + PH * 0.52), mat=pal.joint,
                  major_seg=32, minor_seg=10), "pelvis")
    A.add(R.bolt_ring("pelvis_bolts", (0, 0, zP + PH * 0.52), PW * 0.36,
                      8, pal.copper, axis='Z', r=0.016, depth=0.022),
          "pelvis")

    # 前裙甲（两片，中间留缝 —— 装甲分块的关键）
    for side, sx in (("L", -1.0), ("R", 1.0)):
        # 前裙甲：**放样弧面**（上端贴住骨盆、下摆微微外张）
        # 平板裙甲在腰胯这个"双曲面"位置一定会翘边；
        # 放样能让它顺着骨盆的曲率包下来，下摆再张开一点，像真的护裙。
        A.add(R.loft("pelvis_skirt_%s" % side, [
            ((sx * PW * 0.22, -PD * 0.42, zP + PH * 0.20),
             PW * 0.17, PD * 0.09, 3.4, 0),
            ((sx * PW * 0.22, -PD * 0.49, zP - PH * 0.04),
             PW * 0.20, PD * 0.12, 3.0, 0),
            ((sx * PW * 0.22, -PD * 0.47, zP - PH * 0.28),
             PW * 0.18, PD * 0.11, 2.8, 0),
            ((sx * PW * 0.22, -PD * 0.38, zP - PH * 0.44),
             PW * 0.12, PD * 0.09, 2.6, 0),
        ], seg=26, mat=pal.accent), "pelvis")
        A.add(R.box("pelvis_skirtlip_%s" % side,
                    (PW * 0.34, 0.03, 0.035),
                    (sx * PW * 0.22, -PD * 0.52, zP - PH * 0.40),
                    mat=pal.steel_light, bev=0.006), "pelvis")
        # 侧裙甲
        A.add(R.prism("pelvis_side_%s" % side, (0.05, PD * 0.72, PH * 0.66),
                      (sx * PW * 0.52, 0, zP - PH * 0.04),
                      top=(1.0, 1.0), bottom=(1.0, 0.8),
                      mat=pal.steel, bev=0.010), "pelvis")
        # 髋关节（球窝 + 轴）
        A.add(R.sphere("hip_joint_%s" % side, PD * 0.27,
                       (sx * (PW * 0.50 + 0.02), 0, zP - PH * 0.30),
                       mat=pal.joint, segments=20, rings=14), "pelvis")
        A.add(R.torus("hip_ring_%s" % side, PD * 0.27, 0.016,
                      (sx * (PW * 0.50 + PW * 0.09), 0, zP - PH * 0.30),
                      rot=(0, math.radians(90), 0), mat=pal.copper,
                      major_seg=24, minor_seg=8), "pelvis")
    # 后腰动力单元
    A.add(R.box("pelvis_powercell", (PW * 0.46, PD * 0.26, PH * 0.44),
                (0, PD * 0.52, zP + PH * 0.02), mat=pal.frame, bev=0.010),
          "pelvis")
    A.add(R.grille("pelvis_powergrille", (PW * 0.30, 0.03, PH * 0.26),
                   (0, PD * 0.66, zP + PH * 0.04), slats=4, mat=pal.joint,
                   axis='Z'), "pelvis")
    A.add(R.greeble("pelvis_gb", (0, 0, zP), (PW, PD, PH), 12, 101,
                    pal.greeble_mats(), faces=('+X', '-X', '+Y')), "pelvis")


def build_torso(A, P, pal):
    TW, TD, TH = P["torso"]
    zT = P["z_torso"]
    zS = P["z_shoulder"]
    fy = -TD * 0.5

    # ══════════════════════════════════════════════════════════
    # 胸腔：**一条放样曲线**（本轮替换的核心）
    # ══════════════════════════════════════════════════════════
    #
    # 原来是"内骨架 + 腹部 + 胸腔"三块 prism 拼起来 —— 腰、胸、肩之间
    # 是两道硬接缝，侧面看就是三个方盒叠着。
    # 改成放样之后，截面从腰部的圆角方（n=5.5）连续过渡到胸口的椭圆
    # （n=2.8），中间的收腰和外扩都是同一条曲面上的曲率变化，
    # 不存在接缝 —— 这才是工业造型该有的连续性。
    chest = R.loft("torso_chest", [
        ((0, 0, zT - TH * 0.50), TW * 0.335, TD * 0.380, 5.5, 0),   # 腰（近方）
        ((0, 0, zT - TH * 0.36), TW * 0.300, TD * 0.345, 4.6, 0),   # 收腰
        ((0, 0, zT - TH * 0.16), TW * 0.360, TD * 0.385, 3.6, 0),
        ((0, 0, zT + TH * 0.06), TW * 0.455, TD * 0.430, 3.0, 0),
        ((0, 0, zT + TH * 0.26), TW * 0.490, TD * 0.450, 2.7, 0),   # 胸最宽
        ((0, 0, zT + TH * 0.42), TW * 0.450, TD * 0.415, 2.4, 0),
        ((0, 0, zT + TH * 0.53), TW * 0.330, TD * 0.320, 2.2, 0),   # 肩收口
    ], seg=44, mat=pal.steel)

    # 腹部散热窗：**布尔真挖**三个横槽。
    # 原来是在曲面前面贴一排薄片（grille），近看就是贴纸 ——
    # 光打上去没有任何凹凸，阴影是假的。布尔挖出来的槽有真实深度，
    # 槽壁会自己接住高光和阴影。
    cutters = []
    for i in range(3):
        cutters.append(R.box("cut_abd_%d" % (i + 1),
                             (TW * 0.30, TD * 0.55, TH * 0.028),
                             (0, -TD * 0.30, zT - TH * 0.395 + i * TH * 0.052),
                             mat=None, bev=0))
    R.boolean_cut(chest, cutters)
    A.add(chest, "torso")

    # 腰环：收腰处一圈包边（放样件和骨盆之间的过渡）
    A.add(R.torus("torso_waistband", TW * 0.315, 0.026,
                  (0, 0, zT - TH * 0.44), mat=pal.joint,
                  major_seg=40, minor_seg=10), "torso")
    # 领口：一圈环形护甲（曲面，把"方块胸"和"方块头"之间的硬接缝盖住）
    # 领口环：直径必须接近脖子（0.17·TW ≈ 0.11m 半径），
    # 原来给到 0.30·TW（半径 0.19）—— 从侧面看是一圈横在头下方的帽檐。
    A.add(R.torus("torso_collar", TW * 0.17, 0.028,
                  (0, -0.01, zT + TH * 0.50), mat=pal.steel_light,
                  major_seg=30, minor_seg=9), "torso")

    # 左右胸甲：**贴合胸腔曲率的放样壳**（不是平板）
    #
    # 原来是一块 7cm 厚的方板贴在胸口 —— 从侧面看它和胸腔之间是
    # 一条直线接触，正面看是一块平的东西，光打上去只有一种亮度。
    # 改成放样之后，胸甲自己带曲率：中间鼓、上下收，
    # 于是同一块装甲上有连续的明暗渐变，这才像"装在曲面上的板"。
    for side, sx in (("L", -1.0), ("R", 1.0)):
        A.add(R.loft("chest_plate_%s" % side, [
            ((sx * TW * 0.21, -TD * 0.30, zT - TH * 0.10),
             TW * 0.21, TD * 0.20, 3.6, 0),
            ((sx * TW * 0.23, -TD * 0.34, zT + TH * 0.08),
             TW * 0.25, TD * 0.23, 3.1, 0),
            ((sx * TW * 0.23, -TD * 0.32, zT + TH * 0.28),
             TW * 0.24, TD * 0.21, 2.8, 0),
            ((sx * TW * 0.21, -TD * 0.26, zT + TH * 0.42),
             TW * 0.18, TD * 0.16, 2.5, 0),
        ], seg=30, mat=pal.steel_light), "torso")
        # 识别色条：沿胸甲外缘扫掠的扁条（不是贴一块小方片）
        A.add(R.sweep("chest_stripe_%s" % side,
                      [(sx * TW * 0.36, -TD * 0.30, zT - TH * 0.06),
                       (sx * TW * 0.40, -TD * 0.33, zT + TH * 0.12),
                       (sx * TW * 0.39, -TD * 0.31, zT + TH * 0.30),
                       (sx * TW * 0.34, -TD * 0.25, zT + TH * 0.42)],
                      [(0.022, 0.014), (-0.022, 0.014),
                       (-0.022, -0.014), (0.022, -0.014)],
                      mat=pal.accent), "torso")
        # 肩窝（锁骨连接处）：一根从胸口连到肩关节的锁骨杆 + 末端铜环。
        # 旧版是两根悬在 torso 边缘的短杆，和肩球之间有空隙，看起来像浮空的零件。
        TW = P["torso"][0]
        xA = P["x_arm"]
        clav_inner = TW * 0.20
        clav_outer = xA - 0.05
        A.add(R.cyl("clav_mount_%s" % side, 0.070,
                    (clav_outer - clav_inner) + 0.06,
                    (sx * (clav_inner + clav_outer) * 0.5, 0, zS),
                    rot=(0, math.radians(90), 0),
                    mat=pal.joint, verts=16, bev=0.005), "torso")
        A.add(R.cyl("clav_ring_%s" % side, 0.098, 0.05,
                    (sx * clav_outer, 0, zS), rot=(0, math.radians(90), 0),
                    mat=pal.copper, verts=16, bev=0.004), "torso")
        # 侧肋（三片叠甲）
        for i in range(3):
            A.add(R.box("rib_%s_%d" % (side, i + 1),
                        (0.035, TD * (0.62 - i * 0.06), TH * 0.13),
                        (sx * (TW * 0.50 + 0.008),
                         -TD * 0.06 + i * TD * 0.16,
                         zT + TH * 0.10 - i * TH * 0.17),
                        mat=pal.steel_light if i % 2 == 0 else pal.steel,
                        bev=0.008), "torso")

    # 胸口核心：圆窗 + 环 + 螺栓
    core_c = (0, fy - 0.10, zT + TH * 0.10)
    A.add(R.cyl("part_core", TW * 0.105, 0.07, core_c,
                rot=(math.radians(90), 0, 0), mat=pal.core, verts=26,
                bev=0.006), "torso")
    A.add(R.torus("part_corering", TW * 0.140, 0.020,
                  (0, fy - 0.075, core_c[2]), rot=(math.radians(90), 0, 0),
                  mat=pal.joint, major_seg=32, minor_seg=10), "torso")
    A.add(R.bolt_ring("core_bolts", (0, fy - 0.06, core_c[2]),
                      TW * 0.130, 6, pal.copper, axis='Y', r=0.012,
                      depth=0.03), "torso")

    # 颈部基座
    A.add(R.cyl("torso_neckbase", TW * 0.20, 0.07,
                (0, -0.01, zT + TH * 0.52), mat=pal.joint, verts=18,
                bev=0.005), "torso")

    # 侧腰动力管（从胸腔下沿绕到骨盆）
    for side, sx in (("L", -1.0), ("R", 1.0)):
        A.add(R.cable("torso_cable_%s" % side,
                      [(sx * TW * 0.40, fy * 0.55, zT - TH * 0.16),
                       (sx * TW * 0.52, -TD * 0.10, zT - TH * 0.30),
                       (sx * TW * 0.40, PD_OF(P) * 0.2, P["z_pelvis"] + 0.10)],
                      0.020, pal.joint), "torso")

    A.add(R.panel_lines("torso_pl", (0, 0, zT), (TW, TD, TH), 6, 202,
                        pal.joint, thickness=0.008), "torso")
    A.add(R.greeble("torso_gb", (0, 0, zT), (TW, TD, TH), P["greeble"] // 3,
                    203, pal.greeble_mats()), "torso")


def PD_OF(P):
    return P["pelvis"][1]


def build_head(A, P, pal):
    HW, HD, HH = P["head"]
    zH = P["z_head"]
    zT = P["z_torso"]
    TH = P["torso"][2]

    # 颈（两段，带液压）
    A.add(R.cyl("head_neck", HW * 0.34, 0.14, (0, -0.005, zH - HH * 0.62),
                mat=pal.joint, verts=16, bev=0.005), "head")
    for sx in (-1.0, 1.0):
        A.add(R.piston("neck_piston_%s" % ("L" if sx < 0 else "R"),
                       (sx * HW * 0.30, 0.02, zT + TH * 0.50),
                       (sx * HW * 0.30, -0.02, zH - HH * 0.40),
                       0.018, pal.steel_light, pal.copper), "head")

    # ══════════════════════════════════════════════════════════
    # 颅骨：**一条放样曲线**（下颌窄 → 颧骨宽 → 颅顶收）
    # ══════════════════════════════════════════════════════════
    #
    # 原来是"圆角方盒 + 头顶椭球"两件：方盒的顶面是平的，
    # 椭球扣上去之后，侧面能看到一道明显的交界线（像戴了个头盔壳）。
    # 放样是一条从下颌连到颅顶的曲面，没有交界。
    skull = R.loft("head_skull", [
        ((0, 0.000, zH - HH * 0.50), HW * 0.34, HD * 0.34, 3.4, 0),  # 下颌
        ((0, -0.010, zH - HH * 0.34), HW * 0.43, HD * 0.45, 3.1, 0),
        ((0, -0.018, zH - HH * 0.08), HW * 0.50, HD * 0.51, 2.8, 0),  # 颧骨最宽
        ((0, -0.014, zH + HH * 0.18), HW * 0.47, HD * 0.48, 2.5, 0),
        ((0, -0.006, zH + HH * 0.36), HW * 0.37, HD * 0.38, 2.2, 0),
        ((0, 0.000, zH + HH * 0.47), HW * 0.19, HD * 0.20, 2.0, 0),  # 颅顶收
    ], seg=38, mat=pal.steel)

    # 面罩：**布尔挖槽**，不是贴一块黑片。
    # 贴片在任何角度都是"一块平的深色矩形"，而真挖出来的槽
    # 有深度、有槽壁，光斜着打过去会在槽口形成一条亮边 ——
    # 这是"目镜嵌在头盔里"和"目镜贴在头盔上"的全部差别。
    visor_cut = R.box("cut_visor", (HW * 0.80, HD * 0.46, HH * 0.17),
                      (0, -HD * 0.30, zH + HH * 0.05), mat=None, bev=0)
    R.boolean_cut(skull, [visor_cut])
    A.add(skull, "head")

    # 后脑散热/配重
    A.add(R.box("head_rear", (HW * 0.62, 0.05, HH * 0.42),
                (0, HD * 0.48, zH + HH * 0.04), mat=pal.frame, bev=0.008),
          "head")
    # 目镜：嵌在槽底（略低于槽口）
    A.add(R.ellipsoid("head_visor", (HW * 0.36, HD * 0.09, HH * 0.058),
                      (0, -HD * 0.44, zH + HH * 0.05),
                      mat=pal.visor, segments=30, rings=16,
                      cut_below=-0.15), "head")
    # 眉甲（遮挡上方，让目镜成为一条窄缝）
    A.add(R.ellipsoid("head_brow", (HW * 0.46, HD * 0.10, HH * 0.15),
                      (0, -HD * 0.50 - 0.02, zH + HH * 0.24),
                      mat=pal.accent, segments=26, rings=14,
                      cut_below=-0.45), "head")
    # 下颌格栅
    A.add(R.grille("head_jaw", (HW * 0.46, 0.04, HH * 0.20),
                   (0, -HD * 0.50 - 0.012, zH - HH * 0.26), slats=3,
                   mat=pal.joint, axis='Z'), "head")
    # 侧面传感吊舱
    for side, sx in (("L", -1.0), ("R", 1.0)):
        A.add(R.cyl("head_pod_%s" % side, HW * 0.13, 0.07,
                    (sx * HW * 0.52, -HD * 0.10, zH + HH * 0.06),
                    rot=(0, math.radians(90), 0), mat=pal.joint, verts=14,
                    bev=0.005), "head")
        A.add(R.cyl("head_podring_%s" % side, HW * 0.16, 0.02,
                    (sx * HW * 0.57, -HD * 0.10, zH + HH * 0.06),
                    rot=(0, math.radians(90), 0), mat=pal.copper, verts=14,
                    bev=0.003), "head")
        A.add(R.box("head_podlens_%s" % side, (0.012, HW * 0.10, HW * 0.10),
                    (sx * HW * 0.60, -HD * 0.10, zH + HH * 0.06),
                    mat=pal.visor, bev=0.002), "head")
    # 天线
    A.add(R.cyl("head_antenna", 0.010, 0.30,
                (HW * 0.28, HD * 0.34, zH + HH * 0.5 + 0.15), mat=pal.joint,
                verts=6, bev=0.002), "head")
    A.add(R.cyl("head_antenna_tip", 0.017, 0.045,
                (HW * 0.28, HD * 0.34, zH + HH * 0.5 + 0.31), mat=pal.core,
                verts=8, bev=0.003), "head")
    A.add(R.greeble("head_gb", (0, 0, zH), (HW, HD, HH), 8, 204,
                    pal.greeble_mats(), faces=('+X', '-X', '+Z')), "head")


def build_backpack(A, P, pal):
    TW, TD, TH = P["torso"]
    BW, BD, BH = P["backpack"]
    zB = P["z_backpack"]
    by = TD * 0.5 + BD * 0.5 + 0.01

    A.add(R.prism("backpack_main", (BW, BD, BH), (0, by, zB),
                  top=(0.92, 0.94), bottom=(0.86, 1.0),
                  mat=pal.frame, bev=0.012), "torso")
    A.add(R.box("backpack_plate", (BW * 0.72, 0.05, BH * 0.62),
                (0, by + BD * 0.5 + 0.01, zB), mat=pal.steel, bev=0.010),
          "torso")
    # 推进器（朝后下方）
    for i, sx in enumerate((-1.0, 1.0)):
        nx = sx * BW * 0.30
        ny = by + BD * 0.52
        nz = zB - BH * 0.22
        A.add(R.cyl("thruster_housing_%02d" % (i + 1), 0.075, 0.16,
                    (nx, ny + 0.03, nz), rot=(math.radians(90), 0, 0),
                    mat=pal.steel, verts=16, bev=0.006), "torso")
        A.add(R.nozzle("thruster_%02d" % (i + 1), 0.070, 0.10,
                       (nx, ny + 0.13, nz), rot=(math.radians(-90), 0, 0),
                       mat=pal.joint, inner=pal.core, verts=16), "torso")
    # 顶部散热片（收在框里）
    A.add(R.box("backpack_radiator", (BW * 0.60, BD * 0.46, 0.05),
                (0, by, zB + BH * 0.5 + 0.01), mat=pal.joint, bev=0.006),
          "torso")
    for i in range(4):
        A.add(R.box("backpack_fin_%d" % (i + 1),
                    (BW * 0.56, BD * 0.08, 0.09),
                    (0, by - BD * 0.18 + i * BD * 0.12,
                     zB + BH * 0.5 + 0.06),
                    mat=pal.accent_dark, bev=0.004), "torso")
    # 侧面小罐
    for i, sx in enumerate((-1.0, 1.0)):
        A.add(R.capsule("backpack_tank_%02d" % (i + 1), 0.048, BH * 0.46,
                        (sx * BW * 0.54, by + 0.02, zB - BH * 0.06),
                        mat=pal.copper, segments=20, rings=12), "torso")
    A.add(R.greeble("backpack_gb", (0, by, zB), (BW, BD, BH), 14, 260,
                    pal.greeble_mats(), faces=('+X', '-X', '+Z')), "torso")


def build_arm(A, P, pal, side, sx, weapon=True):
    SW, SD, SH = P["shoulder"]
    UA, FA = P["upper_arm"], P["forearm"]
    xS, xA = P["x_shoulder"], P["x_arm"]
    zS, zU, zF = P["z_shoulder"], P["z_upper"], P["z_fore"]
    bs, bu, bf = ("shoulder_%s" % side, "upperarm_%s" % side,
                  "forearm_%s" % side)

    # ── 肩关节：球窝 + 铜环（曲面，不是圆柱）──
    # ⚠️ 肩球必须放在**上臂的旋转支点**（肩关节）上，而不是内收 0.2m。
    #    旧位置 (xS-SW*0.18) 比上臂支点 (xA) 内收约 0.2m，上臂一摆动，
    #    臂顶就甩离肩球，正面看就是"肩和臂裂开一道缝"。
    jx = sx * xA
    jz = zU + UA[2] * 0.5 + 0.02
    A.add(R.sphere("shoulder_ball_%s" % side, SD * 0.29,
                   (jx, 0, jz), mat=pal.joint,
                   segments=22, rings=14), bs)
    A.add(R.torus("shoulder_ring_%s" % side, SD * 0.30, 0.017,
                  (jx, 0, jz),
                  rot=(0, math.radians(90), 0), mat=pal.copper,
                  major_seg=26, minor_seg=8), bs)
    # 肩甲：**半穹顶 + 两层弧形护壳**。
    # 原来三层斜方板从侧面看是三条直线，一眼低模；穹顶的剪影是连续弧。
    # 肩甲：**放样穹顶**（根部窄 → 外缘宽 → 收边），沿 X 方向外张。
    # 椭球穹顶的问题是它在任何方向都是同一个曲率，看起来像个球；
    # 放样可以让"上下方向"和"前后方向"的曲率不同 ——
    # 肩甲真正该是"上凸、前后收"的贝壳形。
    # ⚠️ 跨度必须**从胸腔边缘一直盖到上臂外侧**。
    #    之前只覆盖 xS±0.4·SW（约 0.39~0.60），而上臂在 x=0.68 ——
    #    肩甲根本没盖住肩关节，看起来像"胸口两侧贴了两个球"，
    #    手臂则从肩甲外面凭空长出来。
    # ⚠️ 放样的 Z 轴是**堆叠方向**，所以护肩必须沿 Z 走"碗口 → 碗顶"，
    #    不能把 5 个截面都摆在同一高度上 —— 那样做出来是一片扁翼
    #    （上一版就是这样：横向铺开 0.5m，竖向只有 5cm）。
    #
    # 现在是一个倒扣的碗：碗口（最大截面）在肩关节下方 0.11m，
    # 向上收成碗顶，正好罩住肩关节和上臂上端。
    A.add(R.loft("pauldron_dome_%s" % side, [
        # Y 半径收到 SD*0.55（直径 0.40 < 胸腔深 0.44）——
        # 之前给到 SD*0.78（直径 0.56）比胸腔还深，侧视时整个上半身
        # 被一个半圆罩住，像背了个龟壳。
        # Y 半径再收到 SD*0.42（前后直径 0.30，明显小于胸腔 0.44）——
        # 护肩该是"左右宽、前后窄"的贝壳，不是正圆碗；
        # 正圆碗从侧面看会把上半身整个罩住。
        # 碗口下移并放大：旧碗口在 zS-SH*0.56≈1.81，上臂横截面 1.80~2.01，
        # 碗口刚好压在上臂上端下沿，正面会露出一圈躯干（"上臂挂在外面"）。
        # 现在碗口下探到 zS-SH*0.78，把上臂与肩球之间的过渡包进碗里。
        ((sx * (xA + SW * 0.06), 0.000, zS - SH * 0.78),
         SW * 0.56, SD * 0.44, 3.0, 0),                          # 碗口
        ((sx * (xA + SW * 0.10), -0.005, zS - SH * 0.42),
         SW * 0.54, SD * 0.43, 3.0, 0),
        ((sx * (xA + SW * 0.12), -0.010, zS - SH * 0.26),
         SW * 0.53, SD * 0.42, 3.0, 0),
        ((sx * (xA + SW * 0.18), -0.010, zS + SH * 0.02),
         SW * 0.42, SD * 0.35, 3.0, 0),
        ((sx * (xA + SW * 0.22), 0.000, zS + SH * 0.24),
         SW * 0.25, SD * 0.23, 3.2, 0),
        ((sx * (xA + SW * 0.24), 0.000, zS + SH * 0.34),
         SW * 0.08, SD * 0.08, 3.4, 0),                          # 碗顶
    ], seg=34, mat=pal.steel), bs)
    # 识别色只做一圈收边，不做整块穹顶 —— 大色块会像塑料玩具
    A.add(R.torus("pauldron_trim_%s" % side, SW * 0.50, 0.022,
                  (sx * xS, -0.012, zS + SH * 0.10),
                  rot=(math.radians(6), 0, 0), mat=pal.accent,
                  major_seg=32, minor_seg=8), bs)
    # （这里原来还有一层 pauldron_shell 椭球护壳，dY=0.45、Z 1.98~2.14，
    #   叠在放样碗上之后侧视就是一个盖住上半身的龟壳。放样碗本身已经
    #   有"碗口 → 碗顶"的层次，不需要再加一层壳，直接删掉。）
    # 肩甲螺栓
    A.add(R.bolt_ring("pauldron_bolts_%s" % side,
                      (sx * (xS + 0.03), -0.02, zS + SH * 0.30),
                      SW * 0.30, 5, pal.copper, axis='X', r=0.013,
                      depth=0.02), bs)
    A.add(R.greeble("shoulder_gb_%s" % side, (sx * xS, 0, zS + SH * 0.2),
                    (SW, SD, SH), 8, 210 + int(sx * 3),
                    pal.greeble_mats(), faces=('+Z', '+X' if sx > 0 else '-X')),
          bs)

    # ── 上臂 ──
    # ⚠️ 上臂要往上多伸一段，接住肩球与肩甲下缘：旧版上臂顶在
    #    zU+UA[2]*0.44≈1.95，肩甲碗口在 zS-SH*0.56≈1.81，中间露出一圈空隙，
    #    正面看像"上臂挂在肩甲外面"。上臂加长并用肩球补住这段。
    A.add(R.cyl("upperarm_%s" % side, UA[0] * 0.50, UA[2] * 1.10,
                (sx * xA, 0, zU + UA[2] * 0.06), mat=pal.frame, verts=22,
                bev=0.012, segments=3), bu)
    A.add(R.ellipsoid("upperarm_armor_%s" % side,
                      (UA[0] * 0.54, UA[1] * 0.26, UA[2] * 0.32),
                      (sx * xA, -UA[1] * 0.30, zU + UA[2] * 0.05),
                      mat=pal.steel, segments=24, rings=16,
                      cut_below=-0.55), bu)
    A.add(R.box("upperarm_band_%s" % side,
                (UA[0] * 1.22, UA[1] * 0.78, 0.045),
                (sx * xA, 0, zU + UA[2] * 0.34), mat=pal.accent, bev=0.005),
          bu)
    # 肱二头液压
    A.add(R.piston("arm_piston_%s" % side,
                   (sx * (xA + UA[0] * 0.62), UA[1] * 0.34, zU + UA[2] * 0.36),
                   (sx * (xA + FA[0] * 0.50), FA[1] * 0.30, zF + FA[2] * 0.30),
                   UA[0] * 0.13, pal.steel_light, pal.copper), bf)
    A.add(R.greeble("upperarm_gb_%s" % side, (sx * xA, 0, zU),
                    (UA[0], UA[1], UA[2]), 7, 220 + int(sx * 3),
                    pal.greeble_mats(),
                    faces=('+X' if sx > 0 else '-X', '-Y')), bu)

    # ── 肘 ──
    elbow = (sx * xA, 0, zU - UA[2] * 0.5 - 0.01)
    A.add(R.sphere("elbow_%s" % side, UA[0] * 0.40, elbow, mat=pal.joint,
                   segments=20, rings=14), bf)
    A.add(R.torus("elbow_ring_%s" % side, UA[0] * 0.40, 0.016,
                  (elbow[0] + sx * UA[0] * 0.34, elbow[1], elbow[2]),
                  rot=(0, math.radians(90), 0), mat=pal.copper,
                  major_seg=24, minor_seg=8), bf)

    # ── 前臂 ──
    A.add(R.cyl("forearm_%s" % side, FA[0] * 0.54, FA[2] * 0.84,
                (sx * xA, 0, zF), mat=pal.frame, verts=22,
                bev=0.012, segments=3), bf)
    A.add(R.ellipsoid("forearm_armor_%s" % side,
                      (FA[0] * 0.56, FA[1] * 0.26, FA[2] * 0.30),
                      (sx * xA, -FA[1] * 0.30, zF + FA[2] * 0.04),
                      mat=pal.steel, segments=24, rings=16,
                      cut_below=-0.55), bf)
    # 识别色条贴在前臂外表面上：前臂圆柱半径 = FA[0]*0.54/2 ≈ 0.038，
    # 中心在 xA。旧值 xA+FA[0]*0.56=0.64 飘在空气里（悬空短杆），
    # 现在贴在圆柱表面（外缘减半个条厚）。
    A.add(R.box("forearm_stripe_%s" % side,
                (0.016, 0.03, FA[2] * 0.46),
                (sx * (xA + FA[0] * 0.27 - 0.008), -FA[1] * 0.30, zF),
                mat=pal.accent, bev=0.004), bf)
    A.add(R.grille("forearm_vent_%s" % side, (FA[0] * 0.42, 0.03, FA[2] * 0.24),
                   (sx * xA, -FA[1] * 0.52, zF - FA[2] * 0.16), slats=3,
                   mat=pal.joint, axis='Z'), bf)

    if weapon:
        # 武器：机匣 + 炮管 + 冷却环 + 制退器
        ry = -FA[1] * 0.5
        A.add(R.box("gun_receiver_%s" % side, (FA[0] * 0.66, FA[1] * 0.55,
                                               FA[2] * 0.34),
                    (sx * xA, ry - FA[1] * 0.18, zF + FA[2] * 0.10),
                    mat=pal.frame, bev=0.008), bf)
        A.add(R.box("gun_feed_%s" % side, (FA[0] * 0.30, FA[1] * 0.30, 0.10),
                    (sx * (xA + FA[0] * 0.34), ry - FA[1] * 0.10,
                     zF + FA[2] * 0.20), mat=pal.copper, bev=0.006), bf)
        A.add(R.cyl("gun_barrel_%s" % side, FA[0] * 0.16, FA[1] * 1.05,
                    (sx * xA, ry - FA[1] * 0.86, zF + FA[2] * 0.06),
                    rot=(math.radians(90), 0, 0), mat=pal.steel_light,
                    verts=16, bev=0.004), bf)
        for i in range(3):
            A.add(R.cyl("gun_ring_%s_%d" % (side, i + 1), FA[0] * 0.21, 0.022,
                        (sx * xA, ry - FA[1] * (0.52 + i * 0.26),
                         zF + FA[2] * 0.06),
                        rot=(math.radians(90), 0, 0), mat=pal.copper,
                        verts=16, bev=0.003), bf)
        # 制退器（带两侧排气槽）
        A.add(R.box("gun_brake_%s" % side, (FA[0] * 0.36, FA[1] * 0.22,
                                            FA[2] * 0.26),
                    (sx * xA, ry - FA[1] * 1.42, zF + FA[2] * 0.06),
                    mat=pal.joint, bev=0.006), bf)
        A.add(R.box("gun_muzzle_%s" % side, (FA[0] * 0.20, FA[1] * 0.10,
                                             FA[2] * 0.16),
                    (sx * xA, ry - FA[1] * 1.54, zF + FA[2] * 0.06),
                    mat=pal.frame, bev=0.004), bf)
    else:
        # 左臂：传感器 / 机械爪
        ry = -FA[1] * 0.5
        A.add(R.cyl("arm_sensor_%s" % side, FA[0] * 0.30, 0.10,
                    (sx * xA, ry - 0.06, zF + FA[2] * 0.10),
                    rot=(math.radians(90), 0, 0), mat=pal.joint, verts=16,
                    bev=0.005), bf)
        A.add(R.cyl("arm_sensorlens_%s" % side, FA[0] * 0.20, 0.03,
                    (sx * xA, ry - 0.12, zF + FA[2] * 0.10),
                    rot=(math.radians(90), 0, 0), mat=pal.visor, verts=16,
                    bev=0.003), bf)
        # 机械爪：三根**放样指**（根粗尖细、向前收成一点）。
        # 原来是三根 5×22×5cm 的直方条斜伸出去 —— 从任何角度看都像一把叉子。
        # 爪子必须是锥形：根部有指节，往前逐段收细，指尖是一个点。
        for i in range(3):
            a = -0.5 + i * 0.5
            fx = sx * (xA + a * 0.14)
            # 指根：一个球关节
            A.add(R.sphere("clawjoint_%s_%d" % (side, i + 1), 0.030,
                           (fx, ry - 0.09, zF - 0.02), mat=pal.joint,
                           segments=16, rings=12), bf)
            A.add(R.loft("claw_%s_%d" % (side, i + 1), [
                ((0, 0, 0.00), 0.028, 0.028, 2.6, 0),
                ((0, 0, 0.11), 0.021, 0.021, 2.4, 0),
                ((0, 0, 0.21), 0.012, 0.012, 2.2, 0),
                ((0, 0, 0.28), 0.004, 0.004, 2.0, 0),   # 指尖收成一点
            ], seg=14, mat=pal.steel_light,
                loc=(fx, ry - 0.09, zF - 0.02),
                rot=(math.radians(90), 0, 0)), bf)

    # 动力线束
    A.add(R.cable("arm_cable_%s" % side,
                  [(sx * (xS + SW * 0.24), SD * 0.34, zS - SH * 0.24),
                   (sx * (xA + UA[0] * 0.56), UA[1] * 0.42, zU - UA[2] * 0.24),
                   (sx * (xA + FA[0] * 0.50), FA[1] * 0.44, zF + FA[2] * 0.30)],
                  0.016, pal.joint), bf)


def build_leg(A, P, pal, side, sx):
    TG, SN, FT = P["thigh"], P["shin"], P["foot"]
    xL = P["x_leg"]
    zTH, zSN, zFT = P["z_thigh"], P["z_shin"], P["z_foot"]
    bth, bsh, bft = ("thigh_%s" % side, "shin_%s" % side, "foot_%s" % side)

    hip_z = zTH + TG[2] * 0.5
    knee_z = zTH - TG[2] * 0.5 + 0.01
    ankle_z = zSN - SN[2] * 0.5 - 0.02

    # ── 大腿：**一条放样**（髋部圆粗 → 中段微收 → 膝部方窄）──
    #
    # 原来是等径圆柱 —— 上下一样粗，所以大腿看起来像根管子。
    # 放样让截面从髋部的椭圆（n=2.2）连续过渡到膝部的圆角方（n=3.4），
    # 同时半径递减：这就是"肌肉感 → 机械关节"的过渡，
    # 一个函数就做完了，拼接做不到。
    A.add(R.loft("thigh_%s" % side, [
        ((sx * xL, 0.000, hip_z - 0.03), TG[0] * 0.50, TG[1] * 0.52, 2.2, 0),
        ((sx * xL, -0.008, zTH + TG[2] * 0.26), TG[0] * 0.47, TG[1] * 0.49, 2.6, 0),
        ((sx * xL, -0.012, zTH), TG[0] * 0.43, TG[1] * 0.45, 2.9, 0),
        ((sx * xL, -0.008, zTH - TG[2] * 0.26), TG[0] * 0.39, TG[1] * 0.41, 3.1, 0),
        # ⚠️ 下端必须**越过**膝关节（knee_z-0.02），不能停在 knee_z+0.03 ——
        #    那样大腿和小腿之间会露出一道 6cm 的缝，膝盖看起来是断的。
        ((sx * xL, 0.000, knee_z - 0.03), TG[0] * 0.34, TG[1] * 0.36, 3.4, 0),
    ], seg=34, mat=pal.frame), bth)
    # 大腿正面装甲：**放样壳**（上宽下窄，中间鼓）
    # 椭球切半做出来的是个"鼓包"，边缘和腿之间有一条硬边；
    # 放样可以让护甲自己收边，跟大腿的锥度对上。
    A.add(R.loft("thigh_armor_%s" % side, [
        ((sx * xL, -TG[1] * 0.26, zTH + TG[2] * 0.34),
         TG[0] * 0.40, TG[1] * 0.13, 3.8, 0),
        ((sx * xL, -TG[1] * 0.33, zTH + TG[2] * 0.12),
         TG[0] * 0.50, TG[1] * 0.19, 3.1, 0),
        ((sx * xL, -TG[1] * 0.31, zTH - TG[2] * 0.12),
         TG[0] * 0.46, TG[1] * 0.17, 2.8, 0),
        ((sx * xL, -TG[1] * 0.24, zTH - TG[2] * 0.34),
         TG[0] * 0.33, TG[1] * 0.12, 2.6, 0),
    ], seg=30, mat=pal.steel), bth)
    # 大腿外侧小装甲 + 编号块
    A.add(R.box("thigh_side_%s" % side, (0.035, TG[1] * 0.44, TG[2] * 0.40),
                (sx * (xL + TG[0] * 0.56), TG[1] * 0.06, zTH + TG[2] * 0.10),
                mat=pal.steel_light, bev=0.006), bth)
    A.add(R.box("thigh_tag_%s" % side, (0.02, 0.10, 0.05),
                (sx * (xL + TG[0] * 0.60), -TG[1] * 0.10,
                 zTH + TG[2] * 0.26), mat=pal.accent, bev=0.003), bth)
    # 髋罩：球窝 + 铜环（曲面，转动时不会露出直角接缝）
    A.add(R.sphere("hipcowl_%s" % side, TG[0] * 0.38,
                   (sx * xL, 0, hip_z - 0.01), mat=pal.joint,
                   segments=22, rings=16), bth)
    A.add(R.torus("hipring_%s" % side, TG[0] * 0.38, 0.014,
                  (sx * (xL + TG[0] * 0.34), 0, hip_z - 0.01),
                  rot=(0, math.radians(90), 0), mat=pal.copper,
                  major_seg=26, minor_seg=8), bth)
    A.add(R.greeble("thigh_gb_%s" % side, (sx * xL, 0, zTH),
                    (TG[0], TG[1], TG[2]), 8, 240 + int(sx * 3),
                    pal.greeble_mats(),
                    faces=('+X' if sx > 0 else '-X', '+Y', '-Y')), bth)

    # ── 膝 ──
    A.add(R.sphere("knee_%s" % side, TG[0] * 0.34,
                   (sx * xL, -TG[1] * 0.04, knee_z), mat=pal.joint,
                   segments=22, rings=16), bth)
    A.add(R.torus("knee_ring_%s" % side, TG[0] * 0.35, 0.017,
                  (sx * (xL + TG[0] * 0.36), -TG[1] * 0.04, knee_z),
                  rot=(0, math.radians(90), 0), mat=pal.copper,
                  major_seg=26, minor_seg=8), bth)
    # 护膝：**放样曲面罩**，不是一块斜扣的方板。
    #
    # 膝盖是整条腿上曲率最大的位置（大腿向下收、小腿向后弯），
    # 方板扣上去必然在两个方向都翘边 —— 之前那一块蓝板就是这样，
    # 从侧面看它和腿之间有一条明显的三角形缝隙。
    # 放样让护膝自己带曲率：中间鼓出去盖住关节，上下两端贴回腿上。
    A.add(R.loft("kneecap_%s" % side, [
        ((sx * xL, -TG[1] * 0.28, knee_z + TG[2] * 0.22),
         TG[0] * 0.30, TG[1] * 0.13, 3.4, 0),
        ((sx * xL, -TG[1] * 0.44, knee_z + TG[2] * 0.06),
         TG[0] * 0.43, TG[1] * 0.20, 2.8, 0),
        ((sx * xL, -TG[1] * 0.42, knee_z - TG[2] * 0.10),
         TG[0] * 0.41, TG[1] * 0.18, 2.6, 0),
        ((sx * xL, -TG[1] * 0.28, knee_z - TG[2] * 0.24),
         TG[0] * 0.27, TG[1] * 0.12, 2.4, 0),
    ], seg=28, mat=pal.accent), bth)

    # ── 小腿 ──
    # ── 小腿：放样，且截面中心向后偏 —— 小腿骨本来就是弯的，
    #    等径直筒会让整条腿看起来像"两根筷子"。
    A.add(R.loft("shin_%s" % side, [
        ((sx * xL, 0.000, knee_z + 0.04), SN[0] * 0.40, SN[1] * 0.42, 3.2, 0),
        ((sx * xL, 0.010, zSN + SN[2] * 0.22), SN[0] * 0.39, SN[1] * 0.42, 3.0, 0),
        ((sx * xL, 0.016, zSN), SN[0] * 0.35, SN[1] * 0.38, 2.8, 0),
        ((sx * xL, 0.012, zSN - SN[2] * 0.24), SN[0] * 0.30, SN[1] * 0.33, 2.6, 0),
        ((sx * xL, 0.004, ankle_z - 0.06), SN[0] * 0.24, SN[1] * 0.26, 2.4, 0),
    ], seg=32, mat=pal.frame), bsh)
    # 胫甲
    # 胫甲：放样壳（膝下宽 → 踝上窄），带一点向前的弧
    A.add(R.loft("shin_guard_%s" % side, [
        ((sx * xL, -SN[1] * 0.22, zSN + SN[2] * 0.36),
         SN[0] * 0.40, SN[1] * 0.14, 3.6, 0),
        ((sx * xL, -SN[1] * 0.30, zSN + SN[2] * 0.10),
         SN[0] * 0.48, SN[1] * 0.19, 3.0, 0),
        ((sx * xL, -SN[1] * 0.28, zSN - SN[2] * 0.16),
         SN[0] * 0.42, SN[1] * 0.17, 2.8, 0),
        ((sx * xL, -SN[1] * 0.20, zSN - SN[2] * 0.38),
         SN[0] * 0.30, SN[1] * 0.12, 2.6, 0),
    ], seg=30, mat=pal.steel), bsh)
    # 小腿外侧加强筋：贴在小腿外壳表面。
    # 小腿最宽处半宽 SN[0]*0.40≈0.076，旧值 xL+SN[0]*0.56≈0.32 悬在外侧 3.5cm。
    A.add(R.box("shin_rib_%s" % side, (0.03, SN[1] * 0.30, SN[2] * 0.52),
                (sx * (xL + SN[0] * 0.36), -SN[1] * 0.16, zSN),
                mat=pal.steel_light, bev=0.006), bsh)
    # 膝关节液压（大腿后侧 → 小腿后侧）
    A.add(R.piston("knee_piston_%s" % side,
                   (sx * (xL + TG[0] * 0.48), TG[1] * 0.36,
                    knee_z + TG[2] * 0.16),
                   (sx * (xL + SN[0] * 0.46), SN[1] * 0.34,
                    zSN + SN[2] * 0.16),
                   TG[0] * 0.11, pal.steel_light, pal.copper), bsh)

    # 散热器：**收进壳体**（凹陷框 + 内嵌鳍片），不再外挂
    n_fin = P["fin_count"]
    fh = 0.030 * P["fin_scale"]
    housing_h = n_fin * (fh * 1.55) + 0.05
    A.add(R.box("radiator_housing_%s" % side,
                (SN[0] * 0.78, 0.07, housing_h),
                (sx * xL, SN[1] * 0.52, zSN + SN[2] * 0.06),
                mat=pal.frame, bev=0.008), bsh)
    for i in range(n_fin):
        A.add(R.box("radiator_fin_%s_%02d" % (side, i + 1),
                    (SN[0] * 0.70, 0.045, fh),
                    (sx * xL, SN[1] * 0.55,
                     zSN + SN[2] * 0.06 - housing_h * 0.5 + 0.03
                     + i * fh * 1.55),
                    mat=pal.accent_dark, bev=0.003), bsh)

    # ── 踝 ──
    A.add(R.sphere("ankle_%s" % side, SN[0] * 0.28,
                   (sx * xL, 0, ankle_z), mat=pal.joint,
                   segments=20, rings=14), bsh)
    # 踝护甲（盖住踝关节，随小腿）
    A.add(R.prism("ankle_guard_%s" % side, (SN[0] * 0.92, 0.09, 0.16),
                  (sx * xL, -SN[1] * 0.40, ankle_z + 0.05),
                  top=(0.94, 1.0), bottom=(0.80, 1.0),
                  mat=pal.steel, bev=0.008), bsh)
    # 跟腱液压（小腿后 → 脚跟）
    A.add(R.piston("ankle_piston_%s" % side,
                   (sx * xL, SN[1] * 0.34, ankle_z + 0.20),
                   (sx * xL, FT[1] * 0.34, zFT + FT[2] * 0.20),
                   0.020, pal.steel_light, pal.copper), bft)

    # ── 足：**一条放样靴形**（脚跟窄 → 脚掌宽 → 趾尖收）──
    #
    # 原来是"脚跟 prism + 脚掌圆角方盒 + 脚趾椭球"三件拼的，
    # 三件之间的交界在低角度看是一道折线，整只脚像积木。
    # 放样沿"脚跟 → 趾尖"走，截面从窄圆过渡到宽扁方，
    # 鞋型是一条连续曲线 —— 这是这一轮改动里视觉收益最直接的。
    #
    # rot=(90,0,0) 把放样的 +Z 轴转到世界 -Y（脚跟朝后、趾尖朝前）。
    A.add(R.loft("foot_%s" % side, [
        ((0, 0, 0.00), FT[0] * 0.34, FT[2] * 0.40, 3.8, 0),   # 脚跟
        ((0, 0, FT[1] * 0.20), FT[0] * 0.46, FT[2] * 0.46, 3.2, 0),
        ((0, 0, FT[1] * 0.50), FT[0] * 0.50, FT[2] * 0.40, 3.0, 0),  # 脚掌最宽
        ((0, 0, FT[1] * 0.80), FT[0] * 0.44, FT[2] * 0.30, 3.3, 0),
        ((0, 0, FT[1] * 1.00), FT[0] * 0.30, FT[2] * 0.18, 3.8, 0),  # 趾尖
    ], seg=30, mat=pal.steel,
        # 脚底要落在鞋底防滑纹（tread，z≈zFT-FT[2]*0.5）上。
        # 旧值 zFT+FT[2]*0.16 把整只脚抬得太高，脚底悬在 tread 上方一截，
        # 侧面看就是"脚下面飘着几块平板"。降到让脚底≈tread 高度。
        loc=(sx * xL, FT[1] * 0.50, zFT - FT[2] * 0.10),
        rot=(math.radians(90), 0, 0)), bft)
    # 趾甲（accent）：贴在趾尖上的一小片
    A.add(R.ellipsoid("toecap_%s" % side,
                      (FT[0] * 0.34, FT[2] * 0.20, 0.035),
                      (sx * xL, -FT[1] * 0.48, zFT - FT[2] * 0.10),
                      mat=pal.accent, segments=24, rings=14,
                      cut_below=-0.30), bft)
    # 鞋底防滑（三条横纹）
    for i in range(3):
        A.add(R.box("tread_%s_%d" % (side, i + 1),
                    (FT[0] * 0.86, FT[1] * 0.16, 0.025),
                    (sx * xL, -FT[1] * 0.30 + i * FT[1] * 0.20,
                     zFT - FT[2] * 0.5),
                    mat=pal.joint, bev=0.004), bft)
    # 脚的 greeble 盒必须贴合脚的实际高度（放样靴约 0.13m），
    # 旧盒用 FT[2]=0.22、中心在 zFT，盒上半部的块全浮在脚上方（悬空件）。
    A.add(R.greeble("foot_gb_%s" % side,
                    (sx * xL, -FT[1] * 0.10, zFT - FT[2] * 0.28),
                    (FT[0], FT[1] * 0.85, FT[2] * 0.55), 6, 270 + int(sx * 3),
                    pal.greeble_mats(), faces=('+X' if sx > 0 else '-X', '-Y')),
          bft)


def build(P, pal):
    A = Assembler(pal)
    build_pelvis(A, P, pal)
    build_torso(A, P, pal)
    build_head(A, P, pal)
    build_backpack(A, P, pal)
    for side, sx in (("L", -1.0), ("R", 1.0)):
        build_arm(A, P, pal, side, sx, weapon=(side == "R"))
        build_leg(A, P, pal, side, sx)
    return A


# ══════════ 骨架 ══════════
#
# ⚠️ 关于骨骼原点的铁律（改动前务必读完）
# ─────────────────────────────────────────────────────────────
# 程序化动画摆骨骼时，旋转**永远绕骨骼自身的原点（head）**进行。
# 所以「骨骼原点放在哪」直接决定「肢体绕哪转」：
#
#   ✗ 原点放在部件质心  → 大腿往后摆、脚往前甩，整条腿像跷跷板
#   ✓ 原点放在关节      → 大腿绕髋转、小腿绕膝转、脚绕踝转 —— 正常步态
#
# 关节位置不是拍脑袋的，而是**从建模参数直接算出来**的 —— 建模时把
# 膝关节壳体放在 `zTH - TG[2]/2`、踝关节壳体放在 `zSN - SN[2]/2`，
# 骨骼原点就用同一个公式，保证与几何严格重合。

def build_rig(A, P):
    pc = A.bone_center("pelvis")
    tc = A.bone_center("torso")
    hc = A.bone_center("head")

    TG, SN, FT = P["thigh"], P["shin"], P["foot"]
    UA, FA = P["upper_arm"], P["forearm"]
    xL, xA, xS = P["x_leg"], P["x_arm"], P["x_shoulder"]
    zTH, zSN, zFT = P["z_thigh"], P["z_shin"], P["z_foot"]
    zU, zF, zS = P["z_upper"], P["z_fore"], P["z_shoulder"]

    defs = [
        dict(name="root", head=(0, 0, 0), tail=(0, 0, 0.20)),
        dict(name="pelvis", head=pc, tail=tc, parent="root"),
        dict(name="torso", head=tc, tail=hc, parent="pelvis", connect=True),
        dict(name="head", head=hc,
             tail=(hc[0], hc[1], hc[2] + A.bone_size("head")[2] * 0.9),
             parent="torso", connect=True),
    ]

    for side, sx in (("L", -1.0), ("R", 1.0)):
        hip = (sx * xL, 0.0, zTH + TG[2] * 0.5)
        knee = (sx * xL, -TG[1] * 0.04, zTH - TG[2] * 0.5 + 0.01)
        ankle = (sx * xL, 0.0, zSN - SN[2] * 0.5 - 0.02)
        toe = (sx * xL, -FT[1] * 0.50, zFT - FT[2] * 0.5 + 0.02)
        defs += [
            dict(name="thigh_%s" % side, head=hip, tail=knee, parent="pelvis"),
            dict(name="shin_%s" % side, head=knee, tail=ankle,
                 parent="thigh_%s" % side, connect=True),
            dict(name="foot_%s" % side, head=ankle, tail=toe,
                 parent="shin_%s" % side, connect=True),
        ]

        clav = (sx * xS * 0.30, 0.0, zS - 0.02)
        shoulder = (sx * xA, 0.0, zU + UA[2] * 0.5 + 0.02)
        elbow = (sx * xA, 0.0, zU - UA[2] * 0.5 - 0.01)
        hand = (sx * xA, -FA[1] * 0.5 - 0.10, zF - FA[2] * 0.5 + 0.02)
        defs += [
            dict(name="shoulder_%s" % side, head=clav, tail=shoulder,
                 parent="torso"),
            dict(name="upperarm_%s" % side, head=shoulder, tail=elbow,
                 parent="shoulder_%s" % side, connect=True),
            dict(name="forearm_%s" % side, head=elbow, tail=hand,
                 parent="upperarm_%s" % side, connect=True),
        ]
    return defs


# ═══════════════════════════════════════════════════════════
# 单机型流程
# ═══════════════════════════════════════════════════════════

def build_one(variant, out_dir, do_render=True, do_uv=True, do_lod=True):
    print("\n" + "=" * 58)
    print("机体: %s" % variant)
    print("=" * 58)

    R.new_scene()
    P = variant_params(variant)
    pal = R.Palette(P["accent"], P["glow"], P["code"])

    A = build(P, pal)
    print("  部件对象: %d   骨骼: %d" % (len(A.all), len(A.by_bone)))

    # ── 调试：导出每个部件的世界包围盒，定位悬空件 ──
    import os as _os
    from mathutils import Vector as _V
    dump = []
    for ob in A.all:
        if ob.type != 'MESH':
            continue
        mn = [1e9] * 3
        mx = [-1e9] * 3
        for c in ob.bound_box:
            w = ob.matrix_world @ _V(c)
            for i in range(3):
                mn[i] = min(mn[i], w[i])
                mx[i] = max(mx[i], w[i])
        dump.append("%-26s c=(%+.2f,%+.2f,%+.2f) sz=(%.2f,%.2f,%.2f)"
                    % (ob.name, (mn[0]+mx[0])*0.5, (mn[1]+mx[1])*0.5,
                       (mn[2]+mx[2])*0.5, mx[0]-mn[0], mx[1]-mn[1], mx[2]-mn[2]))
    with open(_os.path.join(out_dir, "parts_%s.txt" % variant), "w") as f:
        f.write("\n".join(dump))

    defs = build_rig(A, P)

    # ── 肩甲改挂躯干骨 ──
    # 肩骨的静止/瞄准姿态会把整块肩甲穹顶转进胸腔，正面只剩两个“白色胸包”。
    # 肩甲本质是护在肩上的壳，跟着躯干走最稳；球窝 + 铜环仍留在肩骨上，
    # 这样手臂瞄准时肩甲不会跟着甩进身体。
    for side in ("L", "R"):
        key = "shoulder_%s" % side
        source = A.by_bone.get(key, [])
        moved = [o for o in source
                 if o.name.startswith(("pauldron_", "shoulder_gb_"))]
        if moved:
            A.by_bone[key] = [o for o in source if o not in moved]
            A.by_bone.setdefault("torso", []).extend(moved)
            print("  肩甲改挂躯干: %s -> %d 件" % (key, len(moved)))

    for bone, objs in A.by_bone.items():
        for ob in objs:
            R.assign_group(ob, bone)

    mesh = R.join_objects(A.all, "SK_Chassis_%s" % P["code"].capitalize())
    tri0 = R.tri_count(mesh)
    print("  LOD0 三角面: %d" % tri0)

    mn, mx = R.world_bounds([mesh])
    print("  包围盒: 高 %.2f m  宽 %.2f m  深 %.2f m  (设计 %s)"
          % (mx[2] - mn[2], mx[0] - mn[0], mx[1] - mn[1], P["height_note"]))

    base = os.path.join(out_dir, "chassis_%s" % P["code"])

    # ⚠️ UV 必须在**生成 LOD 之前**做。
    #
    #    原来 cube_uv 写在 make_lod 之后，而 make_lod 是 ob.data.copy() ——
    #    也就是 LOD1/LOD2 拷贝到的是"还没展开 UV"的网格，
    #    它们的 UV 最后被导出成归一化的 0~1（实测 FBX 里 LOD1 有 2 个 UV 层、
    #    范围 0~1）。UE 侧结果就是机体表面被贴图糊成一团单色，
    #    近看完全没有装甲板结构 —— 这就是"纹理不像装甲"的最后一个原因。
    if do_uv:
        # 世界对齐立方投影：1 个 UV 单位 = 1.2m，和材质的 TextureSize 对应
        ok = R.cube_uv(mesh, size_m=3.2)   # 4K 铺 3.2m → 约 1280 px/m，近景够用且不密
        print("  UV 展开(立方投影): %s" % ("完成" if ok else "失败"))

    lod_names = []
    if do_lod:
        for ratio, sfx in ((0.45, "_LOD1"), (0.18, "_LOD2")):
            lod = R.make_lod(mesh, ratio, sfx)
            lod_names.append((lod.name, R.tri_count(lod)))
        print("  LOD: " + "  ".join("%s=%d" % (n, t) for n, t in lod_names))
        for n, _ in lod_names:
            ob = bpy.data.objects[n]
            R.activate(ob)
        lod_col = bpy.data.collections.new("LODs")
        bpy.context.scene.collection.children.link(lod_col)
        for n, _ in lod_names:
            ob = bpy.data.objects[n]
            for c in list(ob.users_collection):
                c.objects.unlink(ob)
            lod_col.objects.link(ob)

    arm = R.make_armature("SK_Chassis_%s_Rig" % P["code"].capitalize(), defs)
    R.bind(mesh, arm)
    print("  骨架: %s (%d 骨骼)" % (arm.name, len(defs)))

    R.save_blend(base + ".blend")
    print("  [ok] chassis_%s.blend" % P["code"])
    try:
        R.export_fbx(base + ".fbx")
        print("  [ok] chassis_%s.fbx" % P["code"])
    except Exception as e:
        print("  [FAIL] FBX: %s" % e)
    R.export_glb(base + ".glb")

    if do_render:
        png = os.path.join(out_dir, "preview_chassis_%s.png" % P["code"])
        try:
            R.setup_render(png, (0, 0, (mn[2] + mx[2]) * 0.5), 5.6)
            R.render_to(png)
            print("  [ok] preview_chassis_%s.png" % P["code"])
        except Exception as e:
            print("  [warn] 渲染失败: %s" % e)

    return dict(code=P["code"], name=P["name"], tri0=tri0,
                lods=lod_names,
                bounds=(mx[2] - mn[2], mx[0] - mn[0], mx[1] - mn[1]))


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    chassis, out_dir, render, lod = "medium", "./out", True, True
    i = 0
    while i < len(argv):
        if argv[i] == "--chassis" and i + 1 < len(argv):
            chassis = argv[i + 1]; i += 2
        elif argv[i] == "--out" and i + 1 < len(argv):
            out_dir = argv[i + 1]; i += 2
        elif argv[i] == "--no-render":
            render = False; i += 1
        elif argv[i] == "--no-lod":
            # 诊断用：FBX 里只放 LOD0。
            # UE 的骨骼网格导入对"多个网格当 LOD"的处理有坑，
            # 只留 LOD0 可以排除这条路径（LOD 交给 UE 自己生成更稳）。
            lod = False; i += 1
        else:
            i += 1

    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    print("Blender %s  ->  %s" % (bpy.app.version_string, out_dir))

    vs = ["light", "medium", "heavy"] if chassis == "all" else [chassis]
    results = [build_one(v, out_dir, render, True, lod) for v in vs]

    print("\n" + "-" * 58)
    for r in results:
        print("  %-8s %-10s LOD0 %6d tris   %.2f x %.2f x %.2f m"
              % (r["code"], r["name"], r["tri0"], *r["bounds"]))
    print("完成。")


if __name__ == "__main__":
    main()
