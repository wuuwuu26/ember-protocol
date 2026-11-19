# -*- coding: utf-8 -*-
"""把后处理体的曝光直接写死在关卡里（手动模式 + bias -3.0）。
运行时 FixLevelLighting 也做同样的事，但 relight.py 会把关卡里的值改回
Histogram/EV13.6 —— 两边打架时以关卡数据为准更可靠。"""
import unreal
L = "[PPV修正]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
n = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "PostProcessVolume":
        continue
    a.set_editor_property("unbound", True)
    a.set_editor_property("blend_weight", 1.0)
    a.set_editor_property("priority", 100.0)
    s = a.get_editor_property("settings")
    s.set_editor_property("override_auto_exposure_method", True)
    s.set_editor_property("auto_exposure_method",
                          unreal.AutoExposureMethod.AEM_MANUAL)
    s.set_editor_property("override_auto_exposure_bias", True)
    s.set_editor_property("auto_exposure_bias", 5.6)
    s.set_editor_property("override_bloom_intensity", True)
    s.set_editor_property("bloom_intensity", 0.5)
    s.set_editor_property("override_bloom_threshold", True)
    s.set_editor_property("bloom_threshold", 0.9)
    a.set_editor_property("settings", s)
    n += 1
unreal.EditorLevelLibrary.save_current_level()
unreal.log("%s 已修正 %d 个后处理体" % (L, n))
