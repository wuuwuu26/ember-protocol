# -*- coding: utf-8 -*-
"""大气布光 v5：让太阳越过围墙，先保证机器人可读。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)
log = lambda m: unreal.log("[大气v5] %s" % m)


def g(o, a, d=None):
    try:
        return o.get_editor_property(a)
    except Exception:
        return d


def setp(o, a, v, tag=""):
    try:
        o.set_editor_property(a, v)
        return True
    except Exception as e:
        log("  ❌ %s%s: %s" % (tag, a, str(e)[:90]))
        return False

for a in unreal.EditorLevelLibrary.get_all_level_actors():
    cn = a.get_class().get_name()
    lbl = a.get_actor_label()
    if cn == "DirectionalLight":
        a.set_actor_rotation(unreal.Rotator(0, 15, 35), False)
        c = g(a, "directional_light_component") or g(a, "light_component")
        setp(c, "intensity", 50000.0, "Sun.")
        setp(c, "use_temperature", True, "Sun.")
        setp(c, "temperature", 6000.0, "Sun.")
        setp(c, "atmosphere_sun_light", True, "Sun.")
        setp(c, "light_source_angle", 1.0, "Sun.")
        log("太阳：+15° / 50000 lux / 6000K")
    elif cn == "SkyLight":
        c = g(a, "sky_light_component") or g(a, "light_component")
        setp(c, "intensity", 4.0, "Sky.")
        setp(c, "light_color", unreal.Color(190, 215, 255, 255), "Sky.")
        setp(c, "real_time_capture", True, "Sky.")
        setp(c, "lower_hemisphere_is_black", True, "Sky.")
        c.recapture_sky()
        log("天光：4.0 / 冷蓝")
    elif cn == "SpotLight" and lbl.startswith("FloodLight"):
        c = g(a, "spot_light_component") or g(a, "light_component")
        setp(c, "intensity", 4000.0, "Flood.")
        setp(c, "use_temperature", True, "Flood.")
        setp(c, "temperature", 5200.0, "Flood.")
        setp(c, "attenuation_radius", 3400.0, "Flood.")
    elif cn == "PointLight" and lbl.startswith("FillLight"):
        c = g(a, "point_light_component") or g(a, "light_component")
        setp(c, "intensity", 4000.0, "Fill.")
        setp(c, "use_temperature", True, "Fill.")
        setp(c, "temperature", 6500.0, "Fill.")
        setp(c, "attenuation_radius", 3000.0, "Fill.")
    elif cn == "PointLight" and lbl.startswith("AccentLight"):
        c = g(a, "point_light_component") or g(a, "light_component")
        setp(c, "intensity", 1500.0, "Accent.")
        setp(c, "use_temperature", True, "Accent.")
        setp(c, "temperature", 6500.0, "Accent.")

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_all_dirty_levels()
log("完成")