# -*- coding: utf-8 -*-
"""把 4 个剧毒废液池缩小到 0.72 倍，避免像“地板破洞”。"""
import unreal

unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
count = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() == "RobotHazardSludge":
        a.set_actor_scale3d(unreal.Vector(0.72, 0.72, 0.72))
        count += 1

unreal.EditorLevelLibrary.save_current_level()
unreal.log(f"SLUDGE_SCALED {count}")
with open(r"C:\Users\25227\Documents\robot_game\docs\sludge_scaled.txt", "w", encoding="utf-8") as f:
    f.write(f"scaled={count}\nSLUDGE_SCALED_OK\n")
