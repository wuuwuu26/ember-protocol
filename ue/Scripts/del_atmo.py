# -*- coding: utf-8 -*-
import unreal
L = "[删大气]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
n = 0
for a in list(unreal.EditorLevelLibrary.get_all_level_actors()):
    if a.get_class().get_name() == "SkyAtmosphere":
        sub.destroy_actor(a)
        n += 1
unreal.EditorLevelLibrary.save_current_level()
unreal.log("%s 删除 %d 个 SkyAtmosphere" % (L, n))
