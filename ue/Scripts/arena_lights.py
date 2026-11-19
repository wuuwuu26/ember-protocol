# -*- coding: utf-8 -*-
"""
竞技场投光灯组。

为什么必须有它：
    竞技场四面是 5 米高的围墙，太阳任何低角度都会被墙挡住 ——
    实测玩家出生点 (-1500, 0) 离西墙只有 300cm，永远在墙影里。
    只靠太阳 + 天光，机体就是一块纯黑剪影（截图确认过：整机 RGB 接近 0）。
    真实工业场地在这种情况下会开灯，这里也一样：沿两侧天桥架一排投光灯，
    把场地中央照成一条"跑道"。

布光逻辑：
    · 灯装在天桥高度（Z≈700），从两侧斜向下打，形成交叉光，避免"顶光死板"
    · 色温 4200K 暖白 —— 和天空的冷蓝形成冷暖对冲，这是画面好看的核心
    · 只有 2 盏开阴影：8 盏全开会把 GPU 拖垮，而且阴影互相打架会脏
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
LOG = "[投光灯]"

# 灯位：两侧各 4 盏，沿 X 轴铺开；Y=±1150 在天桥外侧，Z=700 高于天桥
LAMPS = [
    (-1300.0, -1150.0, 700.0),
    (-450.0, -1150.0, 700.0),
    (450.0, -1150.0, 700.0),
    (1250.0, -1150.0, 700.0),
    (-1300.0, 1150.0, 700.0),
    (-450.0, 1150.0, 700.0),
    (450.0, 1150.0, 700.0),
    (1250.0, 1150.0, 700.0),
]
# 瞄准点抬到 Z=170（机体胸口高度）而不是地面。
# 原因：瞄准地面时，光锥中心全落在地板上 → 地板过曝、机体立面吃不到光。
# 抬高之后光束"扫过"机体，地板只吃到光锥边缘，画面重心从地面回到主体。
AIM = [
    (-1300.0, -300.0, 170.0),
    (-450.0, -300.0, 170.0),
    (450.0, -300.0, 170.0),
    (1250.0, -300.0, 170.0),
    (-1300.0, 300.0, 170.0),
    (-450.0, 300.0, 170.0),
    (450.0, 300.0, 170.0),
    (1250.0, 300.0, 170.0),
]

INTENSITY = 6200.0     # 坎德拉；投光灯要远高于普通点光才有"灯柱"感
RADIUS = 3600.0
INNER = 18.0
OUTER = 46.0
TEMP = 4200.0
SHADOW_INDEX = (0, 3, 4, 7)   # 只这四盏开阴影


def log(m):
    unreal.log("%s %s" % (LOG, m))


unreal.EditorLevelLibrary.load_level(LEVEL)

# 清掉上一次生成的（幂等）
killed = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() == "SpotLight" and \
            a.get_actor_label().startswith("FloodLight"):
        unreal.EditorLevelLibrary.destroy_actor(a)
        killed += 1
log("清掉旧投光灯 %d 盏" % killed)

n = 0
for i, (loc, aim) in enumerate(zip(LAMPS, AIM)):
    rot = unreal.MathLibrary.find_look_at_rotation(
        unreal.Vector(*loc), unreal.Vector(*aim))
    sl = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SpotLight, unreal.Vector(*loc), rot)
    if not sl:
        log("❌ 第 %d 盏生成失败" % i)
        continue
    sl.set_actor_label("FloodLight_%d" % i)
    c = None
    for p in ("spot_light_component", "light_component"):
        try:
            c = sl.get_editor_property(p)
            if c:
                break
        except Exception:
            pass
    if not c:
        log("❌ 第 %d 盏没有光组件" % i)
        continue
    for attr, val in (
        ("intensity", INTENSITY),
        ("attenuation_radius", RADIUS),
        ("inner_cone_angle", INNER),
        ("outer_cone_angle", OUTER),
        ("use_temperature", True),
        ("temperature", TEMP),
        ("cast_shadows", i in SHADOW_INDEX),
        ("mobility", unreal.ComponentMobility.MOVABLE),
        ("volumetric_scattering_intensity", 1.0),
    ):
        try:
            c.set_editor_property(attr, val)
        except Exception as e:
            log("  ❌ %s: %s" % (attr, str(e)[:70]))
    n += 1
    log("灯 %d: %s → %s 强度=%.0f" % (i, loc, aim, INTENSITY))

unreal.EditorLevelLibrary.save_current_level()
log("完成：%d 盏投光灯" % n)

# ─────────────────────────────────────────────
# 补光（Fill）
# ─────────────────────────────────────────────
# 为什么需要：投光灯全部朝下打，**地板亮、立面黑** ——
# 机体站在场地中央时，只有头顶和肩甲能吃到光，躯干/腿部全是剪影。
# 实测：地板亮度 0.55、机体躯干 0.12，差 4 倍以上，画面读起来就是"一块黑影"。
#
# 补光放在 3.8m 高、半径 9m 的位置，**横向**照机体立面；冷白 5600K，
# 和 4200K 的暖投光形成冷暖对冲（这是夜景机甲最经典的一套打光）。
# 不开阴影：补光只负责"把暗部提起来"，开阴影只会互相打架。
FILLS = [
    (-650.0, -650.0, 320.0),
    (650.0, -650.0, 320.0),
    (-650.0, 650.0, 320.0),
    (650.0, 650.0, 320.0),
]
FILL_INTENSITY = 4200.0
FILL_RADIUS = 2600.0
FILL_TEMP = 5600.0

killed = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() == "PointLight" and \
            a.get_actor_label().startswith("FillLight"):
        unreal.EditorLevelLibrary.destroy_actor(a)
        killed += 1
log("清掉旧补光 %d 盏" % killed)

nf = 0
for i, loc in enumerate(FILLS):
    pl = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PointLight, unreal.Vector(*loc), unreal.Rotator(0, 0, 0))
    if not pl:
        continue
    pl.set_actor_label("FillLight_%d" % i)
    c = None
    for p in ("point_light_component", "light_component"):
        try:
            c = pl.get_editor_property(p)
            if c:
                break
        except Exception:
            pass
    if not c:
        continue
    for attr, val in (
        ("intensity", FILL_INTENSITY),
        ("attenuation_radius", FILL_RADIUS),
        ("use_temperature", True),
        ("temperature", FILL_TEMP),
        ("cast_shadows", False),
        ("mobility", unreal.ComponentMobility.MOVABLE),
        ("volumetric_scattering_intensity", 0.0),
    ):
        try:
            c.set_editor_property(attr, val)
        except Exception as e:
            log("  ❌ fill %s: %s" % (attr, str(e)[:60]))
    nf += 1
log("补光：%d 盏（%.0f cd / %.0fK）" % (nf, FILL_INTENSITY, FILL_TEMP))

unreal.EditorLevelLibrary.save_current_level()
