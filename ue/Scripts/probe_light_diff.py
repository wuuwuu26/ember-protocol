# -*- coding: utf-8 -*-
"""逐盏量灯的"有效性"：把灯挪到地面正上方 100cm，如果画面还是黑的，
说明灯压根没被渲染（而非强度不够）。

这里不做渲染，只对比两组灯的关键属性差异：
  原有 (0,0,0) 附近的灯 vs 扩建灯
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)

out = []


def dump(a, label):
    c = a.point_light_component
    loc = a.get_actor_location()

    def g(p):
        try:
            return str(c.get_editor_property(p))
        except Exception:
            return "-"
    out.append("%-24s (%.0f,%.0f,%.0f)" % (label, loc.x, loc.y, loc.z))
    out.append("    intensity=%s  radius=%s  src_radius=%s"
               % (g("intensity"), g("attenuation_radius"),
                  g("source_radius")))
    out.append("    mobility=%s  visible=%s  cast_shadow=%s  affect=%s"
               % (g("mobility"), g("visible"), g("cast_shadows"),
                  g("affects_world")))
    out.append("    light_color=%s  use_inv_sq=%s  shadow_res=%s"
               % (g("light_color"), g("use_inverse_squared_falloff"),
                  g("shadow_map_resolution_scale")))


ext = []
orig = []
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if a.get_class().get_name() != "PointLight":
        continue
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        tags = []
    if any(t.startswith("ExtLight_") for t in tags):
        ext.append((tags, a))
    else:
        orig.append(a)

out.append("扩建 %d 盏 / 原有 %d 盏" % (len(ext), len(orig)))
out.append("")
out.append("== 原有灯（参照）==")
for a in orig[:2]:
    dump(a, a.get_actor_label())
out.append("")
out.append("== 扩建灯 ==")
for tags, a in ext[:3]:
    dump(a, tags[-1])

with open(r"C:\Users\25227\Documents\robot_game\docs\ext_lightdiff.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("LIGHTDIFF_DONE")
