# -*- coding: utf-8 -*-
"""把 SkyDome 移到相机前方，验证其是否参与场景渲染。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == "SkyDome":
        # 相机在玩家后上方；放到玩家与相机之间偏上，确保进入视野
        a.set_actor_location(unreal.Vector(1100, -71, 300), False, False)
        a.set_actor_scale3d(unreal.Vector(30, 30, 30))
        c = a.static_mesh_component
        c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
        c.set_editor_property("hidden_in_game", False)
        c.set_editor_property("reverse_culling", False)
        c.set_visibility(True, True)
        unreal.log("[前置穹顶] 位置=(1100,-71,300) 半径=15m")
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_all_dirty_levels()
unreal.log("[前置穹顶] 完成")