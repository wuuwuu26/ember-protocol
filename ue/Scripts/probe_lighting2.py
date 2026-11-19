# -*- coding: utf-8 -*-
"""光源细节探针（修正 get_light_component 的 API 名）。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

out = []


def comp_of(a):
    """取光源组件：不同类型对应不同属性名。"""
    cls = a.get_class().get_name()
    attr = {
        "PointLight": "point_light_component",
        "SpotLight": "spot_light_component",
        "DirectionalLight": "directional_light_component",
        "SkyLight": "light_component",
        "RectLight": "rect_light_component",
    }.get(cls)
    if attr:
        try:
            return a.get_editor_property(attr)
        except Exception:
            pass
    # 兜底：遍历组件找 LightComponentBase 子类
    try:
        for c in a.get_components_by_class(unreal.LightComponentBase):
            return c
    except Exception:
        pass
    return None


def dump_light(a, title=None):
    c = comp_of(a)
    loc = a.get_actor_location()
    out.append("  %s %s at (%.0f,%.0f,%.0f)" %
               (a.get_class().get_name(), title or a.get_actor_label(), loc.x, loc.y, loc.z))
    if not c:
        out.append("    !! 组件取不到")
        return
    for p in ("intensity", "attenuation_radius", "light_color", "cast_shadows",
              "mobility", "source_radius", "volumetric_scattering_intensity",
              "indirect_lighting_intensity", "inverse_exposure_blend"):
        try:
            out.append("      %-32s = %s" % (p, c.get_editor_property(p)))
        except Exception:
            pass
    # 聚光灯额外
    try:
        out.append("      %-32s = %s" % ("inner_cone_angle", c.get_editor_property("inner_cone_angle")))
        out.append("      %-32s = %s" % ("outer_cone_angle", c.get_editor_property("outer_cone_angle")))
    except Exception:
        pass
    # 平行光额外
    for p in ("atmosphere_sun_light", "dynamic_shadow_distance_movable_light"):
        try:
            out.append("      %-32s = %s" % (p, c.get_editor_property(p)))
        except Exception:
            pass
    # 天光额外
    for p in ("source_type", "real_time_capture", "lower_hemisphere_is_black",
              "sky_distance", "cubemap"):
        try:
            v = c.get_editor_property(p)
            out.append("      %-32s = %s" % (p, str(v)[:60]))
        except Exception:
            pass


out.append("═══ DirectionalLight ═══")
for a in sub.get_all_level_actors():
    if a.get_class().get_name() == "DirectionalLight":
        dump_light(a)

out.append("")
out.append("═══ SkyLight ═══")
for a in sub.get_all_level_actors():
    if a.get_class().get_name() == "SkyLight":
        dump_light(a)

out.append("")
out.append("═══ 按 (类型,tag) 分组：各组首个样本 ═══")
seen = set()
for a in sub.get_all_level_actors():
    cls = a.get_class().get_name()
    if cls not in ("PointLight", "SpotLight"):
        continue
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        tags = []
    key = (cls, tags[0] if tags else "(无tag)")
    if key in seen:
        continue
    seen.add(key)
    dump_light(a, "%s [%s]" % (a.get_actor_label(), key[1]))

out.append("")
out.append("═══ ExponentialHeightFog ═══")
for a in sub.get_all_level_actors():
    if a.get_class().get_name() != "ExponentialHeightFog":
        continue
    c = a.get_editor_property("component")
    for p in ("fog_density", "fog_height_falloff", "fog_inscattering_luminance",
              "fog_max_opacity", "start_distance", "fog_radial_inscattering"):
        try:
            out.append("  %-30s = %s" % (p, c.get_editor_property(p)))
        except Exception:
            pass

with open(r"C:\Users\25227\Documents\robot_game\docs\lighting_probe2.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("LIGHTING_PROBE2_DONE")
