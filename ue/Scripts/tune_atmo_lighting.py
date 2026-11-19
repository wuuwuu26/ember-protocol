# -*- coding: utf-8 -*-
"""大气天空 v3：抬高太阳、冷暖对冲、提高机体补光。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)
log = lambda m: unreal.log("[大气布光] %s" % m)


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


def col(r, g, b, a=255):
    return unreal.Color(int(r), int(g), int(b), int(a))

for a in unreal.EditorLevelLibrary.get_all_level_actors():
    cn = a.get_class().get_name()
    lbl = a.get_actor_label()
    if cn == "DirectionalLight":
        a.set_actor_rotation(unreal.Rotator(0, -8, 35), False)
        c = g(a, "directional_light_component") or g(a, "light_component")
        setp(c, "intensity", 18000.0, "Sun.")
        setp(c, "use_temperature", True, "Sun.")
        setp(c, "temperature", 5600.0, "Sun.")
        setp(c, "atmosphere_sun_light", True, "Sun.")
        setp(c, "light_source_angle", 0.8, "Sun.")
        log("太阳：-8° / 18000 lux / 5600K")
    elif cn == "SkyAtmosphere":
        c = g(a, "atmosphere_component") or g(a, "sky_atmosphere_component")
        if c:
            setp(c, "mie_scattering_scale", 0.4, "Atmo.")
            setp(c, "rayleigh_scattering_scale", 1.0, "Atmo.")
            log("大气：Mie 0.4 / Rayleigh 1.0")
    elif cn == "SkyLight":
        c = g(a, "sky_light_component") or g(a, "light_component")
        setp(c, "intensity", 3.0, "Sky.")
        setp(c, "light_color", col(190, 215, 255), "Sky.")
        setp(c, "real_time_capture", True, "Sky.")
        setp(c, "lower_hemisphere_is_black", True, "Sky.")
        c.recapture_sky()
        log("天光：3.0 / 冷蓝")
    elif cn == "SpotLight" and lbl.startswith("FloodLight"):
        c = g(a, "spot_light_component") or g(a, "light_component")
        setp(c, "intensity", 2800.0, "Flood.")
        setp(c, "use_temperature", True, "Flood.")
        setp(c, "temperature", 5000.0, "Flood.")
        setp(c, "attenuation_radius", 3200.0, "Flood.")
    elif cn == "PointLight" and lbl.startswith("FillLight"):
        c = g(a, "point_light_component") or g(a, "light_component")
        setp(c, "intensity", 2800.0, "Fill.")
        setp(c, "use_temperature", True, "Fill.")
        setp(c, "temperature", 6500.0, "Fill.")
        setp(c, "attenuation_radius", 2600.0, "Fill.")
    elif cn == "PointLight" and lbl.startswith("AccentLight"):
        c = g(a, "point_light_component") or g(a, "light_component")
        setp(c, "intensity", 1200.0, "Accent.")
        setp(c, "use_temperature", True, "Accent.")
        setp(c, "temperature", 6500.0, "Accent.")
    elif cn == "ExponentialHeightFog":
        c = g(a, "component") or g(a, "exponential_height_fog_component")
        setp(c, "fog_density", 0.003, "Fog.")
        setp(c, "fog_inscattering_luminance", unreal.LinearColor(0.03, 0.045, 0.08, 1.0), "Fog.")
        setp(c, "start_distance", 2000.0, "Fog.")
        setp(c, "enable_volumetric_fog", True, "Fog.")
        setp(c, "volumetric_fog_extinction_scale", 0.5, "Fog.")
    elif cn == "PostProcessVolume":
        setp(a, "unbound", True, "PP.")
        setp(a, "priority", 100.0, "PP.")
        setp(a, "blend_weight", 1.0, "PP.")
        st = g(a, "settings")
        if not st:
            continue
        setp(st, "override_auto_exposure_method", True, "PP.")
        setp(st, "auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL, "PP.")
        setp(st, "override_auto_exposure_bias", True, "PP.")
        setp(st, "auto_exposure_bias", 0.0, "PP.")
        setp(st, "override_color_contrast", True, "PP.")
        setp(st, "color_contrast", unreal.Vector4(1.10, 1.10, 1.12, 1.0), "PP.")
        setp(st, "override_color_saturation", True, "PP.")
        setp(st, "color_saturation", unreal.Vector4(0.95, 0.95, 0.96, 1.0), "PP.")
        setp(st, "override_bloom_intensity", True, "PP.")
        setp(st, "bloom_intensity", 0.45, "PP.")
        setp(st, "override_bloom_threshold", True, "PP.")
        setp(st, "bloom_threshold", 1.0, "PP.")
        setp(st, "override_vignette_intensity", True, "PP.")
        setp(st, "vignette_intensity", 0.25, "PP.")
        setp(st, "override_ambient_occlusion_intensity", True, "PP.")
        setp(st, "ambient_occlusion_intensity", 0.8, "PP.")
        setp(st, "override_motion_blur_amount", True, "PP.")
        setp(st, "motion_blur_amount", 0.0, "PP.")

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_all_dirty_levels()
log("完成")