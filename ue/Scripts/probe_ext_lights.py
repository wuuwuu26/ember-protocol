# -*- coding: utf-8 -*-
"""检查扩建灯的实际属性：是否启用、强度、半径、是否被阴影挡住。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)

out = []
n = 0
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        continue
    if not any(t.startswith("ExtLight_") for t in tags):
        continue
    n += 1
    c = a.point_light_component
    loc = a.get_actor_location()
    if n <= 6:
        def g(p, d="?"):
            try:
                return str(c.get_editor_property(p))
            except Exception as e:
                return "err:%s" % e
        out.append("%s (%.0f,%.0f,%.0f)" % (tags[-1], loc.x, loc.y, loc.z))
        out.append("   intensity=%s radius=%s visible=%s enabled=%s mobility=%s"
                   % (g("intensity"), g("attenuation_radius"),
                      g("visible"), g("enabled"), g("mobility")))
        out.append("   color=%s cast_shadows=%s"
                   % (g("light_color"), g("cast_shadows")))

out.insert(0, "总灯数 %d" % n)

# 对比：原有 PointLight 的属性（应该在这关里是好的）
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        tags = []
    if a.get_class().get_name() != "PointLight":
        continue
    if any(t.startswith("ExtLight_") for t in tags):
        continue
    c = a.point_light_component
    loc = a.get_actor_location()
    out.append("")
    out.append("== 原有 PointLight 参考 ==")
    out.append("(%.0f,%.0f,%.0f) intensity=%s radius=%s"
               % (loc.x, loc.y, loc.z,
                  c.get_editor_property("intensity"),
                  c.get_editor_property("attenuation_radius")))
    break

with open(r"C:\Users\25227\Documents\robot_game\docs\ext_lightcheck.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("EXT_LIGHTCHECK_DONE")
