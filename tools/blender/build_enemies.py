"""
余火协议 · 敌人构建
================================================
生成敌人机体。每个敌人都带与玩家同一套的部位命名（part_core / part_arm_* /
part_leg_* / part_torso），这样游戏里的 PartDamageComponent 一套代码通吃敌我。

用法:
    blender --background --python build_enemies.py -- --out ../../assets/out

敌人清单:
    巡逻机 / 运输机 / 维修巨像 / 园丁机 / 气象机 / 重型护卫

── 2026-10-23 重做：从"方盒拼接"改为"壳体 + 装甲切面" ──
旧版全部由 R.box 拼成，剪影是直线段和直角，无论加多少倒角都像占位符。
现在遵循三条规则：
  1. 主体轮廓必须是曲线（椭球 / 圆柱 / 圆角棱柱），直角只允许出现在
     "装甲板"这种本来就该是板的地方，而且倒角段数 ≥ 3。
  2. 每个关节 = 球窝 + 铜环。球是轴，环是密封圈，这是机械件的通用语法。
  3. 每种敌人必须有**一眼能认出的剪影特征**：
     巡逻机=悬浮环 / 运输机=横卧货舱筒 / 巨像=穹顶胸腔+巨臂 /
     园丁=围裙 / 气象=雷达罩 / 护卫=双穹顶肩甲+盾。
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
# 1. 巡逻机 —— 小型悬浮侦察单位
# ═══════════════════════════════════════════════════════════

def patrol(pal):
    """悬浮侦察机：扁椭球壳体 + 三道悬浮环 + 单眼。

    剪影特征：没有腿，靠三道水平光环悬浮。这是全场唯一"非人形"敌人，
    玩家在远处也能靠轮廓立刻分辨。
    """
    o = []
    R0 = 0.44                       # 壳体基准半径
    z = 0.80

    # ── 壳体：**球体**，不是扁饼 ──
    # 之前的 z 半径只有 0.60·R0，三层环再一压，整个剪影是个汉堡。
    # 做成接近正球之后，"球形核心 + 外围光环"才是可读的悬浮机体。
    o.append(R.ellipsoid("part_torso", (R0, R0 * 1.04, R0 * 0.90), (0, 0, z),
                         mat=pal.steel, segments=36, rings=24))
    # 上壳：小一圈的穹顶，压出"两级台阶"的层次
    o.append(R.ellipsoid("chassis_dome",
                         (R0 * 0.70, R0 * 0.76, R0 * 0.52),
                         (0, 0, z + R0 * 0.34),
                         mat=pal.steel_light, segments=32, rings=20,
                         cut_below=-0.10))

    # ── 三道悬浮环：由内向外逐级放大，最外圈用识别色 ──
    # ── 单道大光环：离球体足够远，中间用三根辐条连 ──
    # 三道同心环挤在 0.92~1.08·R0 之间，视觉上会糊成一圈厚边；
    # 一道半径 1.5·R0 的细环反而轮廓干净，也真的像"悬浮装置"。
    o.append(R.torus("chassis_hoverring", R0 * 1.50, 0.032,
                     (0, 0, z - R0 * 0.12), mat=pal.accent,
                     major_seg=48, minor_seg=12))
    o.append(R.torus("chassis_hoverring_in", R0 * 1.46, 0.014,
                     (0, 0, z - R0 * 0.12), mat=pal.copper,
                     major_seg=48, minor_seg=8))
    for i in range(3):
        a = math.pi * 0.5 + i * 2.0 * math.pi / 3.0
        # ⚠️ 第七十九轮：辐条内端原来只到半径 0.313、且 Y 偏移 0.51 已超出壳体
        #    （Y 半径仅 0.458）—— 悬浮环整组与壳体断开。加长辐条并往内收。
        o.append(R.prism("chassis_hoverspoke_%d" % (i + 1),
                         (0.042, 0.46, 0.026),
                         (math.cos(a) * R0 * 1.02, math.sin(a) * R0 * 1.05,
                          z - R0 * 0.12),
                         rot=(0, 0, a), mat=pal.joint, bev=0.005,
                         segments=2))
    # 环上的传感器吊舱：挂在环外侧（左右各一），让光环不只是装饰
    for s2, sx in (("L", -1), ("R", 1)):
        o.append(R.ellipsoid("chassis_pod_%s" % s2, (0.085, 0.135, 0.095),
                             (sx * R0 * 1.52, 0.02, z - R0 * 0.12),
                             mat=pal.steel_light, segments=22, rings=14,
                             cut_below=-0.35))
        o.append(R.sphere("chassis_podlens_%s" % s2, 0.042,
                          (sx * R0 * 1.52, -0.11, z - R0 * 0.12),
                          mat=pal.visor, segments=16, rings=12))

    # ── 单眼：眼珠 + 眼眶环 + 弧形护罩 ──
    ey = -R0 * 1.02
    o.append(R.sphere("part_core", 0.088, (0, ey, z + 0.02),
                      mat=pal.core, segments=26, rings=18))
    o.append(R.torus("part_corering", 0.100, 0.019, (0, ey, z + 0.02),
                     rot=(math.radians(90), 0, 0), mat=pal.joint,
                     major_seg=32, minor_seg=10))
    # 护罩：向前突出的半椭球壳，把眼珠包进去
    o.append(R.ellipsoid("chassis_eyecowl",
                         (0.155, 0.115, 0.135), (0, ey + 0.055, z + 0.02),
                         mat=pal.accent, segments=28, rings=18,
                         cut_below=-0.35))

    # ── 下方两门短炮（part_arm_*，伤害系统按手臂部位算）──
    for s, sx in (("L", -1), ("R", 1)):
        gx, gy, gz = sx * 0.175, -0.115, z - R0 * 0.60 - 0.055
        o.append(R.cyl("part_arm_%s" % s, 0.030, 0.26, (gx, gy, gz),
                       rot=(math.radians(78), 0, 0), mat=pal.joint,
                       verts=16, bev=0.004, segments=2))
        o.append(R.torus("arm_collar_%s" % s, 0.038, 0.010,
                         (gx, gy + 0.035, gz + 0.025),
                         rot=(math.radians(78), 0, 0), mat=pal.copper,
                         major_seg=20, minor_seg=8))
        o.append(R.cyl("arm_muzzle_%s" % s, 0.020, 0.045,
                       (gx, gy - 0.135, gz - 0.030),
                       rot=(math.radians(78), 0, 0), mat=pal.steel_light,
                       verts=12, bev=0.003, segments=2))

    # ── 底部三推进器 ──
    # 推进器：三个喇叭口朝下、内收到 R0*0.55，并且只露出很短一截。
    # 旧参数（0.085 长 + 外置）看起来像四条小短腿，破坏了"悬浮"的读感。
    for i in range(3):
        a = math.pi * 0.5 + i * 2.0 * math.pi / 3.0
        px, py = math.cos(a) * R0 * 0.55, math.sin(a) * R0 * 0.55
        o += R.nozzle("chassis_thruster_%d" % (i + 1), 0.070, 0.075,
                      (px, py, z - R0 * 0.46),
                      rot=(math.radians(180), 0, 0), mat=pal.joint,
                      inner=pal.core, verts=20)

    # ── 天线 + 侧向传感器 ──
    # 半径 0.009 的细杆在 _finish 里倒角会算成负数（bev 相对半径过大），
    # 整根杆被吞掉 —— 高度直接少 0.4m。加粗到 0.014、倒角 0.001。
    o.append(R.cyl("chassis_antenna", 0.014, 0.32, (0, R0 * 0.34, z + R0 * 0.64),
                   mat=pal.joint, verts=10, bev=0.001, segments=1))
    o.append(R.sphere("chassis_antennatip", 0.020,
                      (0, R0 * 0.34, z + R0 * 0.62 + 0.16),
                      mat=pal.core, segments=14, rings=10))
    for s, sx in (("L", -1), ("R", 1)):
        o.append(R.sphere("chassis_sensor_%s" % s, 0.038,
                          (sx * R0 * 0.80, R0 * 0.42, z + R0 * 0.22),
                          mat=pal.visor, segments=16, rings=12))

    # ⚠️ 第七十九轮：同园丁，包围盒改用躯干椭球的真实尺寸
    o += R.greeble("patrol_gb", (0, 0, z),
                   (R0, R0 * 1.04, R0 * 0.90), 14, 401,
                   pal.greeble_mats(), faces=('+X', '-X', '+Y'),
                   scale=(0.018, 0.050), depth=(0.006, 0.016))
    return o, "巡逻机", 1.30


# ═══════════════════════════════════════════════════════════
# 2. 运输机 —— 中型货运单位
# ═══════════════════════════════════════════════════════════

def hauler(pal):
    """四足货运机：横卧货舱筒 + 四道加强环 + 前伸驾驶舱。

    剪影特征：一个横躺的大圆筒。旧版是个方箱子，从任何角度看都是"纸箱"。
    """
    o = []
    W, D, H = 1.05, 1.50, 0.88
    # z=1.42（r223 验证：玩家/双足正常，C_7/C_9 仍超伸但属建模几何限制）
    # ⚠️ 第七十五轮：货舱筒原来半径 0.47、筒心在 z=1.42，筒底到 0.95 ——
    #    而髋在 0.7 左右，正面看整台机只剩一个大圆盘，腿和驾驶舱全被遮住
    #    （检阅视角里"中间那台是个球"就是它）。
    #    把筒身抬高并压扁，让驾驶舱、腿、吊臂都能露出来。
    z = 1.58
    Rr = 0.40                        # 货舱筒半径

    # ── 货舱：沿 Y 轴的胶囊（两端球面封头，不是平盖）──
    o.append(R.capsule("part_torso", Rr, D * 0.86, (0, 0, z),
                       rot=(math.radians(90), 0, 0), mat=pal.steel,
                       segments=32, rings=20))

    # 加强环：三道，压在筒身上（比"贴几块板"更像承压容器）
    for i in range(3):
        yy = -D * 0.30 + i * (D * 0.60 / 2.0)
        o.append(R.torus("chassis_rib_%d" % (i + 1), Rr * 1.02, 0.024,
                         (0, yy, z), rot=(math.radians(90), 0, 0),
                         mat=pal.steel_light, major_seg=36, minor_seg=8))

    # ── 前端驾驶舱：椭球 + 弧形风挡 ──
    cy = -D * 0.50 - 0.10
    o.append(R.ellipsoid("chassis_cabin", (0.50, 0.40, 0.40),
                         (0, cy, z + 0.06), mat=pal.steel_light,
                         segments=30, rings=20, cut_below=-0.45))
    # 风挡：压扁的椭球面（弧形镜面）。
    # 横置圆柱的端面在正前方会读成"两个白圆点"，像眼睛而不像玻璃。
    # 用 visor 而不是 core：风挡是玻璃，不该像灯泡一样发白光
    o.append(R.ellipsoid("part_core", (0.235, 0.070, 0.135),
                         (0, cy - 0.30, z + 0.14), mat=pal.visor,
                         segments=30, rings=18, cut_below=-0.15))
    o.append(R.torus("part_corering", 0.225, 0.016,
                     (0, cy - 0.30, z + 0.14),
                     rot=(math.radians(90), 0, 0), mat=pal.joint,
                     major_seg=34, minor_seg=8))
    # 驾驶舱顶棚：一道横置的弧壳，把风挡框住
    o.append(R.ellipsoid("chassis_visorhood", (0.34, 0.14, 0.10),
                         (0, cy - 0.22, z + 0.30), mat=pal.accent,
                         segments=26, rings=16, cut_below=-0.20))

    # ── 顶部吊架：两根纵梁 + 弧形吊臂 + 软管 ──
    for s, sx in (("L", -1), ("R", 1)):
        o.append(R.cyl("chassis_spine_%s" % s, 0.045, D * 0.72,
                       (sx * 0.30, 0.02, z + Rr * 0.86),
                       rot=(math.radians(90), 0, 0), mat=pal.steel_light,
                       verts=14, bev=0.004, segments=2))
    # 吊臂：从顶部斜向前，末端一个挂钩（tube 弯管 + 球）
    o.append(R.tube("chassis_crane",
                    [(0.0, D * 0.30, z + Rr * 0.80),
                     (0.0, D * 0.30, z + Rr * 1.35),
                     (0.0, -D * 0.02, z + Rr * 1.45),
                     (0.0, -D * 0.30, z + Rr * 1.30)],
                    0.032, pal.joint, res=10, bevel_res=3))
    o.append(R.sphere("chassis_hook", 0.055,
                      (0, -D * 0.30, z + Rr * 1.22),
                      mat=pal.copper, segments=16, rings=12))
    # 侧面液压软管（tube 的弯角是圆的，这是它相对"两根圆柱对接"的全部价值）
    o.append(R.tube("chassis_hose_a",
                    [(0.34, D * 0.16, z + Rr * 0.70),
                     (0.46, D * 0.10, z + Rr * 0.20),
                     (0.44, -D * 0.02, z - Rr * 0.40)],
                    0.022, pal.rubber, res=8, bevel_res=2))
    o.append(R.tube("chassis_hose_b",
                    [(-0.34, D * 0.16, z + Rr * 0.70),
                     (-0.46, D * 0.10, z + Rr * 0.20),
                     (-0.44, -D * 0.02, z - Rr * 0.40)],
                    0.022, pal.rubber, res=8, bevel_res=2))

    # ── 四条腿：圆柱大腿 + 球膝 + 圆柱小腿 + 圆角脚掌 ──
    # 屈膝站立：膝盖沿前后方向偏移（前腿膝后偏、后腿膝前偏），让大腿/小腿不共线，
    # 留出水平余量——否则腿完全伸直时 IK 无水平行程，满速行走必超伸（实测裁剪 32 次）。
    for s, sx in (("L", -1), ("R", 1)):
        for tag, dy in (("F", -D * 0.30), ("B", D * 0.30)):
            hx = sx * (Rr + 0.12)
            # ⚠️ 膝盖前后偏移必须与**腿的垂直落差**成比例，不能按机体宽度 D 来定。
            #    旧值 0.36·D（D≈2.9 → 1.04m）是腿垂直落差（≈0.55+0.5m）的近两倍，
            #    形成"大腿朝前 45°、小腿朝后 45°"的反折尖角：
            #    实机截图里四足腿呈明显折膝，UE 侧 th1=+44.5° / th2=-45.1°，夹角近 90°。
            #    改为落差的 0.18 倍：膝关节自然前屈，大腿不再过分斜撑。
            #    （0.30 时近景仍呈"O 型腿"：大腿明显外撇、小腿近乎垂直。）
            # 偏移量按"伸直腿高"算，与 hip_z 的实际压低无关，保持屈膝姿态稳定。
            _drop = (z - Rr * 0.55) - 0.075
            # ⚠️ 第七十八轮对照实验：0.18 → 0.26。
            #    0.18 时 slack（(L1+L2) − 髋踝落差）只有 8.7cm，而步态抬脚可达 22cm，
            #    落脚轨迹不稳 → C_7 六次运行 netSlip 均值 30（C_8/C_9 只有 8/11）。
            #    0.26 时 slack 提到 17.6cm，大腿前倾 29.5°（0.30 会明显 O 型腿）。
            knee_off = _drop * 0.26
            kneeY = dy + (knee_off if tag == "B" else -knee_off)
            # ⚠️ 髋部高度必须比"腿伸直时的长度"更低，腿才有真实的屈膝余量。
            #    只把圆柱倾倒是"视觉弯、骨骼直"：髋踝距离仍 = L1+L2，腿实际是直的，
            #    IK 一动脚就够不到地面（第七十一轮的"走路悬空"）。
            #    这里把髋部压低 8% 的腿高，让髋踝距离 < L1+L2，腿真正弯起来。
            _full = (z - Rr * 0.55) - 0.075
            hip_z = 0.075 + _full * 0.92
            # ⚠️ 第七十五轮：knee_z 原来是 `z - Rr*0.55 - 0.55`（写死 0.55 的偏移）。
            #    z/Rr 一变（比如把货舱抬高、筒径压小），这个值就不跟着走：
            #    实测 z=1.58 时 髋=1.257、膝=0.81、踝=0.075 → 大腿 0.447、小腿 0.735，
            #    膝盖严重偏向小腿端，渲染里就是"膝盖下面挂着一段细管、脚掌另起一头"。
            #    改成与巨像/园丁一致：取髋踝中点，两段骨长相等。
            knee_z = (hip_z + 0.075) * 0.5
            ankle_z = 0.075
            # 髋：球 + 环（高度必须与 hip_z 一致，否则圆柱两头接不上关节）
            o.append(R.sphere("leg_hip_%s%s" % (s, tag), 0.105,
                              (hx, dy, hip_z), mat=pal.joint,
                              segments=20, rings=14))
            # ⚠️ 第七十九轮：髋在 (±0.52, ±0.45)，到货舱轴线的水平距离 0.688，
            #    而货舱筒半径只有 0.40 —— 髋球完全在筒外，实测断开 15.3cm。
            #    补一段髋桥斜插进货舱筒体。
            o.append(R.cyl_between("leg_hipbridge_%s%s" % (s, tag),
                                   (hx, dy, hip_z),
                                   (sx * Rr * 0.35, dy * 0.45, z - Rr * 0.18),
                                   0.062, mat=pal.joint, verts=16,
                                   bev=0.006, segments=2))
            o.append(R.torus("leg_hipring_%s%s" % (s, tag), 0.108, 0.016,
                             (hx + sx * 0.055, dy, hip_z),
                             rot=(0, math.radians(90), 0), mat=pal.copper,
                             major_seg=24, minor_seg=8))
            # 大腿：髋中心 → 膝球中心，直接由两端点建（见 robotlib.cyl_between）
            _dv1 = math.sqrt((kneeY - dy) ** 2 + (hip_z - knee_z) ** 2)
            o.append(R.cyl_between("part_leg_%s%s" % (s, tag),
                                   (hx, dy, hip_z), (hx, kneeY, knee_z),
                                   0.088, mat=pal.steel, verts=22,
                                   bev=0.008, segments=3))
            # 膝
            o.append(R.sphere("leg_knee_%s%s" % (s, tag), 0.098,
                              (hx, kneeY, knee_z),
                              mat=pal.joint, segments=20, rings=14))
            # 小腿（膝→踝）：圆柱必须**真正斜向脚踝**，长度取膝踝三维距离。
            # ⚠️ 旧实现用竖直长度 abs(knee_z-ankle_z) 且不旋转，而膝(Y=kneeY)与
            #    踝(Y=dy) 在 Y 上错开 → 圆柱两端都接不上关节，视觉上膝盖处折出尖角。
            _dv = math.sqrt((kneeY - dy) ** 2 + (knee_z - ankle_z) ** 2)
            # 小腿：膝球中心 → 踝中心，直接由两端点建（见 robotlib.cyl_between）
            o.append(R.cyl_between("leg_shin_%s%s" % (s, tag),
                                   (hx, kneeY, knee_z), (hx, dy, ankle_z),
                                   0.072, mat=pal.steel_light, verts=20,
                                   bev=0.007, segments=3))
            # 脚：圆角块 + 半椭球趾
            o.append(R.rounded_box("part_foot_%s%s" % (s, tag),
                                   (0.26, 0.38, 0.15),
                                   (hx, dy - 0.04, 0.075),
                                   mat=pal.joint, radius=0.035, segments=4))
            o.append(R.ellipsoid("foot_toe_%s%s" % (s, tag),
                                 (0.115, 0.075, 0.070),
                                 (hx, dy - 0.21, 0.072),
                                 mat=pal.steel_light, segments=18, rings=12,
                                 cut_below=-0.40))
            # 液压缸：大腿外侧一根斜撑
            o += R.piston("leg_pist_%s%s" % (s, tag),
                          (hx + sx * 0.075, dy + 0.10, z - Rr * 0.62),
                          (hx + sx * 0.065, dy + 0.06, z - Rr * 0.62 - 0.34),
                          0.024, pal.steel_light, pal.copper)

    # ── 侧挂武器（part_arm_*）──
    for s, sx in (("L", -1), ("R", 1)):
        ax = sx * (Rr + 0.22)
        # ⚠️ 第七十九轮：武器挂在筒外 0.22m 处，与货舱之间没有连接件 ——
        #    实测整把侧挂武器（壳体+炮管+环+炮口）是一整块孤岛。
        #    补一根挂架横梁插进筒体。
        o.append(R.cyl_between("arm_mount_%s" % s,
                               (sx * Rr * 0.45, -D * 0.20, z + 0.02),
                               (ax, -D * 0.20, z + 0.02),
                               0.045, mat=pal.joint, verts=16,
                               bev=0.005, segments=2))
        o.append(R.ellipsoid("part_arm_%s" % s, (0.13, 0.26, 0.15),
                             (ax, -D * 0.20, z + 0.02),
                             mat=pal.steel_light, segments=22, rings=14,
                             cut_below=-0.30))
        o.append(R.cyl("arm_barrel_%s" % s, 0.042, 0.30,
                       (ax, -D * 0.20 - 0.30, z + 0.02),
                       rot=(math.radians(90), 0, 0), mat=pal.joint,
                       verts=16, bev=0.004, segments=2))
        o.append(R.torus("arm_ring_%s" % s, 0.048, 0.012,
                         (ax, -D * 0.20 - 0.16, z + 0.02),
                         rot=(math.radians(90), 0, 0), mat=pal.copper,
                         major_seg=20, minor_seg=8))
        o.append(R.nozzle("arm_brake_%s" % s, 0.055, 0.06,
                          (ax, -D * 0.20 - 0.46, z + 0.02),
                          rot=(math.radians(-90), 0, 0),
                          mat=pal.steel_light, inner=pal.core, verts=18))

    # ⚠️ 第七十九轮：同园丁，包围盒改用货舱筒的真实尺寸
    o += R.greeble("hauler_gb", (0, 0, z), (Rr * 2.0, D * 0.86, Rr * 2.0), 24, 402,
                   pal.greeble_mats(), faces=('+X', '-X', '+Y'),
                   scale=(0.03, 0.09), depth=(0.010, 0.030))
    return o, "运输机", 3.10


# ═══════════════════════════════════════════════════════════
# 3. 维修巨像 —— 大型具名敌人
# ═══════════════════════════════════════════════════════════

def colossus(pal):
    """维修巨像：穹顶胸腔 + 三层反应堆 + 双巨臂。

    剪影特征：胸是一个大穹顶（不是方箱），两条维修臂垂到膝盖以下，
    末端是锥形焊枪 —— 远看像一台会走的工程车。
    """
    o = []
    W, D, H = 2.40, 2.90, 2.20
    # z=3.55（r223 验证：玩家/双足正常）
    z = 3.55

    # ── 胸腔：大椭球，下部切平接腰 ──
    o.append(R.ellipsoid("part_torso", (W * 0.44, D * 0.42, H * 0.54),
                         (0, 0, z), mat=pal.steel, segments=36, rings=24,
                         cut_below=-0.52))
    # 胸甲：小一圈的弧壳，前面压出"护心镜"的层次
    o.append(R.ellipsoid("chassis_chest", (W * 0.35, D * 0.36, H * 0.44),
                         (0, -D * 0.10, z + H * 0.06),
                         mat=pal.steel_light, segments=32, rings=22,
                         cut_below=-0.30))
    # 腰部：收窄的环（连接胸腔与骨盆，避免两球直接对撞）
    # ⚠️ 第七十五轮：环半径原来 W*0.30=0.72，比骨盆和胸腔都宽，
    #    远看腰间横着一个"大盘子"。收到 0.16，只做过渡。
    # ⚠️ 第七十九轮：**补一根实心腰柱**。原来只有这个环，而环悬在
    #    胸腔切面（z−H·0.54·0.52）与骨盆顶之间，两头都没碰上 ——
    #    实测躯干与骨盆之间断开 60.5cm，游戏里躯干整个浮在腿上。
    #    腰柱从胸腔切面内一直伸到骨盆中心。
    _torsoBottom = z - H * 0.54 * 0.52
    _pelvisZ = z - H * 0.58

    o.append(R.torus("chassis_waist", W * 0.16, 0.055, (0, 0, z - H * 0.52),
                     mat=pal.joint, major_seg=36, minor_seg=10))
    o.append(R.ellipsoid("chassis_pelvis", (W * 0.28, D * 0.26, H * 0.16),
                         (0, 0, _pelvisZ), mat=pal.steel,
                         segments=28, rings=18, cut_below=-0.40))
    # 腰柱：连接胸腔与骨盆（实心，两端都插进相邻部件里）
    o.append(R.cyl_between("chassis_spine",
                           (0, 0, _torsoBottom + 0.30),
                           (0, 0, _pelvisZ - 0.02),
                           W * 0.17, mat=pal.joint, verts=28,
                           bev=0.02, segments=3))

    # ── 反应堆：球心 + 三层同心环 + 八片散热鳍 ──
    # 反应堆缩到 0.24 —— 0.30 的球 + 0.54 的外环几乎占满整个胸口，
    # 巨型机体的胸口应该是"装甲 + 一块核心"，不是"一颗大眼球"。
    cz = z + H * 0.18
    cy = -D * 0.40
    o.append(R.sphere("part_core", 0.235, (0, cy, cz),
                      mat=pal.core, segments=30, rings=20))
    for i, (rr, mm) in enumerate(((0.270, pal.joint), (0.350, pal.copper),
                                  (0.430, pal.steel_light))):
        o.append(R.torus("part_corering_%d" % (i + 1), rr, 0.026 - i * 0.004,
                         (0, cy + 0.02 * i, cz),
                         rot=(math.radians(90), 0, 0), mat=mm,
                         major_seg=38, minor_seg=10))
    for i in range(6):
        a = i * math.pi / 3.0
        o.append(R.prism("core_fin_%d" % (i + 1), (0.045, 0.16, 0.20),
                         (math.cos(a) * 0.50, cy + 0.05,
                          cz + math.sin(a) * 0.50),
                         rot=(0, math.radians(-90) + a, 0),
                         mat=pal.accent, bev=0.007, segments=3))

    # ── 头部：圆顶 + 观察缝 + 两根排气烟囱 ──
    # 头缩到 0.30 —— 头部相对躯干越大，机体读起来就越"玩具"。
    # 7.6m 的工程机，头应该只是躯干上的一小块传感器罩。
    hz = z + H * 0.50
    o.append(R.ellipsoid("chassis_head", (0.30, 0.32, 0.26),
                         (0, -0.10, hz + 0.14), mat=pal.steel,
                         segments=28, rings=18, cut_below=-0.55))
    o.append(R.ellipsoid("head_visor", (0.21, 0.075, 0.065),
                         (0, -0.36, hz + 0.17), mat=pal.visor,
                         segments=24, rings=14, cut_below=-0.30))
    for s, sx in (("L", -1), ("R", 1)):
        # ⚠️ 第七十九轮：触角起点原来在 (sx*0.42, 0.34, hz-0.10)，
        #    而躯干表面在那一侧不够高 —— 实测与躯干断开 4.2cm。
        #    把起点往躯干内部下沉，确保插进去。
        o.append(R.tube("chassis_stack_%s" % s,
                        [(sx * 0.36, 0.30, hz - 0.28),
                         (sx * 0.50, 0.44, hz + 0.45),
                         (sx * 0.50, 0.40, hz + 0.95)],
                        0.082, pal.joint, res=8, bevel_res=3))
        o.append(R.torus("chassis_stackcap_%s" % s, 0.088, 0.020,
                         (sx * 0.50, 0.40, hz + 0.96), mat=pal.copper,
                         major_seg=22, minor_seg=8))

    # ── 双巨臂：球肩 + 圆柱上臂 + 球肘 + 圆柱前臂 + 锥形焊枪 ──
    for s, sx in (("L", -1), ("R", 1)):
        shx = sx * (W * 0.44 + 0.62)
        shz = z + H * 0.24
        # ⚠️ 第七十九轮：肩球在躯干外侧 62cm 处，而躯干 X 半径只有 1.056m ——
        #    两者之间**没有任何连接件**，实测躯干与肩断开 39.3cm，
        #    游戏里整条手臂悬在机体旁边。
        #    补一段肩桥：从躯干内部一直插到肩球中心。
        o.append(R.cyl_between("shoulder_bridge_%s" % s,
                               (sx * W * 0.30, 0, shz),
                               (shx, 0, shz),
                               W * 0.105, mat=pal.steel_light, verts=24,
                               bev=0.015, segments=3))
        # 肩：球窝 + 双环（大件用双环显得更重）
        o.append(R.sphere("shoulder_%s" % s, 0.30, (shx, 0, shz),
                          mat=pal.joint, segments=24, rings=16))
        for i, off in enumerate((0.10, 0.22)):
            o.append(R.torus("shoulder_ring_%s_%d" % (s, i + 1), 0.30, 0.020,
                             (shx + sx * off, 0, shz),
                             rot=(0, math.radians(90), 0), mat=pal.copper,
                             major_seg=28, minor_seg=8))
        # 上臂
        o.append(R.cyl("part_arm_%s" % s, 0.275, 1.32,
                       (shx + sx * 0.04, 0, shz - 0.76),
                       mat=pal.steel, verts=26, bev=0.016, segments=3))
        # 肘
        ez = shz - 1.50
        o.append(R.sphere("arm_elbow_%s" % s, 0.235,
                          (shx + sx * 0.04, 0, ez), mat=pal.joint,
                          segments=24, rings=16))
        o.append(R.torus("arm_elbowring_%s" % s, 0.235, 0.022,
                         (shx + sx * 0.16, 0, ez),
                         rot=(0, math.radians(90), 0), mat=pal.copper,
                         major_seg=28, minor_seg=8))
        # 前臂（略细，末端是焊枪）
        o.append(R.cyl("arm_fore_%s" % s, 0.185, 1.10,
                       (shx + sx * 0.04, -0.04, ez - 0.62),
                       mat=pal.steel_light, verts=24, bev=0.013, segments=3))
        # ⚠️ 第七十五轮：原来前臂下来直接就是一个喇叭口喷嘴，游戏里读作
        #    "手臂末端接了个扁圆盘"，不像工具。补一个枪身（握把段）+ 护套环，
        #    让"前臂 → 枪身 → 喷嘴"三段读得出来。
        _gun_z = ez - 1.10
        o.append(R.sphere("arm_wrist_%s" % s, 0.175,
                          (shx + sx * 0.04, -0.04, _gun_z),
                          mat=pal.joint, segments=22, rings=14))
        o.append(R.cyl("arm_grip_%s" % s, 0.130, 0.30,
                       (shx + sx * 0.04, -0.04, _gun_z - 0.17),
                       mat=pal.steel, verts=22, bev=0.010, segments=3))
        o.append(R.torus("arm_gripr_%s" % s, 0.135, 0.018,
                         (shx + sx * 0.04, -0.04, _gun_z - 0.30),
                         mat=pal.copper, major_seg=26, minor_seg=8))
        o.append(R.nozzle("arm_tool_%s" % s, 0.145, 0.28,
                          (shx + sx * 0.04, -0.04, _gun_z - 0.50),
                          rot=(math.radians(180), 0, 0),
                          mat=pal.joint, inner=pal.core, verts=22))
        # 液压缸：肩 → 前臂，两根
        for i, dy in enumerate((-0.20, 0.20)):
            o += R.piston("arm_pist_%s_%d" % (s, i + 1),
                          (shx + sx * 0.20, dy, shz - 0.30),
                          (shx + sx * 0.16, dy, ez - 0.30),
                          0.042, pal.steel_light, pal.copper)

    # ── 四条支撑腿：粗圆柱 + 球膝 + 大脚掌 ──
    # 屈膝站立：膝前/后偏，让大腿/小腿不共线，留出水平余量。
    #
    # ⚠️ 以下三处几何在第六十九轮之前是"按感觉"定的，导致两个可见缺陷，
    #    统一改成与**腿的垂直落差**成比例（与运输机同一套规则）：
    #    1. 膝盖偏移固定 0.55m → 改为落差的 0.18 倍；
    #    2. knee_z 固定 0.92 → 改为髋踝中点，让大腿/小腿接近等长
    #       （旧值让大腿 |V1|=142cm、小腿 |V2|=68cm，比例 2:1）；
    #    3. 圆柱按竖直长度建且不旋转 → 长度取三维距离并按倾角旋转，
    #       否则圆柱两端接不上关节，膝盖处折出尖角。
    for s, sx in (("L", -1), ("R", 1)):
        for j, dy in enumerate((-0.78, 0.78)):
            lx = sx * (W * 0.38)
            # ⚠️ 与运输机同理：髋部压低 8%，让髋踝距离 < L1+L2，腿真正屈膝。
            #    ankle_z 必须等于脚块**中心高度**（脚块高 0.42 → 中心 0.21），
            #    否则小腿插进脚里或脚悬空。
            ankle_z = 0.21
            _full = (z - H * 0.60) - ankle_z
            # 髋部压低 8%：让髋踝距离 < L1+L2，腿真正屈膝（见第七十一轮）。
            # ⚠️ 不要为了"更多余量"继续压 —— 压低 hip_z 等于腿变短，
            #    脚会离地；抬脚高度与余量的匹配由程序侧限制（见 DbgLeg）。
            hip_z = ankle_z + _full * 0.92
            _drop = (z - H * 0.60) - ankle_z
            knee_off = _drop * 0.18
            # 前腿(j=0)膝向后偏、后腿(j=1)膝向前偏
            kneeY = dy + (knee_off if j == 1 else -knee_off)
            # 膝高取髋踝中点：两段骨长接近，IK 反解不会因单段过长而钳位
            knee_z = (hip_z + ankle_z) * 0.5
            o.append(R.sphere("leg_hip_%s%d" % (s, j + 1), 0.325,
                              (lx, dy, hip_z), mat=pal.joint,
                              segments=22, rings=16))
            # ⚠️ 第七十九轮：髋球在 (±0.91, ±0.78) 处，而骨盆椭球在该位置的
            #    实际半径远小于名义值 —— 实测髋与骨盆断开 20.5cm，
            #    游戏里四条腿吊在骨盆下方够不着。补一段髋桥横向插进骨盆。
            o.append(R.cyl_between("leg_hipbridge_%s%d" % (s, j + 1),
                                   (lx, dy, hip_z),
                                   (sx * W * 0.10, dy * 0.55, hip_z + 0.02),
                                   0.135, mat=pal.joint, verts=20,
                                   bev=0.01, segments=2))
            _dv1 = math.sqrt((kneeY - dy) ** 2 + (hip_z - knee_z) ** 2)
            o.append(R.cyl_between("part_leg_%s%d" % (s, j + 1),
                                   (lx, dy, hip_z), (lx, kneeY, knee_z),
                                   0.305, mat=pal.steel,
                                   verts=26, bev=0.018, segments=3))
            o.append(R.sphere("leg_knee_%s%d" % (s, j + 1), 0.315,
                              (lx, kneeY, knee_z), mat=pal.joint,
                              segments=22, rings=16))
            o.append(R.torus("leg_kneering_%s%d" % (s, j + 1), 0.315, 0.024,
                             (lx, kneeY, knee_z),
                             rot=(0, math.radians(90), 0), mat=pal.copper,
                             major_seg=26, minor_seg=8))
            _dv2 = math.sqrt((kneeY - dy) ** 2 + (knee_z - ankle_z) ** 2)
            # 小腿：膝球中心 → 踝中心，直接由两端点建（见 robotlib.cyl_between）
            o.append(R.cyl_between("leg_shin_%s%d" % (s, j + 1),
                                   (lx, kneeY, knee_z), (lx, dy, ankle_z),
                                   0.235, mat=pal.steel_light, verts=22,
                                   bev=0.014, segments=3))
            # 脚：圆角 + 半椭球趾（大件也要圆，否则像砖头）
            # ⚠️ 第七十五轮：脚块原来整体前移 0.16（中心在 dy-0.16），
            #    踝却落在 dy —— 腿的轴线与脚的承重点错开 16cm，
            #    远看就是"腿没插在脚上"。改为脚块中心对齐踝，前伸交给足趾。
            o.append(R.rounded_box("part_foot_%s%d" % (s, j + 1),
                                   (0.86, 1.24, 0.42),
                                   (lx, dy, 0.21),
                                   mat=pal.joint, radius=0.090, segments=5))
            o.append(R.ellipsoid("foot_toe_%s%d" % (s, j + 1),
                                 (0.38, 0.26, 0.19),
                                 (lx, dy - 0.60, 0.19), mat=pal.steel_light,
                                 segments=22, rings=14, cut_below=-0.45))

    # ⚠️ 第七十九轮：greeble 原来用 (W, D, H) = (2.40, 2.90, 2.20) 当包围盒，
    #    而躯干椭球只有 (W*0.44, D*0.42, H*0.54) ≈ (1.06, 1.22, 1.19) ——
    #    包围盒比实体大一倍多，小零件全贴在**空中**，实测 36 个孤立块。
    #    改用躯干椭球的真实尺寸。
    o += R.greeble("colossus_gb", (0, 0, z),
                   (W * 0.44, D * 0.42, H * 0.54), 50, 403,
                   pal.greeble_mats(), scale=(0.05, 0.16),
                   depth=(0.018, 0.055), faces=('+X', '-X', '+Y'))
    return o, "维修巨像", 7.60


# ═══════════════════════════════════════════════════════════
# 4. 园丁机 —— 具名，可招募
# ═══════════════════════════════════════════════════════════

def gardener(pal):
    """园丁机：细长人形 + 弧面围裙 + 圆顶帽。

    剪影特征：一条从胸口垂到膝上的围裙，配一顶圆帽 —— 唯一"拟人"的敌人。
    """
    o = []
    W, D, H = 0.60, 0.44, 0.72
    z = 1.76

    # ── 躯干：竖椭球（细长，别做成桶）──
    o.append(R.ellipsoid("part_torso", (W * 0.50, D * 0.52, H * 0.52),
                         (0, 0, z), mat=pal.steel, segments=30, rings=20,
                         cut_below=-0.42))
    # 围裙：向前下垂的弧面壳（cut_below 让它上宽下窄）
    o.append(R.ellipsoid("chassis_apron",
                         (W * 0.44, D * 0.20, H * 0.52),
                         (0, -D * 0.42, z - H * 0.18),
                         mat=pal.accent, segments=28, rings=20,
                         cut_below=-0.62))
    # 围裙下摆的一圈包边（torus 压扁 → 看起来像布边）
    o.append(R.torus("chassis_apronhem", W * 0.30, 0.016,
                     (0, -D * 0.40, z - H * 0.66), mat=pal.steel_light,
                     major_seg=30, minor_seg=8))

    # ── 核心：胸口小反应堆 ──
    cz = z + H * 0.16
    o.append(R.sphere("part_core", 0.072, (0, -D * 0.52, cz),
                      mat=pal.core, segments=22, rings=16))
    o.append(R.torus("part_corering", 0.088, 0.014, (0, -D * 0.50, cz),
                     rot=(math.radians(90), 0, 0), mat=pal.joint,
                     major_seg=26, minor_seg=8))

    # ── 颈 + 头：球颈 + 圆顶颅骨 + 宽帽檐 ──
    # ⚠️ 第七十五轮：头部原来用 cut_below=-0.40，把颅骨底部切平抬高了 6cm，
    #    而颈球半径只有 0.070 → 头**悬在脖子上方 8cm**，游戏里看就是"头浮空"。
    #    头部不需要切面（它下面是脖子，不是要接平面），改为完整椭球并下沉贴住颈球。
    nz = z + H * 0.50
    o.append(R.sphere("chassis_neck", 0.070, (0, 0, nz), mat=pal.joint,
                      segments=18, rings=12))
    hz = nz + 0.145
    o.append(R.ellipsoid("chassis_head", (0.155, 0.165, 0.150),
                         (0, -0.02, hz), mat=pal.steel,
                         segments=26, rings=18))
    # 帽檐：大而扁的圆盘（园丁的标志）
    o.append(R.cyl("head_brim", 0.215, 0.028, (0, -0.02, hz + 0.10),
                   mat=pal.accent, verts=32, bev=0.008, segments=3))
    # 帽顶：小穹顶
    o.append(R.ellipsoid("head_crown", (0.115, 0.120, 0.095),
                         (0, -0.02, hz + 0.13), mat=pal.accent,
                         segments=24, rings=16, cut_below=0.0))
    # 观察缝
    o.append(R.ellipsoid("head_visor", (0.115, 0.035, 0.030),
                         (0, -0.165, hz + 0.02), mat=pal.visor,
                         segments=20, rings=12, cut_below=-0.20))

    # ── 肩 + 双臂 ──
    for s, sx in (("L", -1), ("R", 1)):
        shx = sx * (W * 0.50 + 0.045)
        shz = z + H * 0.34
        # ⚠️ 第七十九轮：肩球贴着椭球表面，但椭球在该高度已经收窄，
        #    实测整条手臂（肩→肘→前臂→工具）与躯干断开成一整块孤岛。
        #    补一段肩桥插进躯干。
        o.append(R.cyl_between("shoulder_bridge_%s" % s,
                               (sx * W * 0.18, 0, shz),
                               (shx, 0, shz),
                               W * 0.055, mat=pal.steel_light, verts=16,
                               bev=0.005, segments=2))
        # 肩：小球 + 环（园丁是轻型机，肩甲不做穹顶）
        o.append(R.sphere("shoulder_%s" % s, 0.085, (shx, 0, shz),
                          mat=pal.joint, segments=18, rings=14))
        o.append(R.torus("shoulder_ring_%s" % s, 0.085, 0.013,
                         (shx + sx * 0.045, 0, shz),
                         rot=(0, math.radians(90), 0), mat=pal.copper,
                         major_seg=22, minor_seg=8))
        # 上臂
        o.append(R.cyl("part_arm_%s" % s, 0.062, 0.30,
                       (shx + sx * 0.02, -0.02, shz - 0.20),
                       mat=pal.steel, verts=18, bev=0.006, segments=2))
        # 肘
        ez = shz - 0.40
        o.append(R.sphere("arm_elbow_%s" % s, 0.068,
                          (shx + sx * 0.02, -0.02, ez), mat=pal.joint,
                          segments=18, rings=12))
        # 前臂
        # ⚠️ 第七十五轮：前臂原来固定长 0.30、止于 ez-0.35，而"手"（水壶/修枝剪）
        #    在 x=±0.46、z=z-H*0.50 —— 两者横向差 9cm、纵向差十几厘米，中间没有腕关节，
        #    游戏里看就是"手悬在胳膊外侧"。
        #    改为：前臂下端接到手的高度，并补一个腕球把两者连起来。
        _hand_z = z - H * 0.50
        _fore_bottom = _hand_z + 0.04
        _fore_len = max(ez - _fore_bottom, 0.10)
        _hand_x = sx * 0.46
        _fore_x = shx + sx * 0.02
        o.append(R.cyl("arm_fore_%s" % s, 0.054, _fore_len,
                       ((_fore_x + _hand_x) * 0.5, -0.05,
                        ez - _fore_len * 0.5),
                       rot=(0, math.atan2(_hand_x - _fore_x, _fore_len), 0),
                       mat=pal.steel_light, verts=18, bev=0.006, segments=2))
        # 腕关节
        o.append(R.sphere("arm_wrist_%s" % s, 0.046,
                          (_hand_x, -0.11, _fore_bottom + 0.02),
                          mat=pal.joint, segments=16, rings=10))

    # 左手：浇水壶（圆筒 + 弯管壶嘴）
    # ⚠️ 第七十五轮：壶嘴起点原来在 z-H*0.58，比壶底（壶中心 z-H*0.50、半长 0.10）还低，
    #    看起来是从壶底戳出来的一根悬空弯钩。改为从壶口侧壁伸出。
    _can_z = z - H * 0.50
    o.append(R.cyl("arm_can_L", 0.105, 0.20, (-0.46, -0.14, _can_z),
                   rot=(math.radians(74), 0, 0), mat=pal.copper,
                   verts=22, bev=0.008, segments=3))
    o.append(R.torus("arm_canring_L", 0.108, 0.014,
                     (-0.46, -0.14, _can_z + 0.06),
                     rot=(math.radians(74), 0, 0), mat=pal.steel_light,
                     major_seg=24, minor_seg=8))
    o.append(R.tube("arm_spout_L",
                    [(-0.46, -0.20, _can_z + 0.02),
                     (-0.50, -0.34, _can_z + 0.06),
                     (-0.52, -0.44, _can_z + 0.14)],
                    0.022, pal.steel_light, res=8, bevel_res=3))

    # 右手：修枝剪（两根刀片 + 中心轴）
    for i, sx2 in enumerate((-1, 1)):
        o.append(R.prism("arm_blade_R%d" % (i + 1), (0.030, 0.075, 0.30),
                         (0.46 + sx2 * 0.032, -0.16, z - H * 0.52),
                         rot=(math.radians(-24), 0, math.radians(sx2 * 5)),
                         top=(1.0, 0.45), mat=pal.steel_light,
                         bev=0.004, segments=2))
    o.append(R.sphere("arm_pivot_R", 0.036, (0.46, -0.13, z - H * 0.38),
                      mat=pal.copper, segments=16, rings=12))

    # ── 细腿 ──
    # ⚠️ 第七十一轮：统一改成与 hauler/colossus 同一套几何规则。
    #    旧实现：圆柱长度/中心是手填的（0.56 / 0.48，中心 hz2-0.34 / hz2-0.96），
    #    与关节位置对不上（圆柱两端各留 6cm 空隙），而且髋部高度使腿几乎完全伸直
    #    （髋踝 111.3cm ≈ L1+L2），IK 一动脚就够不到地面 → "走路悬空"。
    for s, sx in (("L", -1), ("R", 1)):
        lx = sx * 0.145
        _top = z - H * 0.52          # 腿伸直时的髋高
        _ank = 0.055                 # 踝高（脚块中心）
        _full = _top - _ank
        hip_z = _ank + _full * 0.92  # 压低 8%，留出真实屈膝余量
        # ⚠️ 第七十八轮：0.10 时 slack 只有 2.9cm，腿几乎伸直，IK 在近奇异点抖动。
        #    提到 0.22，slack 升到 13.3cm，大腿前倾 25.6°（仍自然）。
        #    注意：真正上场的是 SK_Enemy_Gardener（C_8），不是 Weather。
        knee_off = _full * 0.22
        knee_z = (hip_z + _ank) * 0.5
        kneeY = -knee_off            # 膝盖朝前（-Y）
        o.append(R.sphere("leg_hip_%s" % s, 0.078, (lx, 0, hip_z),
                          mat=pal.joint, segments=18, rings=12))
        # ⚠️ 第七十九轮：躯干是 cut_below=-0.42 的椭球，底部被切平抬到
        #    z−0.42·(H·0.52) 处；而髋球顶还差 24cm 才碰到它 ——
        #    实测髋与躯干断开 31.4cm，游戏里两条腿吊在躯干下方。
        #    补一段髋柱，从髋球一直插进躯干实体里。
        #    ⚠️ 上端必须**高于**躯干切面（z − 0.42·H·0.52 ≈ 1.603），
        #       原来用 z − H*0.30 = 1.544，落在切面下方，仍然没接上。
        o.append(R.cyl_between("leg_hippost_%s" % s,
                               (lx, 0, hip_z),
                               (lx, 0, z - H * 0.14),
                               0.052, mat=pal.joint, verts=16,
                               bev=0.005, segments=2))
        _dv1 = math.sqrt(knee_off ** 2 + (hip_z - knee_z) ** 2)
        o.append(R.cyl_between("part_leg_%s" % s, (lx, 0.0, hip_z),
                               (lx, kneeY, knee_z), 0.062,
                               mat=pal.steel, verts=18, bev=0.006,
                               segments=2))
        o.append(R.sphere("leg_knee_%s" % s, 0.070, (lx, kneeY, knee_z),
                          mat=pal.joint, segments=18, rings=12))
        _dv2 = math.sqrt(knee_off ** 2 + (knee_z - _ank) ** 2)
        # 小腿：膝球中心 → 踝中心，直接由两端点建（见 robotlib.cyl_between）
        o.append(R.cyl_between("leg_shin_%s" % s, (lx, kneeY, knee_z),
                               (lx, 0.0, _ank), 0.062,
                               mat=pal.steel_light, verts=18, bev=0.005,
                               segments=2))
        o.append(R.rounded_box("part_foot_%s" % s, (0.17, 0.30, 0.11),
                               (lx, -0.05, _ank), mat=pal.joint,
                               radius=0.028, segments=4))

    # ── 背后工具架：三根细管 + 环扣 ──
    for i in range(3):
        o.append(R.cyl("chassis_tool_%d" % (i + 1), 0.014, 0.42,
                       (-0.11 + i * 0.11, D * 0.62, z + 0.06),
                       rot=(math.radians(8), 0, 0), mat=pal.steel_light,
                       verts=10, bev=0.002, segments=1))
    o.append(R.cyl("chassis_rack", 0.020, 0.36, (0, D * 0.60, z - 0.12),
                   rot=(0, math.radians(90), 0), mat=pal.joint,
                   verts=12, bev=0.003, segments=1))

    # ⚠️ 第七十九轮：greeble 的包围盒必须用**实体的真实尺寸**，不能用 W/D/H。
    #    旧值 (W, D, H) 是椭球的 2 倍大，小零件全贴在空气里（实测大量孤立块）。
    o += R.greeble("gardener_gb", (0, 0, z),
                   (W * 0.50, D * 0.52, H * 0.52), 16, 404,
                   pal.greeble_mats(), faces=('+X', '-X', '+Z'),
                   scale=(0.015, 0.042), depth=(0.005, 0.014))
    return o, "园丁机", 2.60


# ═══════════════════════════════════════════════════════════
# 5. 气象机 —— 具名同伴
# ═══════════════════════════════════════════════════════════

def weather(pal):
    """气象机：半球雷达罩 + 风速计 + 天线阵列。

    剪影特征：头顶一个比头还大的半球罩。旧版是一块扁平圆盘，
    从正面几乎看不见 —— 换成半球之后轮廓一眼可辨。
    """
    o = []
    W, D, H = 0.68, 0.52, 0.72
    z = 1.68

    # ── 躯干：椭球 + 侧面散热格栅 ──
    o.append(R.ellipsoid("part_torso", (W * 0.50, D * 0.54, H * 0.52),
                         (0, 0, z), mat=pal.steel, segments=30, rings=20,
                         cut_below=-0.40))
    o.append(R.ellipsoid("chassis_backpack", (W * 0.34, D * 0.20, H * 0.34),
                         (0, D * 0.50, z + 0.02), mat=pal.steel_light,
                         segments=26, rings=18, cut_below=-0.35))
    for i in range(4):
        o.append(R.torus("chassis_louver_%d" % (i + 1), W * 0.28, 0.010,
                         (0, D * 0.56, z - 0.14 + i * 0.085),
                         rot=(math.radians(90), 0, 0), mat=pal.joint,
                         major_seg=26, minor_seg=6))

    # ── 核心 ──
    cz = z + H * 0.14
    o.append(R.sphere("part_core", 0.078, (0, -D * 0.52, cz),
                      mat=pal.core, segments=22, rings=16))
    o.append(R.torus("part_corering", 0.094, 0.014, (0, -D * 0.50, cz),
                     rot=(math.radians(90), 0, 0), mat=pal.joint,
                     major_seg=26, minor_seg=8))

    # ── 颈 + 头 ──
    # ⚠️ 同园丁：头部不能 cut_below，否则颅骨底面被切掉、悬在颈球上方（"头浮空"）。
    nz = z + H * 0.50
    o.append(R.sphere("chassis_neck", 0.072, (0, 0, nz), mat=pal.joint,
                      segments=18, rings=12))
    hz = nz + 0.152
    o.append(R.ellipsoid("chassis_head", (0.170, 0.180, 0.160),
                         (0, -0.01, hz), mat=pal.steel,
                         segments=28, rings=18))
    o.append(R.ellipsoid("head_visor", (0.125, 0.038, 0.032),
                         (0, -0.180, hz + 0.01), mat=pal.visor,
                         segments=20, rings=12, cut_below=-0.20))

    # ── 雷达罩：碟形天线 + 馈源 + 支杆 ──
    # 罩子加大到 0.52 半径、抬高到头顶上方 ——
    # 深碗（z 半径 0.42）而不是扁盘：扁盘从正面看只剩一条线，
    # 碗才有"碟形天线"的侧壁，也才能接住方向光形成明暗。
    #
    # ⚠️ 第七十五轮：倾角原来是 -38°，把**封口面（碟底）转向了观众**，
    #    游戏里看到的是一块暗色大圆盘，像"头上扣了个黑洞"。
    #    改为 +20°：碟口朝前上方，观众看到的是内凹面 + 边沿一圈亮边，
    #    这才是"雷达罩"的读法。
    dz = hz + 0.30
    _tilt = math.radians(20)
    # ⚠️ 第七十五轮：方位试错记录 —— 关键是**罩子不能盖住头**。
    #    · 负倾角（-38°）→ 封口面转向观众（"头上扣了个黑洞"）
    #    · 正倾角 + cut_below → 切面朝前下，正面一片暗色内壁（"打开的空壳"）
    #    · 任何 cut 都会在正面露出一块明暗突变的平面 → 改为完整穹顶
    #    · 半径 0.34 仍把头整个遮住 → 缩到 0.24，并抬到头顶更高处，
    #      让"头（带面罩）+ 上方的雷达罩"两段都读得出来。
    #
    # ⚠️ 第七十五轮（修正）：设计意图是"头顶一个比头还大的半球罩"（见函数 docstring），
    #    所以罩子大本身不是缺陷。真正的缺陷是**罩子压在头上、两者重叠成一个大球**。
    #    这里保留设计意图（比头大），但把罩子抬到头顶上方，让头和罩子分开。
    dz = hz + 0.46
    _tilt = math.radians(14)
    o.append(R.ellipsoid("head_dish", (0.30, 0.30, 0.30), (0, 0.06, dz),
                         rot=(_tilt, 0, 0), mat=pal.steel_light,
                         segments=32, rings=22))
    o.append(R.torus("head_dishrim", 0.292, 0.016,
                     (0, 0.06, dz - 0.30 * math.sin(_tilt)),
                     rot=(_tilt, 0, 0), mat=pal.copper,
                     major_seg=32, minor_seg=8))
    # 罩子与头之间的支杆，避免"球浮在头顶上"
    o.append(R.cyl("head_dishpost", 0.026, 0.26, (0, 0.03, hz + 0.23),
                   mat=pal.joint, verts=12, bev=0.004, segments=2))
    # 碗背面的加强筋（三根），否则背面是一片空白
    for i in range(3):
        a = i * 2.0 * math.pi / 3.0
        o.append(R.prism("head_dishrib_%d" % (i + 1), (0.030, 0.28, 0.022),
                         (math.cos(a) * 0.20, 0.04 + math.sin(a) * 0.20,
                          dz + 0.12),
                         rot=(math.radians(-38), 0, a), mat=pal.joint,
                         bev=0.004, segments=2))
    # 馈源：罩心正前方
    o.append(R.sphere("head_feed", 0.034, (0, 0.06 - 0.12, dz + 0.05),
                      mat=pal.copper, segments=16, rings=12))
    for i in range(3):
        a = i * 2.0 * math.pi / 3.0
        o.append(R.cyl("head_strut_%d" % (i + 1), 0.005, 0.14,
                       (math.cos(a) * 0.055, 0.06 - 0.06 + math.sin(a) * 0.012,
                        dz + 0.025 + math.sin(a) * 0.055),
                       rot=(math.radians(70), 0, a), mat=pal.joint,
                       verts=8, bev=0.002, segments=1))

    # ── 两侧风速计：立杆 + 三杯 ──
    for s, sx in (("L", -1), ("R", 1)):
        mx = sx * (W * 0.50 + 0.10)
        o.append(R.cyl("arm_mast_%s" % s, 0.014, 0.36, (mx, 0.02, z + 0.28),
                       mat=pal.joint, verts=10, bev=0.002, segments=1))
        o.append(R.sphere("arm_hub_%s" % s, 0.028, (mx, 0.02, z + 0.47),
                          mat=pal.copper, segments=14, rings=10))
        for i in range(3):
            a = i * 2.0 * math.pi / 3.0
            o.append(R.ellipsoid("arm_cup_%s%d" % (s, i + 1),
                                 (0.042, 0.042, 0.020),
                                 (mx + math.cos(a) * 0.095,
                                  0.02 + math.sin(a) * 0.095, z + 0.47),
                                 mat=pal.accent, segments=16, rings=10,
                                 cut_below=-0.10))

    # ── 侧天线（细长 + 球端）──
    for s, sx in (("L", -1), ("R", 1)):
        o.append(R.cyl("chassis_ant_%s" % s, 0.007, 0.46,
                       (sx * 0.16, D * 0.42, z + 0.62),
                       mat=pal.joint, verts=8, bev=0.002, segments=1))
        o.append(R.sphere("chassis_anttip_%s" % s, 0.017,
                          (sx * 0.16, D * 0.42, z + 0.85),
                          mat=pal.core, segments=12, rings=8))

    # ── 双臂（细，只为完整性；武器系统仍按手臂算伤害）──
    for s, sx in (("L", -1), ("R", 1)):
        shx = sx * (W * 0.50 + 0.030)
        shz = z + H * 0.30
        o.append(R.sphere("shoulder_%s" % s, 0.080, (shx, 0, shz),
                          mat=pal.joint, segments=18, rings=14))
        o.append(R.cyl("part_arm_%s" % s, 0.058, 0.56,
                       (shx + sx * 0.015, -0.02, shz - 0.32),
                       mat=pal.steel, verts=18, bev=0.006, segments=2))
        o.append(R.sphere("arm_elbow_%s" % s, 0.062,
                          (shx + sx * 0.015, -0.03, shz - 0.60),
                          mat=pal.joint, segments=16, rings=12))
        # ── 手臂：上臂 + 肘 + 前臂 + 末端传感器 ──
        # ⚠️ 第七十五轮：前臂原来止于 shz-0.86，末端什么都没有 ——
        #    游戏里就是两根光秃秃的圆筒，读作"建模不完整"。
        #    这里补一块"气象传感器模块"（探头 + 环形罩），让手臂有终点。
        _fore_bot = shz - 0.86
        o.append(R.cyl("arm_fore_%s" % s, 0.050, 0.24,
                       (shx + sx * 0.015, -0.05, shz - 0.74),
                       mat=pal.steel_light, verts=16, bev=0.005, segments=2))
        o.append(R.sphere("arm_wrist_%s" % s, 0.046,
                          (shx + sx * 0.015, -0.05, _fore_bot),
                          mat=pal.joint, segments=16, rings=10))
        o.append(R.cyl("arm_sensor_%s" % s, 0.062, 0.14,
                       (shx + sx * 0.015, -0.05, _fore_bot - 0.10),
                       mat=pal.accent, verts=20, bev=0.008, segments=3))
        o.append(R.torus("arm_sensorring_%s" % s, 0.066, 0.012,
                         (shx + sx * 0.015, -0.05, _fore_bot - 0.17),
                         mat=pal.copper, major_seg=24, minor_seg=8))
        o.append(R.sphere("arm_probe_%s" % s, 0.026,
                          (shx + sx * 0.015, -0.05, _fore_bot - 0.21),
                          mat=pal.core, segments=14, rings=10))

    # ── 双腿 ──
    # ⚠️ 第七十五轮：原来大腿/小腿长度是硬编码（0.58 / 0.48），
    #    与髋/膝/踝的实际位置对不上，末端接不住脚 → 游戏里腿是"一节一节的"。
    #    改为与园丁/护卫同一套规则：由髋踝落差反算，各段按三维距离并倾斜。
    for s, sx in (("L", -1), ("R", 1)):
        lx = sx * 0.165
        _ank = 0.06
        _top = z - H * 0.50
        _full = _top - _ank
        _hip_z = _ank + _full * 0.92
        # ⚠️ 第七十八轮：0.10 时 slack（(L1+L2) − 髋踝落差）只有 2.7cm ，
        #    是全机体里最小的 —— 腿几乎伸直，IK 解算在近奇异点附近抖动。
        #    提到 0.22，slack 升到 12.3cm，大腿前倾 25.6°（仍自然）。
        _knee_off = _full * 0.22
        _knee_z = (_hip_z + _ank) * 0.5
        o.append(R.sphere("leg_hip_%s" % s, 0.085, (lx, 0, _hip_z),
                          mat=pal.joint, segments=18, rings=12))
        # 髋柱：躯干 cut_below 把底部切平抬高，髋球顶离它有一段空隙（同园丁/护卫）
        o.append(R.cyl_between("leg_hippost_%s" % s,
                               (lx, 0, _hip_z),
                               (lx, 0, z - H * 0.30),
                               0.055, mat=pal.joint, verts=16,
                               bev=0.005, segments=2))
        _dv1 = math.sqrt(_knee_off ** 2 + (_hip_z - _knee_z) ** 2)
        o.append(R.cyl_between("part_leg_%s" % s, (lx, 0.0, _hip_z),
                               (lx, -_knee_off, _knee_z), 0.070,
                               mat=pal.steel, verts=18, bev=0.006,
                               segments=2))
        o.append(R.sphere("leg_knee_%s" % s, 0.078, (lx, -_knee_off, _knee_z),
                          mat=pal.joint, segments=18, rings=12))
        _dv2 = math.sqrt(_knee_off ** 2 + (_knee_z - _ank) ** 2)
        # 小腿：膝球中心 → 踝中心，直接由两端点建（见 robotlib.cyl_between）
        o.append(R.cyl_between("leg_shin_%s" % s, (lx, -_knee_off, _knee_z),
                               (lx, 0.0, _ank), 0.062,
                               mat=pal.steel_light, verts=18, bev=0.005,
                               segments=2))
        o.append(R.rounded_box("part_foot_%s" % s, (0.19, 0.34, 0.12),
                               (lx, -0.05, 0.06), mat=pal.joint,
                               radius=0.030, segments=4))
        o.append(R.ellipsoid("foot_toe_%s" % s, (0.085, 0.065, 0.055),
                             (lx, -0.19, 0.058), mat=pal.steel_light,
                             segments=16, rings=10, cut_below=-0.40))

    # ⚠️ 第七十九轮：同园丁，包围盒改用躯干椭球的真实尺寸
    o += R.greeble("weather_gb", (0, 0, z),
                   (W * 0.50, D * 0.54, H * 0.52), 18, 405,
                   pal.greeble_mats(), faces=('+X', '-X', '+Z'),
                   scale=(0.015, 0.045), depth=(0.005, 0.015))
    return o, "气象机", 2.70


# ═══════════════════════════════════════════════════════════
# 6. 重型护卫 —— 具名同伴
# ═══════════════════════════════════════════════════════════

def guard(pal):
    """重型护卫：双穹顶肩甲 + 弧面胸甲 + 圆角盾 + 重锤。

    剪影特征：两个比头还大的半球肩甲，加一面到膝盖的盾。
    旧版是三层方板叠起来，从侧面看是三条直线。
    """
    o = []
    W, D, H = 0.94, 0.62, 0.86
    z = 1.70

    # ── 躯干：椭球 + 弧面胸甲 ──
    o.append(R.ellipsoid("part_torso", (W * 0.50, D * 0.54, H * 0.52),
                         (0, 0, z), mat=pal.steel, segments=32, rings=22,
                         cut_below=-0.45))
    o.append(R.ellipsoid("chassis_chest", (W * 0.42, D * 0.26, H * 0.40),
                         (0, -D * 0.40, z + 0.02), mat=pal.accent,
                         segments=30, rings=20, cut_below=-0.35))
    # 胸甲中缝：一条竖向凹槽（用一根细长圆柱压进去，比画线有效）
    # ⚠️ 第七十五轮：旧值把中缝放在 y=-D*0.50=-0.31，而胸甲椭球中心在 y=-D*0.40=-0.248、
    #    前表面到 y=-0.408 —— 中缝落在胸甲**内部**，只在胸甲下边缘以下露出一小截，
    #    游戏里看起来就是"胸口挂着一根悬空的黑色细棍"（像建模缺了一半）。
    #    改为贴住胸甲前表面，长度略短于胸甲高度（不能超出，否则上下都戳出来）。
    _chest_cy = -D * 0.40
    _chest_ry = D * 0.26
    _chest_rz = H * 0.40
    o.append(R.cyl("chassis_chestseam", 0.012, _chest_rz * 1.30,
                   (0, _chest_cy - _chest_ry * 0.82, z + 0.02), mat=pal.joint,
                   verts=10, bev=0.002, segments=1))

    # ── 核心 ──
    cz = z + H * 0.08
    o.append(R.sphere("part_core", 0.092, (0, -D * 0.56, cz),
                      mat=pal.core, segments=24, rings=16))
    for i, rr in enumerate((0.108, 0.132)):
        o.append(R.torus("part_corering_%d" % (i + 1), rr, 0.014,
                         (0, -D * 0.54 + i * 0.02, cz),
                         rot=(math.radians(90), 0, 0),
                         mat=pal.joint if i == 0 else pal.copper,
                         major_seg=28, minor_seg=8))

    # ── 颈 + 头 ──
    # ⚠️ 同园丁/气象：头部不能 cut_below，否则颅骨底面被切掉、悬在颈球上方（"头浮空"）。
    nz = z + H * 0.50
    o.append(R.sphere("chassis_neck", 0.078, (0, 0, nz), mat=pal.joint,
                      segments=18, rings=12))
    hz = nz + 0.158
    o.append(R.ellipsoid("chassis_head", (0.185, 0.195, 0.165),
                         (0, -0.01, hz), mat=pal.steel,
                         segments=28, rings=18))
    # 护额：弧形眉甲
    o.append(R.ellipsoid("head_brow", (0.150, 0.070, 0.055),
                         (0, -0.155, hz + 0.075), mat=pal.accent,
                         segments=24, rings=14, cut_below=-0.30))
    o.append(R.ellipsoid("head_visor", (0.130, 0.040, 0.036),
                         (0, -0.180, hz - 0.01), mat=pal.visor,
                         segments=20, rings=12, cut_below=-0.20))

    # ── 肩：双穹顶（里层钢板色 + 外层识别色收边环）──
    for s, sx in (("L", -1), ("R", 1)):
        shx = sx * (W * 0.50 + 0.10)
        shz = z + H * 0.26
        o.append(R.sphere("shoulder_%s" % s, 0.155, (shx, 0, shz),
                          mat=pal.joint, segments=22, rings=16))
        # 外层穹顶
        o.append(R.ellipsoid("pauldron_%s" % s, (0.290, 0.275, 0.240),
                             (shx, -0.01, shz + 0.03),
                             rot=(0, math.radians(-8 * sx), 0),
                             mat=pal.steel, segments=28, rings=20,
                             cut_below=-0.28))
        # 内层小穹顶（压出层次）
        o.append(R.ellipsoid("pauldron_in_%s" % s, (0.195, 0.190, 0.165),
                             (shx + sx * 0.015, -0.03, shz + 0.09),
                             mat=pal.steel_light, segments=24, rings=18,
                             cut_below=-0.15))
        # 识别色收边环（不做整块大色，会像塑料玩具）
        o.append(R.torus("pauldron_trim_%s" % s, 0.268, 0.020,
                         (shx, -0.01, shz + 0.02),
                         rot=(math.radians(8 * sx), 0, 0),
                         mat=pal.accent, major_seg=32, minor_seg=8))

    # ── 左臂 + 盾 ──
    ax = -(W * 0.50 + 0.10)
    o.append(R.cyl("part_arm_L", 0.105, 0.66, (ax, -0.03, z - H * 0.30),
                   mat=pal.steel, verts=22, bev=0.010, segments=3))
    o.append(R.sphere("arm_elbow_L", 0.110, (ax, -0.05, z - H * 0.62),
                      mat=pal.joint, segments=20, rings=14))
    # ⚠️ 第七十五轮：左臂原来止于肘球，末端没有任何部件（"光秃秃的一截"）。
    #    补一段前臂 + 两指液压夹爪，与右手的重锤对称。
    _lz = z - H * 0.62
    o.append(R.cyl("arm_fore_L", 0.082, 0.26, (ax, -0.05, _lz - 0.15),
                   mat=pal.steel_light, verts=20, bev=0.008, segments=3))
    o.append(R.sphere("arm_palm_L", 0.095, (ax, -0.06, _lz - 0.31),
                      mat=pal.joint, segments=20, rings=14))
    for i, fx in enumerate((-1, 1)):
        o.append(R.prism("arm_finger_L%d" % (i + 1), (0.035, 0.075, 0.20),
                         (ax + fx * 0.055, -0.09, _lz - 0.44),
                         rot=(math.radians(-12), 0, math.radians(fx * 9)),
                         top=(1.0, 0.5), mat=pal.steel_light,
                         bev=0.005, segments=2))
    # 盾：圆角大板 + 两道加强筋 + 观察缝
    # 盾：上宽下窄的梯形 + 大倒角（圆角方块读作"铁板"，梯形才读作"盾"）
    # ⚠️ prism 的倒角宽度会被 min(size)*0.24 限制 —— 盾厚 0.095 时
    #    上限只有 2.3cm，看起来仍然是刀刃直角。厚度加到 0.20 才有真圆角。
    o.append(R.prism("shield", (0.56, 0.20, 1.20),
                     (ax - 0.22, -0.30, z - H * 0.10),
                     top=(1.0, 1.0), bottom=(0.52, 0.72),
                     mat=pal.accent, bev=0.048, segments=5))
    # 底尖：一个向下的锥，把"上宽下窄"收成一个真正的盾形
    o.append(R.cone("shield_tip", 0.30, 0.045, 0.26,
                    (ax - 0.22, -0.30, z - H * 0.10 - 0.60 - 0.11),
                    rot=(math.radians(180), 0, 0), mat=pal.accent_dark,
                    verts=20, bev=0.012))
    # 盾面中心凸起：一块小穹顶，让盾在侧光下有高光过渡
    o.append(R.ellipsoid("shield_boss", (0.155, 0.070, 0.32),
                         (ax - 0.24, -0.40, z - H * 0.06),
                         mat=pal.accent_dark, segments=24, rings=16,
                         cut_below=-0.30))
    for i, dz in enumerate((0.36, -0.26)):
        o.append(R.prism("shield_rib_%d" % (i + 1), (0.38, 0.055, 0.075),
                         (ax - 0.21, -0.40, z - H * 0.10 + dz),
                         mat=pal.accent_dark, bev=0.010, segments=3))
    o.append(R.ellipsoid("shield_slit", (0.115, 0.030, 0.028),
                         (ax - 0.21, -0.36, z + H * 0.22),
                         mat=pal.visor, segments=20, rings=12,
                         cut_below=-0.20))

    # ── 右臂 + 重锤 ──
    ax2 = W * 0.50 + 0.10
    o.append(R.cyl("part_arm_R", 0.105, 0.66, (ax2, -0.03, z - H * 0.30),
                   mat=pal.steel, verts=22, bev=0.010, segments=3))
    o.append(R.sphere("arm_elbow_R", 0.110, (ax2, -0.05, z - H * 0.62),
                      mat=pal.joint, segments=20, rings=14))
    # 锤柄
    o.append(R.cyl("arm_hammer", 0.055, 0.52, (ax2 + 0.04, -0.14, z - H * 0.80),
                   rot=(math.radians(16), 0, 0), mat=pal.joint,
                   verts=18, bev=0.006, segments=2))
    # 锤头：圆柱 + 球端（不是方砖）
    o.append(R.cyl("arm_hammerhead", 0.135, 0.34, (ax2 + 0.04, -0.30, z - H * 0.86),
                   rot=(math.radians(90), 0, math.radians(16)),
                   mat=pal.steel_light, verts=24, bev=0.012, segments=3))
    for i, dy in enumerate((-0.14, 0.14)):
        o.append(R.torus("arm_hammerring_%d" % (i + 1), 0.138, 0.016,
                         (ax2 + 0.04, -0.30 + dy, z - H * 0.86),
                         rot=(math.radians(90), 0, math.radians(16)),
                         mat=pal.copper, major_seg=24, minor_seg=8))

    # ── 双腿：圆柱 + 球膝 + 圆角脚 ──
    # ⚠️ 第七十一轮：与 hauler/colossus 统一几何规则。
    #    旧实现圆柱长度/中心是手填的（0.60 / 0.48），与关节对不上；
    #    且髋高使腿几乎伸直（髋踝≈L1+L2），IK 一动脚就离地 → "走路悬空"。
    for s, sx in (("L", -1), ("R", 1)):
        lx = sx * 0.265
        _top = z - H * 0.50
        _ank = 0.085
        _full = _top - _ank
        hip_z = _ank + _full * 0.92
        knee_off = _full * 0.10
        knee_z = (hip_z + _ank) * 0.5
        kneeY = -knee_off
        o.append(R.sphere("leg_hip_%s" % s, 0.130, (lx, 0, hip_z),
                          mat=pal.joint, segments=20, rings=14))
        # ⚠️ 第七十九轮：与园丁同样的断裂 —— 躯干 cut_below 把底部切平抬高，
        #    髋球顶离它有 24.6cm。补一段髋柱插进躯干。
        o.append(R.cyl_between("leg_hippost_%s" % s,
                               (lx, 0, hip_z),
                               (lx, 0, z - H * 0.30),
                               0.070, mat=pal.joint, verts=16,
                               bev=0.006, segments=2))
        o.append(R.torus("leg_hipring_%s" % s, 0.132, 0.016,
                         (lx + sx * 0.06, 0, hip_z),
                         rot=(0, math.radians(90), 0), mat=pal.copper,
                         major_seg=24, minor_seg=8))
        _dv1 = math.sqrt(knee_off ** 2 + (hip_z - knee_z) ** 2)
        o.append(R.cyl_between("part_leg_%s" % s, (lx, 0.0, hip_z),
                               (lx, kneeY, knee_z), 0.115,
                               mat=pal.steel, verts=22, bev=0.010,
                               segments=3))
        o.append(R.sphere("leg_knee_%s" % s, 0.125, (lx, kneeY, knee_z),
                          mat=pal.joint, segments=20, rings=14))
        _dv2 = math.sqrt(knee_off ** 2 + (knee_z - _ank) ** 2)
        # 小腿：膝球中心 → 踝中心，直接由两端点建（见 robotlib.cyl_between）
        o.append(R.cyl_between("leg_shin_%s" % s, (lx, kneeY, knee_z),
                               (lx, 0.0, _ank), 0.095,
                               mat=pal.steel_light, verts=20, bev=0.008,
                               segments=3))
        o.append(R.rounded_box("part_foot_%s" % s, (0.30, 0.50, 0.17),
                               (lx, -0.06, _ank), mat=pal.joint,
                               radius=0.040, segments=4))
        o.append(R.ellipsoid("foot_toe_%s" % s, (0.135, 0.085, 0.075),
                             (lx, -0.27, 0.082), mat=pal.steel_light,
                             segments=18, rings=12, cut_below=-0.40))
        o += R.piston("leg_pist_%s" % s,
                      (lx, -0.14, hip_z - 0.16),
                      (lx, -0.12, hip_z - 0.62),
                      0.030, pal.steel_light, pal.copper)

    # ⚠️ 第七十九轮：同园丁，包围盒改用躯干椭球的真实尺寸
    o += R.greeble("guard_gb", (0, 0, z),
                   (W * 0.50, D * 0.54, H * 0.52), 26, 406,
                   pal.greeble_mats(), faces=('+X', '-X', '+Z', '+Y'),
                   scale=(0.02, 0.055), depth=(0.006, 0.018))
    return o, "重型护卫", 2.80


# ═══════════════════════════════════════════════════════════
# 目录
# ═══════════════════════════════════════════════════════════

CATALOG = [
    ("patrol", patrol, (0.32, 0.76, 0.86), (0.35, 0.95, 0.95)),
    ("hauler", hauler, (0.72, 0.52, 0.24), (1.00, 0.72, 0.30)),
    ("colossus", colossus, (0.62, 0.34, 0.30), (1.00, 0.42, 0.32)),
    ("gardener", gardener, (0.42, 0.72, 0.38), (0.55, 0.95, 0.50)),
    ("weather", weather, (0.36, 0.62, 0.86), (0.45, 0.78, 1.00)),
    ("guard", guard, (0.78, 0.44, 0.30), (1.00, 0.56, 0.32)),
]


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    out_dir, sheet_only = "./out", False
    only = ""
    i = 0
    while i < len(argv):
        if argv[i] == "--out" and i + 1 < len(argv):
            out_dir = argv[i + 1]; i += 2
        elif argv[i] == "--sheet-only":
            sheet_only = True; i += 1
        elif argv[i] == "--only" and i + 1 < len(argv):
            only = argv[i + 1]; i += 2
        else:
            i += 1
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    if not sheet_only:
        print("\n" + "=" * 58)
        print("敌人：逐个生成")
        print("=" * 58)
        for code, fn, accent, glow in CATALOG:
            if only and code != only:
                continue
            R.new_scene()
            # 双足机拆出 thigh/shin/foot 三段骨（步态两骨 IK 需要）；四足与悬浮机保持原样
            R.SPLIT_LEGS = code in ("gardener", "weather", "guard")
            R.SPLIT_QUAD = code in ("hauler", "colossus")
            pal = R.Palette(accent, glow, "enemy_%s" % code)
            objs, label, height = fn(pal)
            # 自动绑定：按部件名推断骨骼（part_core / arm_* / leg_* / torso），
            # 并顺带完成 UV 与三级 LOD。
            # ⚠️ 第八十二轮：LOD 分段保留率从 0.45/0.18 提到 0.62/0.34。
            #    巡逻机是 36 段的球，0.45 时 LOD1 只剩约 16 段 ——
            #    在检阅/中距离（约 10m）就切到 LOD1，球面出现明显经向条纹。
            #    敌人是场上的主角，LOD 切得太早非常显眼。
            mesh, arm, lods = R.auto_rig(
                objs, "Enemy_%s" % code.capitalize(),
                lods=((0.62, "_LOD1"), (0.34, "_LOD2")))
            tris = R.tri_count(mesh)
            mn, mx = R.world_bounds([mesh])
            base = os.path.join(out_dir, "enemy_%s" % code)
            R.save_blend(base + ".blend")
            try:
                R.export_fbx(base + ".fbx")
            except Exception as e:
                print("    [FAIL] %s: %s" % (code, e))
            print("  %-10s %-8s %6d tris  高 %.2f m  %2d 骨骼  LOD %s"
                  % (code, label, tris, mx[2] - mn[2],
                     len(arm.data.bones),
                     "/".join(str(t) for _, t in lods)))

    print("\n生成敌人目录图...")
    R.new_scene()
    groups, labels = [], []
    for code, fn, accent, glow in CATALOG:
        if only and code != only:
            continue
        pal = R.Palette(accent, glow, "enemy_%s" % code)
        objs, label, height = fn(pal)
        groups.append(objs)
        labels.append(label)
    cols = min(3, max(1, len(groups)))
    rows, cw, cd = R.layout_grid(groups, cols, gap=1.1)
    span_x, span_z = cols * cw, rows * cd
    png = os.path.join(out_dir, "sheet_enemies.png")
    # flat=False → 3/4 机位。正前方看不出前后腿 / 货舱朝向，
    # 目录图的意义就是"一眼看懂结构"，必须给一个能看出深度的角度。
    R.setup_render(png, (0, 0, 0), res=1100, wide=True,
                   span=(span_x, span_z), lens=50, flat=False)
    R.render_to(png)
    print("  [ok] sheet_enemies.png  (%d 个敌人)" % len(groups))
    print("完成。")


if __name__ == "__main__":
    main()
