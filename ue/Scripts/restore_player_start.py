# -*- coding: utf-8 -*-
"""还原 PlayerStart 到原始位置 (-200, 0, 130)，朝 +X。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

starts = [a for a in actor_sub.get_all_level_actors()
          if isinstance(a, unreal.PlayerStart)]
for ps in starts:
    ps.set_actor_location(unreal.Vector(-200.0, 0.0, 130.0), False, False)
    ps.set_actor_rotation(unreal.Rotator(0.0, 0.0, 0.0), False)
    unreal.log("[ExtShot] PlayerStart 还原到 (-200, 0, 130)")

les.save_current_level()
unreal.log("RESTORE_PLAYER_DONE")
