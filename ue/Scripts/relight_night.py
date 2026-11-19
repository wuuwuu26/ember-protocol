# -*- coding: utf-8 -*-
"""
重做"竞技场夜景"的布光比例：太阳退成冷色剪影光，点光当氛围。

为什么要重做（而不是继续调曝光）：
  上一轮把曝光压到 Bias 4.3 后，过曝仍有 15%，而画面里**没有中间调**
  （中位亮度 0.047、死黑 47%）。这说明问题不在曝光，在**光比**：
  · 太阳 22000 lux 打在一块 albedo 很亮的混凝土地面上 = 整片纯白；
  · 压曝光把暗部一起压死 → 亮部惨白、暗部全黑，中间调消失。
  正确做法是降低主光、抬高环境光与氛围光的比例 —— 也就是"月光般的夜景"。

目标（用 tools/shot_stats.py 量）：
  mean 0.20~0.32、p50 0.12~0.25、clip < 3%、crush < 12%

运行：
    bash tools/ue_py.sh ue/Scripts/relight_night.py "夜景布光"
"""
import unreal

L = "[夜景布光]"
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"

# ── 可调参数（一次改这里，跑一次脚本）──
SUN_LUX = 3200.0                # 太阳：从 22000 降到 3200（约 -2.8 档）
SUN_COLOR = (150, 175, 255)     # 冷蓝月光（原来是 (199,219,255) 近白）
SUN_PITCH = -34.0               # 低一点：影子拉长，形体更有体积
SUN_YAW = 38.0
SUN_SOURCE_ANGLE = 1.2          # 阴影半影更软，硬边场景不显廉价

ACCENT_CD = 2600.0              # 装饰点光：800 → 2600（当氛围主角）
ACCENT_RADIUS = 2100.0
FLOOD_CD = 2600.0               # 泛光：4200 → 2600（不再和太阳抢主光）
SKY_INT = 1.35                  # 天光：3.2 → 1.35（压住环境光，暗部才有层次）

unreal.EditorLevelLibrary.load_level(LEVEL)
actors = unreal.EditorLevelLibrary.get_all_level_actors()


def comp_of(a):
    for attr in ("light_component", "point_light_component",
                 "spot_light_component", "directional_light_component"):
        try:
            c = a.get_editor_property(attr)
            if c:
                return c
        except Exception:
            pass
    return None


def col(rgb):
    return unreal.Color(int(rgb[0]), int(rgb[1]), int(rgb[2]), 255)


n_sun = n_acc = n_flood = n_sky = 0
for a in actors:
    cls = a.get_class().get_name()
    c = comp_of(a)
    if not c:
        continue
    lbl = a.get_actor_label()

    if cls == "DirectionalLight":
        a.set_actor_rotation(unreal.Rotator(0.0, SUN_PITCH, SUN_YAW), False)
        c.set_editor_property("intensity", SUN_LUX)
        c.set_editor_property("light_color", col(SUN_COLOR))
        c.set_editor_property("light_source_angle", SUN_SOURCE_ANGLE)
        c.set_editor_property("atmosphere_sun_light", False)
        c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
        n_sun += 1

    elif cls == "SkyLight":
        c.set_editor_property("intensity", SKY_INT)
        c.set_editor_property("real_time_capture", True)
        c.set_editor_property("lower_hemisphere_is_black", True)
        c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
        n_sky += 1

    elif cls == "PointLight":
        if lbl.startswith("Accent"):
            c.set_editor_property("intensity", ACCENT_CD)
            c.set_editor_property("attenuation_radius", ACCENT_RADIUS)
            c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
            n_acc += 1

    elif cls == "SpotLight":
        if lbl.startswith("Flood"):
            c.set_editor_property("intensity", FLOOD_CD)
            c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
            n_flood += 1

unreal.EditorLevelLibrary.save_current_level()
unreal.log("%s 太阳=%d(%.0f lux) 天光=%d(%.2f) 装饰=%d(%.0fcd) 泛光=%d(%.0fcd)"
           % (L, n_sun, SUN_LUX, n_sky, SKY_INT, n_acc, ACCENT_CD,
              n_flood, FLOOD_CD))
unreal.log("%s 已保存关卡" % L)
