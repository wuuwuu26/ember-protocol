# -*- coding: utf-8 -*-
import unreal
L = "[远景探测]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    lbl = a.get_actor_label()
    if not lbl.startswith("BG_"):
        continue
    loc = a.get_actor_location()
    sc = a.get_actor_scale3d()
    b = a.get_actor_bounds(False)
    unreal.log("%s %-18s 位置=(%.0f,%.0f,%.0f) 缩放=(%.2f,%.2f,%.2f) 包围盒中心Z=%.0f 半径=%.0f"
               % (L, lbl, loc.x, loc.y, loc.z, sc.x, sc.y, sc.z,
                  b[0].z, b[1].z))
