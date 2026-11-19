# -*- coding: utf-8 -*-
"""重建 M_SkyDome：纯亮红自发光，验证穹顶是否参与主视图。"""
import unreal

MAT_PATH = "/Game/RobotGame/Art/Materials/M_SkyDome"
mat = unreal.EditorAssetLibrary.load_asset(MAT_PATH)
mel = unreal.MaterialEditingLibrary
mel.delete_all_material_expressions(mat)
mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
mat.set_editor_property("two_sided", True)
mat.set_editor_property("is_sky", False)
node = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, 0, 0)
node.set_editor_property("constant", unreal.LinearColor(4.0, 0.05, 4.0, 1.0))
mel.connect_material_property(node, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.recompile_material(mat)
unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log("[天空重建] M_SkyDome 已改为纯亮红")