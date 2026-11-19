# -*- coding: utf-8 -*-
"""列出关卡里悬空/可疑的静态网格演员，排查天空里的黑色浮块。"""
import unreal

unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")

rows = []
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    try:
        loc = a.get_actor_location()
    except Exception:
        continue
    if loc.z < 250.0:
        continue
    label = a.get_actor_label()
    cls = a.get_class().get_name()
    rows.append("%-28s %-22s z=%.0f (%.0f,%.0f,%.0f)"
                % (label[:28], cls[:22], loc.z, loc.x, loc.y, loc.z))

with open(r"C:\Users\25227\Documents\robot_game\docs\floating_actors.txt", "w") as f:
    f.write("\n".join(sorted(rows)))
    f.write("\nFLOAT_DONE\n")
