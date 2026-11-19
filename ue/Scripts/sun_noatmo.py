# -*- coding: utf-8 -*-
"""在**关卡里**关掉平行光的"大气太阳光"。

运行时改 bAtmosphereSunLight 不够：SkyAtmosphere 在初始化时就把这盏灯
记成了自己的太阳，之后每帧对它的光做一次大气透过率（低角度 → 强暖色），
所以不管把 light_color 设成多冷的颜色，出来的光都是暖的。
必须在关卡数据里就关掉，让大气层从不关联它。
"""
import unreal
L = "[关大气太阳]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
n = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "DirectionalLight":
        continue
    c = a.get_editor_property("light_component")
    try:
        c.set_editor_property("atmosphere_sun_light", False)
        n += 1
    except Exception as e:
        unreal.log("%s ⚠️ %s" % (L, str(e)[:60]))
    # 回读
    try:
        unreal.log("%s 大气太阳光=%s 色=%s" % (
            L, c.get_editor_property("atmosphere_sun_light"),
            c.get_editor_property("light_color")))
    except Exception:
        pass
# 顺便把 SkyAtmosphere 也关掉（它没有太阳之后只会渲染一片黑）
m = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() == "SkyAtmosphere":
        a.set_editor_property("is_temporarily_hidden_in_editor", True)
        m += 1
unreal.EditorLevelLibrary.save_current_level()
unreal.log("%s 处理 %d 盏灯，%d 个大气" % (L, n, m))
