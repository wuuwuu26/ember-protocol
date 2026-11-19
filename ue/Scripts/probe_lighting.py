# -*- coding: utf-8 -*-
"""第一百一十轮：光影现状盘点（为安全打磨找可调项）。

查：
  1) PostProcessVolume 全部设置（Lumen/反射/曝光/Bloom/雾）
  2) 各光源的强度/颜色/阴影/动态，按 tag 分组
  3) SkyLight / DirectionalLight 配置
  4) 材质里 Roughness/Metallic 的大致分布（影响反射观感）
只读。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

out = []

# ── 1. PPV ──
out.append("═══ 1. PostProcessVolume ═══")
for a in sub.get_all_level_actors():
    if a.get_class().get_name() != "PostProcessVolume":
        continue
    loc = a.get_actor_location()
    out.append("  %s at (%.0f,%.0f,%.0f) unbound=%s" %
               (a.get_actor_label(), loc.x, loc.y, loc.z,
                a.get_editor_property("unbound")))
    st = a.get_editor_property("settings")
    # 只打印常用的、有覆盖的字段
    FIELDS = [
        ("override_auto_exposure_method", "auto_exposure_method"),
        ("override_auto_exposure_bias", "auto_exposure_bias"),
        ("override_auto_exposure_min_brightness", "auto_exposure_min_brightness"),
        ("override_auto_exposure_max_brightness", "auto_exposure_max_brightness"),
        ("override_bloom_intensity", "bloom_intensity"),
        ("override_vignette_intensity", "vignette_intensity"),
        ("override_ambient_occlusion_intensity", "ambient_occlusion_intensity"),
        ("override_ambient_occlusion_radius", "ambient_occlusion_radius"),
        ("override_dynamic_global_illumination_method", "dynamic_global_illumination_method"),
        ("override_reflection_method", "reflection_method"),
        ("override_lumen_reflection_quality", "lumen_reflection_quality"),
        ("override_lumen_scene_lighting_quality", "lumen_scene_lighting_quality"),
        ("override_lumen_final_gather_quality", "lumen_final_gather_quality"),
        ("override_screen_space_reflection_intensity", "screen_space_reflection_intensity"),
        ("override_ray_tracing_ao", "ray_tracing_ao"),
        ("override_ray_tracing_gi", "ray_tracing_gi"),
        ("override_ray_tracing_reflections", "ray_tracing_reflections"),
        ("override_motion_blur_amount", "motion_blur_amount"),
        ("override_film_grain_intensity", "film_grain_intensity"),
        ("override_chromatic_aberration_intensity", "chromatic_aberration_intensity"),
        ("override_color_saturation", "color_saturation"),
        ("override_color_contrast", "color_contrast"),
        ("override_color_gain", "color_gain"),
        ("override_color_gamma", "color_gamma"),
    ]
    for ov_name, val_name in FIELDS:
        try:
            ov = st.get_editor_property(ov_name)
            if ov:
                out.append("    %-40s = %s" % (val_name, st.get_editor_property(val_name)))
        except Exception:
            pass

# ── 2. 光源统计 ──
out.append("")
out.append("═══ 2. 光源（按类型/标签分组）═══")
groups = {}
for a in sub.get_all_level_actors():
    cls = a.get_class().get_name()
    if "Light" not in cls or cls == "SkyLight":
        continue
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        tags = []
    tag = tags[0] if tags else "(无tag)"
    groups.setdefault((cls, tag), []).append(a)

for (cls, tag), arr in sorted(groups.items()):
    a = arr[0]
    loc = a.get_actor_location()
    info = ""
    try:
        comp = a.get_light_component()
        fields = {}
        for p in ("intensity", "attenuation_radius", "light_color",
                  "cast_shadows", "mobility", "source_radius"):
            try:
                fields[p] = comp.get_editor_property(p)
            except Exception:
                pass
        info = " ".join("%s=%s" % (k, str(v)[:28]) for k, v in fields.items())
    except Exception as e:
        info = "err %s" % e
    out.append("  %-12s %-22s x%-3d 例:(%.0f,%.0f,%.0f)" %
               (cls, tag, len(arr), loc.x, loc.y, loc.z))
    out.append("      %s" % info)

# ── 3. SkyLight / Directional ──
out.append("")
out.append("═══ 3. SkyLight / DirectionalLight ═══")
for a in sub.get_all_level_actors():
    cls = a.get_class().get_name()
    if cls not in ("SkyLight", "DirectionalLight"):
        continue
    loc = a.get_actor_location()
    try:
        comp = a.get_light_component()
        parts = []
        for p in ("intensity", "light_color", "cast_shadows", "mobility",
                  "source_type", "real_time_capture", "lower_hemisphere_is_black",
                  "atmosphere_sun_light"):
            try:
                parts.append("%s=%s" % (p, comp.get_editor_property(p)))
            except Exception:
                pass
        out.append("  %s at (%.0f,%.0f,%.0f)" % (cls, loc.x, loc.y, loc.z))
        out.append("    " + " ".join(str(x)[:40] for x in parts))
    except Exception as e:
        out.append("  %s err %s" % (cls, e))

# ── 4. 雾 / 大气 ---
out.append("")
out.append("═══ 4. 雾/大气 ═══")
for a in sub.get_all_level_actors():
    cls = a.get_class().get_name()
    if any(k in cls for k in ("Fog", "Atmosphere", "Sky")):
        out.append("  %s (%s)" % (a.get_actor_label(), cls))

with open(r"C:\Users\25227\Documents\robot_game\docs\lighting_probe.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("LIGHTING_PROBE_DONE")
