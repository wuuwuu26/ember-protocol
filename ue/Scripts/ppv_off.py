# -*- coding: utf-8 -*-
import sys
import unreal
L = "[PPV开关]"
w = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "PostProcessVolume":
        continue
    a.set_editor_property("blend_weight", w)
    unreal.log("%s 后处理权重 → %.1f" % (L, w))
unreal.EditorLevelLibrary.save_current_level()
