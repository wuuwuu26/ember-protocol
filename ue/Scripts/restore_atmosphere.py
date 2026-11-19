# -*- coding: utf-8 -*-
import unreal
L = "[大气恢复]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
has = any(a.get_class().get_name() == "SkyAtmosphere"
          for a in unreal.EditorLevelLibrary.get_all_level_actors())
if not has:
    a = sub.spawn_actor_from_class(unreal.SkyAtmosphere,
                                   unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    unreal.log("%s 已重建 SkyAtmosphere" % L)
unreal.EditorLevelLibrary.save_current_level()
