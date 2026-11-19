# -*- coding: utf-8 -*-
"""测试：关闭 IsSky 后，双面 Unlit 穹顶是否进入主视图。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
MAT_PATH = "/Game/RobotGame/Art/Materials/M_SkyDomeSimple"
mat = unreal.EditorAssetLibrary.load_asset(MAT_PATH)
mat.set_editor_property("is_sky", False)
mat.set_editor_property("two_sided", True)
unreal.MaterialEditingLibrary.recompile_material(mat)
unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log("[关闭IsSky] 材质已更新")

unreal.EditorLevelLibrary.load_level(LEVEL)
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == "SkyDome":
        c = a.static_mesh_component
        c.set_material(0, mat)
        try:
            c.set_editor_property("visible_in_real_time_sky_captures", True)
        except Exception as e:
            unreal.log("[关闭IsSky] 组件天空捕获标记失败: %s" % str(e)[:80])
        unreal.log("[关闭IsSky] 穹顶材质已替换")
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_all_dirty_levels()
unreal.log("[关闭IsSky] 完成")