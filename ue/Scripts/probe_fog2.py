# -*- coding: utf-8 -*-
import unreal
L = "[体积雾]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if "Fog" not in a.get_class().get_name():
        continue
    c = a.get_editor_property("component")
    for n in dir(c):
        if "volumetric" not in n.lower():
            continue
        try:
            v = c.get_editor_property(n)
            unreal.log("%s %-38s = %s" % (L, n, v))
        except Exception:
            pass
