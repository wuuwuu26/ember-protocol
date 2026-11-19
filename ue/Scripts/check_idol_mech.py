# -*- coding: utf-8 -*-
"""确认 IdolMech 雕像是否还在关卡里（第一百零九轮诊断）。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

out = []
n = 0
for a in sub.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    c = a.static_mesh_component
    m = c.get_editor_property("static_mesh") if c else None
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        tags = []
    label = a.get_actor_label()
    if "idol" in (m.get_name() if m else "").lower() or "idol" in label.lower() or any("idol" in t.lower() for t in tags):
        loc = a.get_actor_location()
        n += 1
        out.append("FOUND  %s  mesh=%s  (%.0f,%.0f,%.1f)  tags=%s" %
                   (label, m.get_name() if m else "?", loc.x, loc.y, loc.z, tags))
out.insert(0, "IdolMech actor 数量 = %d" % n)
with open(r"C:\Users\25227\Documents\robot_game\docs\idol_check.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("IDOL_CHECK_DONE  count=%d" % n)
