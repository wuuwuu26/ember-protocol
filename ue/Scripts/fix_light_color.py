# -*- coding: utf-8 -*-
"""统一场景灯光色温 —— 解决"整个画面一片橙红"。

诊断：点光是早期用钠灯（约 2000K 橙）搭的，relight.py 只改了强度没改色温，
于是 15 盏橙光叠在一起，把地板、机体、墙全部染成橙色。
"""
import unreal
L = "[灯光色温]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")

PT_TEMP = 5200.0
PT_INT = 1400.0
SPOT_TEMP = 5000.0

n_p = n_s = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    cn = a.get_class().get_name()
    if cn == "PointLight":
        c = a.get_editor_property("point_light_component")
        if not c:
            continue
        c.set_editor_property("use_temperature", True)
        c.set_editor_property("temperature", PT_TEMP)
        c.set_editor_property("intensity", PT_INT)
        n_p += 1
    elif cn == "SpotLight":
        c = a.get_editor_property("spot_light_component")
        if not c:
            continue
        c.set_editor_property("use_temperature", True)
        c.set_editor_property("temperature", SPOT_TEMP)
        n_s += 1
unreal.log("%s 点光 %d 盏 → %.0fK / %.0fcd；投光 %d 盏 → %.0fK"
           % (L, n_p, PT_TEMP, PT_INT, n_s, SPOT_TEMP))
unreal.EditorLevelLibrary.save_current_level()
