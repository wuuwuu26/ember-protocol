# -*- coding: utf-8 -*-
"""查清楚新区域里立柱/围墙/龙门架/雕像的占位，给道具微调做依据。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)

out = []
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    c = a.static_mesh_component
    m = c.get_editor_property("static_mesh") if c else None
    if not m:
        continue
    nm = m.get_name().lower()
    loc = a.get_actor_location()
    if not (2200 <= loc.x <= 5600):
        continue
    if any(k in nm for k in ("wall", "pillar", "gantry", "doorframe")):
        try:
            tags = [str(t) for t in a.get_editor_property("tags")]
        except Exception:
            tags = []
        out.append("%-22s (%.0f, %.0f, %.0f)  %s" %
                   (m.get_name(), loc.x, loc.y, loc.z, ",".join(tags)))

out.sort()
with open(r"C:\Users\25227\Documents\robot_game\docs\ext_occupancy.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("OCCUPANCY_DONE  %d" % len(out))
