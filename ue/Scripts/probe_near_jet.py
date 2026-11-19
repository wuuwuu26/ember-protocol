# -*- coding: utf-8 -*-
"""列出 (120,300) 注水落点附近的所有 actor（含隐藏的），找那两个浅色半圆的真身。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

out = []
for a in sub.get_all_level_actors():
    loc = a.get_actor_location()
    if abs(loc.x - 120) > 260 or abs(loc.y - 300) > 260:
        continue
    cls = a.get_class().get_name()
    label = a.get_actor_label()
    vis = ""
    try:
        c = a.get_component_by_class(unreal.PrimitiveComponent)
        if c:
            vis = "visible=%s" % c.is_visible()
    except Exception:
        pass
    out.append("%-24s %-28s (%.0f,%.0f,%.1f) %s" % (
        cls, label, loc.x, loc.y, loc.z, vis))

out.insert(0, "附近 actor 共 %d 个" % len(out))
with open(r"C:\Users\25227\Documents\robot_game\docs\near_jet.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("NEAR_JET_DONE")
