# -*- coding: utf-8 -*-
"""创建双面 Unlit IsSky 测试材质并替换穹顶。"""
import unreal

MAT_DIR = "/Game/RobotGame/Art/Materials"
NAME = "M_SkyDomeSimple"
PATH = MAT_DIR + "/" + NAME
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"

if unreal.EditorAssetLibrary.does_asset_exist(PATH):
    unreal.EditorAssetLibrary.delete_asset(PATH)
at = unreal.AssetToolsHelpers.get_asset_tools()
mat = at.create_asset(NAME, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
mat.set_editor_property("two_sided", True)
mat.set_editor_property("is_sky", True)
mel = unreal.MaterialEditingLibrary
node = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, 0, 0)
node.set_editor_property("constant", unreal.LinearColor(0.25, 0.35, 0.55, 1.0))
mel.connect_material_property(node, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.recompile_material(mat)
unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log("[穹顶简单测试] 材质已建: %s" % PATH)

unreal.EditorLevelLibrary.load_level(LEVEL)
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == "SkyDome":
        a.static_mesh_component.set_material(0, mat)
        unreal.log("[穹顶简单测试] 已替换穹顶材质")
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_all_dirty_levels()
unreal.log("[穹顶简单测试] 完成")