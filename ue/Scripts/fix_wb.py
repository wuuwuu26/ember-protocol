# -*- coding: utf-8 -*-
"""修正后处理白平衡。

诊断过程：太阳 9000lux 冷白（已确认运行时参数）、天光关掉无变化、
装饰点光降到 800cd 无变化 —— 画面 R/B 始终 1.30。
说明偏色不在任何一盏灯上，而在**色调映射的白平衡**：
PPV 的 white_temp = 5900（默认 6500），值越低画面越暖。
"""
import unreal
L = "[白平衡]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
n = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "PostProcessVolume":
        continue
    s = a.get_editor_property("settings")
    try:
        s.set_editor_property("override_white_temp", True)
        s.set_editor_property("white_temp", 5850.0)   # 中性点（大气层已关）
        s.set_editor_property("override_white_tint", True)
        s.set_editor_property("white_tint", 0.0)
        # 色相增益也归中性（关卡里残留 (1.03,1.00,0.96) 是暖偏置）
        s.set_editor_property("override_color_gain", True)
        s.set_editor_property("color_gain", unreal.Vector4(1.0, 1.0, 1.0, 1.0))
        a.set_editor_property("settings", s)
        n += 1
        unreal.log("%s 白平衡 → 4600K，ColorGain 归中性" % L)
    except Exception as e:
        unreal.log("%s ⚠️ %s" % (L, str(e)[:70]))
unreal.EditorLevelLibrary.save_current_level()
unreal.log("%s 修正 %d 个后处理体" % (L, n))
