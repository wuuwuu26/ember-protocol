# -*- coding: utf-8 -*-
"""新建废料核心拾取物专用自发光材质 M_Salvage_Core（Unlit 金琥珀色高动态发光）。"""
import unreal

MAT_DIR = "/Game/RobotGame/Art/Materials"
NAME = "M_Salvage_Core"
path = "%s/%s" % (MAT_DIR, NAME)

if unreal.EditorAssetLibrary.does_asset_exist(path):
    mat = unreal.EditorAssetLibrary.load_asset(path)
    for e in unreal.MaterialEditingLibrary.get_material_expressions(mat):
        unreal.MaterialEditingLibrary.delete_material_expression(mat, e)
    unreal.log("更新 %s" % NAME)
else:
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        NAME, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    unreal.log("新建 %s" % NAME)

mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
mat.set_editor_property("two_sided", False)

# 黄金琥珀色 HDR 自发光：白核 (280, 140, 20)
# 在 Manual 曝光 Bias=3.6 下呈现耀眼的金色晶体核心与柔和金晕
col = unreal.MaterialEditingLibrary.create_material_expression(
    mat, unreal.MaterialExpressionConstant3Vector, -420, 0)
col.set_editor_property("constant", unreal.LinearColor(280.0, 140.0, 20.0, 1.0))

unreal.MaterialEditingLibrary.connect_material_property(
    col, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
unreal.MaterialEditingLibrary.recompile_material(mat)
unreal.EditorAssetLibrary.save_asset(path)

with open(r"C:\Users\25227\Documents\robot_game\docs\salvage_mat.txt", "w") as f:
    f.write("M_Salvage_Core created\nSALVAGEMAT_DONE\n")
unreal.log("M_Salvage_Core done")
