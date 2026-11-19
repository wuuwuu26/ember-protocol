# -*- coding: utf-8 -*-
import unreal
L = "[PPV]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
n = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "PostProcessVolume":
        continue
    n += 1
    s = a.get_editor_property("settings")
    try:
        m = s.get_editor_property("auto_exposure_method")
        mn = s.get_editor_property("auto_exposure_min_brightness")
        mx = s.get_editor_property("auto_exposure_max_brightness")
        bias = s.get_editor_property("auto_exposure_bias")
    except Exception as e:
        m, mn, mx, bias = "?", 0, 0, 0
    unreal.log("%s #%d label=%s unbound=%s blend=%.2f pri=%.1f 方法=%s min=%.2f max=%.2f bias=%.2f"
               % (L, n, a.get_actor_label(), a.get_editor_property("unbound"),
                  a.get_editor_property("blend_weight"),
                  a.get_editor_property("priority"), m, mn, mx, bias))
unreal.log("%s 共 %d 个后处理体" % (L, n))
