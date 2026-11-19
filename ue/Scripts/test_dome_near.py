# -*- coding: utf-8 -*-
"""临时把穹顶缩到 10m 半径并挪到玩家出生点，排查远裁剪/尺度问题。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == "SkyDome":
        a.set_actor_location(unreal.Vector(1500, 0, 130), False, False)
        a.set_actor_scale3d(unreal.Vector(20, 20, 20))
        c = a.static_mesh_component
        c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
        c.set_editor_property("hidden_in_game", False)
        c.set_visibility(True, True)
        unreal.log("[近穹顶] 位置=(1500,0,130) 半径=10m 材质=%s" % [m.get_name() if m else "None" for m in c.get_materials()])
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_all_dirty_levels()
unreal.log("[近穹顶] 完成")