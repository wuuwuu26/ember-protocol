# -*- coding: utf-8 -*-
import unreal
L = "[增益]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "PostProcessVolume":
        continue
    s = a.get_editor_property("settings")
    for n in ("color_gain", "color_saturation", "color_contrast", "color_gamma"):
        try:
            v = s.get_editor_property(n)
            unreal.log("%s %-18s type=%s repr=%s" % (L, n, type(v).__name__, repr(v)))
        except Exception as e:
            unreal.log("%s %-18s ❌ %s" % (L, n, str(e)[:80]))
