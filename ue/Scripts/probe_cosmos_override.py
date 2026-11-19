# -*- coding: utf-8 -*-
"""精查：Cosmos 贴墙道具是否被 apply_polyhaven.py 误改材质。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

out = []
for a in sub.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        tags = []
    if "CosmosProp" not in tags:
        continue
    c = a.static_mesh_component
    m = c.get_editor_property("static_mesh") if c else None
    ov = c.get_editor_property("override_materials")
    names = [x.get_name() if x else "None" for x in ov]
    loc = a.get_actor_location()
    out.append("%-22s mesh=%-42s tags=%s" %
               (a.get_actor_label(), m.get_name() if m else "?", tags))
    out.append("      ov=%s" % names)

with open(r"C:\Users\25227\Documents\robot_game\docs\cosmos_override.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("COSMOS_OV_DONE")
