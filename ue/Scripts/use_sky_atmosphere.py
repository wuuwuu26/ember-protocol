# -*- coding: utf-8 -*-
"""删除黑穹顶，恢复 SkyAtmosphere 作为天空与天光来源。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)
log = lambda m: unreal.log("[大气天空] %s" % m)


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


# 1) 删除黑穹顶
killed = 0
for a in list(unreal.EditorLevelLibrary.get_all_level_actors()):
    lbl = a.get_actor_label()
    if "SkyDome" in lbl:
        log("删除 %s" % lbl)
        unreal.EditorLevelLibrary.destroy_actor(a)
        killed += 1
log("删除穹顶 %d 个" % killed)

# 2) 确保 SkyAtmosphere 存在
atmos = None
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() == "SkyAtmosphere":
        atmos = a
        break
if not atmos:
    atmos = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SkyAtmosphere, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    if atmos:
        atmos.set_actor_label("SkyAtmosphere_Runtime")
        log("新建 SkyAtmosphere")
if atmos:
    c = g(atmos, "atmosphere_component") or g(atmos, "sky_atmosphere_component")
    if c:
        for attr, val in (
            ("mie_scattering_scale", 1.0),
            ("rayleigh_scattering_scale", 1.0),
            ("absorption_scale", 0.0),
            ("multiscattering", True),
        ):
            setp(c, attr, val, "Atmo.")
    log("SkyAtmosphere 已配置")

# 3) 太阳
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    cn = a.get_class().get_name()
    if cn == "DirectionalLight":
        a.set_actor_rotation(unreal.Rotator(0, -26, 42), False)
        c = g(a, "directional_light_component") or g(a, "light_component")
        setp(c, "intensity", 22000.0, "Sun.")
        setp(c, "use_temperature", True, "Sun.")
        setp(c, "temperature", 5200.0, "Sun.")
        setp(c, "atmosphere_sun_light", True, "Sun.")
        setp(c, "light_source_angle", 0.7, "Sun.")
        log("太阳：22000 lux / 5200K / atmosphere_sun_light")
    elif cn == "SkyLight":
        c = g(a, "sky_light_component") or g(a, "light_component")
        setp(c, "intensity", 2.0, "Sky.")
        setp(c, "light_color", unreal.Color(210, 225, 255, 255), "Sky.")
        setp(c, "real_time_capture", True, "Sky.")
        setp(c, "lower_hemisphere_is_black", True, "Sky.")
        setp(c, "source_type", unreal.SkyLightSourceType.SLS_CAPTURED_SCENE, "Sky.")
        c.recapture_sky()
        log("天光：2.0 / 实时捕获")
    elif cn == "ExponentialHeightFog":
        c = g(a, "component") or g(a, "exponential_height_fog_component")
        setp(c, "fog_density", 0.004, "Fog.")
        setp(c, "fog_inscattering_luminance", unreal.LinearColor(0.03, 0.045, 0.08, 1.0), "Fog.")
        setp(c, "start_distance", 1500.0, "Fog.")
        setp(c, "enable_volumetric_fog", True, "Fog.")
        setp(c, "volumetric_fog_extinction_scale", 0.6, "Fog.")
        log("雾：0.004 / 冷灰蓝")

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_all_dirty_levels()
log("完成")