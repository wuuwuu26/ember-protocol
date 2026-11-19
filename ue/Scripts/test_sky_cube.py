# -*- coding: utf-8 -*-
"""把 SkyDome 换成 Cube，排查球面剔除/网格问题。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)
cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
unreal.log("[立方天空] cube=%s" % (cube.get_name() if cube else "None"))
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == "SkyDome":
        c = a.static_mesh_component
        c.set_static_mesh(cube)
        c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
        c.set_editor_property("hidden_in_game", False)
        c.set_editor_property("reverse_culling", False)
        c.set_visibility(True, True)
        a.set_actor_location(unreal.Vector(1100, -71, 300), False, False)
        a.set_actor_scale3d(unreal.Vector(30, 30, 30))
        unreal.log("[立方天空] 已换成 Cube")
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_all_dirty_levels()
unreal.log("[立方天空] 完成")