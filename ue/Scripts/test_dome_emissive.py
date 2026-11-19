# -*- coding: utf-8 -*-
"""临时把天空穹顶换成引擎自发光材质，做可见性隔离测试。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)
mat = unreal.EditorAssetLibrary.load_asset("/Engine/EngineMaterials/EmissiveMeshMaterial")
unreal.log("[穹顶测试] 材质=%s" % (mat.get_name() if mat else "None"))
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == "SkyDome":
        a.static_mesh_component.set_material(0, mat)
        unreal.log("[穹顶测试] 已替换 SkyDome 材质")
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_all_dirty_levels()
unreal.log("[穹顶测试] 完成")