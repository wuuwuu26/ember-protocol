# -*- coding: utf-8 -*-
"""找场景里所有"长方形水渠/水槽"几何（含 StaticMesh，不只 RobotBasin）。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

out = []
# 关键词：渠/槽/沟/冷却/水/池/液
KW = ("channel", "canal", "trough", "gutter", "trench", "water", "pool",
      "basin", "coolant", "fluid", "spill", "drain", "pipe")

for a in sub.get_all_level_actors():
    cls = a.get_class().get_name()
    label = a.get_actor_label()
    mesh_name = ""
    if cls == "StaticMeshActor":
        c = a.static_mesh_component
        m = c.get_editor_property("static_mesh") if c else None
        mesh_name = m.get_name() if m else ""
    blob = (label + " " + mesh_name).lower()
    if not any(k in blob for k in KW):
        continue
    loc = a.get_actor_location()
    try:
        org, ext = a.get_actor_bounds(False)
        dims = (round(ext.x * 2), round(ext.y * 2), round(ext.z * 2))
    except Exception:
        dims = (0, 0, 0)
    out.append("%-22s %-30s mesh=%-28s (%.0f,%.0f,%.0f) 尺寸=%s" % (
        cls, label[:30], mesh_name[:28], loc.x, loc.y, loc.z, dims))

out.insert(0, "共 %d 个" % len(out))
with open(r"C:\Users\25227\Documents\robot_game\docs\all_water.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("ALL_WATER_DONE")
