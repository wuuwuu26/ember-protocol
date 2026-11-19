# -*- coding: utf-8 -*-
"""把 M_SkyDome 的输出直接接到引擎自发光材质，排除节点图问题。"""
import unreal

MAT_PATH = "/Game/RobotGame/Art/Materials/M_SkyDome"
mat = unreal.EditorAssetLibrary.load_asset(MAT_PATH)
mel = unreal.MaterialEditingLibrary
mel.delete_all_material_expressions(mat)
mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
mat.set_editor_property("two_sided", True)
mat.set_editor_property("is_sky", False)
# 用一个纯白常量 3 向量，确保不是颜色空间问题
node = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, 0, 0)
node.set_editor_property("constant", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
mel.connect_material_property(node, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
# 强制写入一个明确的材质使用标记
try:
    mat.set_editor_property("used_with_static_mesh", True)
except Exception:
    pass
try:
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
except Exception:
    pass
mel.recompile_material(mat)
unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log("[白天空] M_SkyDome 已改为纯白")