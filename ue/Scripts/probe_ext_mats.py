# -*- coding: utf-8 -*-
"""查墙段、门框、龙门架、立柱的材质覆盖，给扩建脚本补上同样的设置。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)

want = ("wall_segment", "wall_corner", "pillar", "gantry", "doorframe", "catwalk")
seen = {}
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    c = a.static_mesh_component
    m = c.get_editor_property("static_mesh") if c else None
    if not m:
        continue
    nm = m.get_name().lower()
    hit = None
    for w in want:
        if w in nm:
            hit = w
            break
    if not hit or hit in seen:
        continue
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        tags = []
    if "ExtRegion" in tags:
        continue      # 只看原有的
    ov = c.get_editor_property("override_materials")
    loc = a.get_actor_location()
    seen[hit] = "%-14s at (%.0f,%.0f)  overrides=%s" % (
        hit, loc.x, loc.y, [x.get_name() if x else "None" for x in ov])

with open(r"C:\Users\25227\Documents\robot_game\docs\ext_mats.txt", "wb") as f:
    f.write("\n".join(seen[k] for k in sorted(seen)).encode("utf-8"))
unreal.log("EXTMATS_DONE")
