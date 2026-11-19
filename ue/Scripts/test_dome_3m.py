# -*- coding: utf-8 -*-
"""把穹顶放到相机正前方 3m，验证是否被深度/裁剪遮挡。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == "SkyDome":
        a.set_actor_location(unreal.Vector(1500, 0, 130), False, False)
        a.set_actor_scale3d(unreal.Vector(3, 3, 3))
        c = a.static_mesh_component
        c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
        c.set_editor_property("hidden_in_game", False)
        c.set_editor_property("reverse_culling", True)
        c.set_visibility(True, True)
        unreal.log("[近距离] 穹顶位置=(1500,0,130) 半径=1.5m 缩放=3")
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_all_dirty_levels()
unreal.log("[近距离] 完成")