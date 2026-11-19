# -*- coding: utf-8 -*-
"""导出关卡里所有光照/大气/后处理相关 Actor 的关键参数。

为什么需要它：观感出问题时，第一反应总是"改参数"，但真正的答案往往是
"某个 Actor 根本没被创建"或"参数写在了错的组件上"。先把现状读出来，
再决定改什么，比反复盲调快得多。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
LOG = "[场景诊断]"


def log(s):
    unreal.log("%s %s" % (LOG, s))


def g(o, a, d="—"):
    try:
        return o.get_editor_property(a)
    except Exception:
        return d


unreal.EditorLevelLibrary.load_level(LEVEL)
actors = unreal.EditorLevelLibrary.get_all_level_actors()
log("关卡 %s 共 %d 个 Actor" % (LEVEL, len(actors)))

counts = {}
for a in actors:
    cn = a.get_class().get_name()
    counts[cn] = counts.get(cn, 0) + 1
log("类型统计: %s" % sorted(counts.items(), key=lambda x: -x[1])[:20])

# ── 光源 ──
for a in actors:
    cn = a.get_class().get_name()
    if "Light" not in cn:
        continue
    lc = g(a, "light_component", None)
    if lc is None:
        for p in ("point_light_component", "spot_light_component",
                  "directional_light_component", "sky_light_component",
                  "rect_light_component"):
            lc = g(a, p, None)
            if lc is not None:
                break
    if lc is None:
        log("%-22s %-26s 无光组件" % (a.get_actor_label(), cn))
        continue
    info = {
        "intensity": g(lc, "intensity"),
        "color": g(lc, "light_color"),
        "mobility": g(lc, "mobility"),
        "cast_shadow": g(lc, "cast_shadows"),
        "attenuation": g(lc, "attenuation_radius"),
        "temperature": g(lc, "temperature"),
        "use_temp": g(lc, "use_temperature"),
        "affects_world": g(lc, "affects_world"),
        "source_angle": g(lc, "light_source_angle"),
    }
    log("%-22s %-26s %s" % (a.get_actor_label(), cn, info))

# ── 大气 / 雾 ──
for a in actors:
    cn = a.get_class().get_name()
    if cn in ("SkyAtmosphere", "ExponentialHeightFog"):
        log("── %s (%s)" % (a.get_actor_label(), cn))
        if cn == "ExponentialHeightFog":
            c = g(a, "component", None) or g(a, "exponential_height_fog_component", None)
            if c:
                for p in ("fog_density", "fog_height_falloff", "fog_max_opacity",
                          "start_distance", "enable_volumetric_fog",
                          "volumetric_fog_density", "volumetric_fog_albedo",
                          "volumetric_fog_extinction_scale",
                          "volumetric_fog_scattering_distribution",
                          "fog_inscattering_luminance"):
                    log("     %-42s = %s" % (p, g(c, p)))

# ── 后处理 ──
for a in actors:
    if "PostProcess" not in a.get_class().get_name():
        continue
    log("── 后处理 %s 无边界=%s 优先级=%s"
        % (a.get_actor_label(), g(a, "unbound"), g(a, "priority")))
    s = g(a, "settings", None)
    if not s:
        continue
    for p in ("auto_exposure_min_brightness", "auto_exposure_max_brightness",
              "auto_exposure_method", "bloom_intensity", "bloom_threshold",
              "vignette_intensity", "film_grain_intensity", "scene_fringe_intensity",
              "color_saturation", "color_contrast", "color_gain",
              "color_saturation_shadows", "color_gain_shadows",
              "tone_curve_amount", "motion_blur_amount",
              "ambient_occlusion_intensity", "ambient_occlusion_radius",
              "indirect_lighting_intensity", "lumen_scene_lighting_quality"):
        v = g(s, p, "·")
        if v != "·":
            log("     %-38s = %s" % (p, v))
