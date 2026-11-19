# -*- coding: utf-8 -*-
"""删掉 SkyAtmosphere —— 这台机器上它不工作，但仍在渲染一层暗红背景，
并且被天光捕获成橙色环境光（整个画面发橙的元凶之一）。"""
import unreal
L = "[大气]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
n = 0
for a in list(unreal.EditorLevelLibrary.get_all_level_actors()):
    if a.get_class().get_name() == "SkyAtmosphere":
        sub.destroy_actor(a)
        n += 1
unreal.log("%s 删除 SkyAtmosphere %d 个" % (L, n))
unreal.EditorLevelLibrary.save_current_level()
