# -*- coding: utf-8 -*-
"""
给竞技场铺一层"蓝色体积雾 + 暖色气氛光"，目标是把夜景从"曝光问题"变成"氛围问题"。

背景：曝光已经标定到 Bias 3.0（过曝 0.1%、均值 0.28），但画面偏灰、层次平。
下一步不是继续加光，而是给空间加**介质**：
  · 体积雾：让光有"光柱/散射"，远处淡出，空间纵深立刻出来；
  · 冷暖对比：冷雾 + 暖点光 = 电影里最常见的夜景配方。

同时把装饰点光的颜色稍微收一点（纯暖黄 (255,198,140) 在冷雾里会显脏），
提高半径让光的衰减更柔和（灯下方不再是一个硬边圆斑）。

运行：
    bash tools/ue_py.sh ue/Scripts/relight_atmo.py "氛围"
"""
import unreal

L = "[氛围]"
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"

# ── 体积雾 ──
FOG_DENSITY = 0.006
FOG_START = 600.0
VOL_EXTINCTION = 1.6
VOL_ALBEDO = (150, 170, 205)      # 冷灰蓝：夜间丁达尔散射的颜色
VOL_SCATTER = 0.55
FOG_INSCATTER = unreal.LinearColor(0.020, 0.026, 0.042, 1.0)

unreal.EditorLevelLibrary.load_level(LEVEL)

n_fog = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "ExponentialHeightFog":
        continue
    c = a.get_editor_property("component")
    c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    c.set_editor_property("fog_density", FOG_DENSITY)
    c.set_editor_property("fog_height_falloff", 0.10)
    c.set_editor_property("fog_inscattering_luminance", FOG_INSCATTER)
    c.set_editor_property("start_distance", FOG_START)
    c.set_editor_property("fog_max_opacity", 0.90)
    c.set_editor_property("enable_volumetric_fog", True)
    c.set_editor_property("volumetric_fog_albedo",
                          unreal.Color(VOL_ALBEDO[0], VOL_ALBEDO[1],
                                       VOL_ALBEDO[2], 255))
    c.set_editor_property("volumetric_fog_extinction_scale", VOL_EXTINCTION)
    c.set_editor_property("volumetric_fog_scattering_distribution",
                          VOL_SCATTER)
    c.set_editor_property("volumetric_fog_distance", 9000.0)
    n_fog += 1
    unreal.log("%s 雾：密度=%.4f 起始=%.0f 体积消光=%.2f"
               % (L, FOG_DENSITY, FOG_START, VOL_EXTINCTION))

# ── 装饰点光：半径加大、颜色稍收 ──
WARM = (255, 208, 165)
COOL = (120, 180, 255)
n_acc = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "PointLight":
        continue
    lbl = a.get_actor_label()
    if not lbl.startswith("Accent"):
        continue
    c = a.get_editor_property("point_light_component")
    cur = c.get_editor_property("light_color")
    # 原色是暖黄或冷蓝两种，按 B 通道区分，统一到一组更有电影感的色
    is_cool = cur.b > cur.r
    c.set_editor_property("light_color",
                          unreal.Color(*(COOL if is_cool else WARM), 255))
    c.set_editor_property("attenuation_radius", 2600.0)
    n_acc += 1

unreal.EditorLevelLibrary.save_current_level()
unreal.log("%s 雾=%d 装饰灯=%d 已保存" % (L, n_fog, n_acc))
