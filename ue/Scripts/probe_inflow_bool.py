# -*- coding: utf-8 -*-
"""精确读 bInflow / bStagnant 的当前值（用多种属性名尝试）。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

out = []
for a in sub.get_all_level_actors():
    if a.get_class().get_name() != "RobotCoolantField":
        continue
    out.append("=== %s ===" % a.get_actor_label())
    for key in ("bInflow", "b_inflow", "binflow", "bStagnant", "b_stagnant"):
        try:
            out.append("  %-14s = %s" % (key, a.get_editor_property(key)))
        except Exception as e:
            out.append("  %-14s err" % key)

with open(r"C:\Users\25227\Documents\robot_game\docs\inflow_bool.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("INFLOW_BOOL_DONE")
