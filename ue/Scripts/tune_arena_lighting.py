# -*- coding: utf-8 -*-
"""重新布光：天空穹顶提亮、太阳/投光灯降强、环境光转冷。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
MAT_PATH = "/Game/RobotGame/Art/Materials/M_SkyDome"
log = lambda m: unreal.log("[重新布光] %s" % m)


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
        log("  ❌ %s%s: %s" % (tag, a, str(e)[:100]))
        return False


def col(r, g, b, a=255):
    return unreal.Color(int(r), int(g), int(b), int(a))


def linc(r, g, b, a=1.0):
    return unreal.LinearColor(r, g, b, a)

# ── 1. 天空穹顶颜色 ──
mat = unreal.EditorAssetLibrary.load_asset(MAT_PATH)
if not mat:
    raise SystemExit("找不到 M_SkyDome")
mel = unreal.MaterialEditingLibrary
exprs = mel.get_material_expressions(mat)
remap = [
    ((0.028, 0.048, 0.125), (0.060, 0.090, 0.200)),
    ((1.050, 0.780, 0.550), (0.450, 0.320, 0.220)),
    ((0.200, 0.260, 0.420), (0.120, 0.160, 0.280)),
    ((1.100, 0.660, 0.340), (0.550, 0.300, 0.140)),
    ((3.600, 2.600, 1.700), (2.000, 1.400, 0.800)),
]
for e in exprs:
    if e.get_class().get_name() != "MaterialExpressionConstant3Vector":
        continue
    c = e.get_editor_property("constant")
    for old, new in remap:
        if abs(c.r-old[0]) < 0.02 and abs(c.g-old[1]) < 0.02 and abs(c.b-old[2]) < 0.02:
            e.set_editor_property("constant", linc(*new))
            log("天空常量 %s -> (%.3f,%.3f,%.3f)" % (e.get_name(), *new))
            break
setp(mat, "is_sky", True, "SkyMat.")
mel.recompile_material(mat)
unreal.EditorAssetLibrary.save_loaded_asset(mat)
log("M_SkyDome 已更新")

# ── 2. 灯光 ──
unreal.EditorLevelLibrary.load_level(LEVEL)
actors = unreal.EditorLevelLibrary.get_all_level_actors()
for a in actors:
    cn = a.get_class().get_name()
    lbl = a.get_actor_label()
    if cn == "DirectionalLight":
        a.set_actor_rotation(unreal.Rotator(0.0, -22.0, 35.0), False)
        c = g(a, "directional_light_component") or g(a, "light_component")
        setp(c, "intensity", 12000.0, "Sun.")
        setp(c, "use_temperature", True, "Sun.")
        setp(c, "temperature", 6200.0, "Sun.")
        setp(c, "light_source_angle", 1.0, "Sun.")
        setp(c, "cast_shadows", True, "Sun.")
        log("太阳：12000 lux / 6200K")
    elif cn == "SkyLight":
        c = g(a, "sky_light_component") or g(a, "light_component")
        setp(c, "intensity", 2.0, "Sky.")
        setp(c, "light_color", col(200, 220, 255), "Sky.")
        setp(c, "real_time_capture", True, "Sky.")
        setp(c, "lower_hemisphere_is_black", True, "Sky.")
        setp(c, "source_type", unreal.SkyLightSourceType.SLS_CAPTURED_SCENE, "Sky.")
        c.recapture_sky()
        log("天光：2.0 / 冷白")
    elif cn == "SpotLight" and lbl.startswith("FloodLight"):
        c = g(a, "spot_light_component") or g(a, "light_component")
        setp(c, "intensity", 3000.0, "Flood.")
        setp(c, "use_temperature", True, "Flood.")
        setp(c, "temperature", 5000.0, "Flood.")
        setp(c, "attenuation_radius", 3200.0, "Flood.")
    elif cn == "PointLight" and lbl.startswith("FillLight"):
        c = g(a, "point_light_component") or g(a, "light_component")
        setp(c, "intensity", 1500.0, "Fill.")
        setp(c, "use_temperature", True, "Fill.")
        setp(c, "temperature", 6500.0, "Fill.")
    elif cn == "PointLight" and lbl.startswith("AccentLight"):
        c = g(a, "point_light_component") or g(a, "light_component")
        setp(c, "intensity", 1200.0, "Accent.")
        setp(c, "use_temperature", True, "Accent.")
        setp(c, "temperature", 6500.0, "Accent.")

for a in actors:
    if a.get_class().get_name() != "ExponentialHeightFog":
        continue
    c = g(a, "component") or g(a, "exponential_height_fog_component")
    setp(c, "fog_density", 0.006, "Fog.")
    setp(c, "fog_height_falloff", 0.12, "Fog.")
    setp(c, "fog_inscattering_luminance", linc(0.030, 0.042, 0.075), "Fog.")
    setp(c, "start_distance", 1200.0, "Fog.")
    setp(c, "fog_max_opacity", 0.80, "Fog.")
    setp(c, "enable_volumetric_fog", True, "Fog.")
    setp(c, "volumetric_fog_albedo", col(77, 92, 120), "Fog.")
    setp(c, "volumetric_fog_extinction_scale", 0.8, "Fog.")
    setp(c, "volumetric_fog_scattering_distribution", 0.30, "Fog.")
    setp(c, "volumetric_fog_distance", 7000.0, "Fog.")
    log("雾：0.006 / 冷灰蓝")

for a in actors:
    if a.get_class().get_name() != "PostProcessVolume":
        continue
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
    setp(st, "color_contrast", unreal.Vector4(1.08, 1.08, 1.10, 1.0), "PP.")
    setp(st, "override_color_saturation", True, "PP.")
    setp(st, "color_saturation", unreal.Vector4(0.96, 0.96, 0.97, 1.0), "PP.")
    setp(st, "override_bloom_intensity", True, "PP.")
    setp(st, "bloom_intensity", 0.40, "PP.")
    setp(st, "override_bloom_threshold", True, "PP.")
    setp(st, "bloom_threshold", 1.0, "PP.")
    setp(st, "override_vignette_intensity", True, "PP.")
    setp(st, "vignette_intensity", 0.25, "PP.")
    setp(st, "override_ambient_occlusion_intensity", True, "PP.")
    setp(st, "ambient_occlusion_intensity", 0.8, "PP.")
    setp(st, "override_motion_blur_amount", True, "PP.")
    setp(st, "motion_blur_amount", 0.0, "PP.")
    log("PPV：手动 bias=0 / 对比 1.08 / 饱和 0.96")

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_all_dirty_levels()
log("完成")