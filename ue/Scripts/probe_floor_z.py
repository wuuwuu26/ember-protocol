# -*- coding: utf-8 -*-
"""查地面块的实际 Z 与网格名，确认接缝原因。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)

out = []
zs = {}
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    c = a.static_mesh_component
    m = c.get_editor_property("static_mesh") if c else None
    if not m:
        continue
    nm = m.get_name()
    if "floor" not in nm.lower():
        continue
    loc = a.get_actor_location()
    sc = a.get_actor_scale3d()
    zs.setdefault((round(loc.z, 2), round(sc.x, 3), round(sc.z, 3)), 0)
    zs[(round(loc.z, 2), round(sc.x, 3), round(sc.z, 3))] += 1

out.append("地面块 Z 分布 (z, scaleX, scaleZ) -> count")
for k, v in sorted(zs.items()):
    out.append("  %s -> %d" % (k, v))

with open(r"C:\Users\25227\Documents\robot_game\docs\ext_floor.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("EXT_FLOOR_DONE")
