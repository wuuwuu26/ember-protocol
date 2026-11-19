# -*- coding: utf-8 -*-
"""清掉远景（摆放方案未收敛，先把场地恢复干净）。"""
import unreal
L = "[清远景]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
n = 0
for a in list(unreal.EditorLevelLibrary.get_all_level_actors()):
    if a.get_actor_label().startswith("BG_"):
        sub.destroy_actor(a)
        n += 1
unreal.EditorLevelLibrary.save_current_level()
unreal.log("%s 删除 %d 个" % (L, n))
