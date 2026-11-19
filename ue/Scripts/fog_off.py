# -*- coding: utf-8 -*-
import sys
import unreal
L = "[体积雾]"
off = (sys.argv[1] == "1") if len(sys.argv) > 1 else True
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
n = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if "Fog" not in a.get_class().get_name():
        continue
    c = a.get_editor_property("component")
    c.set_editor_property("enable_volumetric_fog", not off)
    c.set_editor_property("fog_density", 0.002 if off else 0.006)
    n += 1
unreal.EditorLevelLibrary.save_current_level()
unreal.log("%s 体积雾关闭=%s（%d 个）" % (L, off, n))
