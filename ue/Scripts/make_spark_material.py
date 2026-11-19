# -*- coding: utf-8 -*-
"""新建残破电火花粒子专用发光材质 M_Spark_Flash（Unlit 电光白/电光青极亮发光）。"""
import unreal

MAT_DIR = "/Game/RobotGame/Art/Materials"
NAME = "M_Spark_Flash"
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

# 电光青白：(450.0, 520.0, 700.0) 极亮纯白核 + 耀眼电弧青蓝光晕
col = unreal.MaterialEditingLibrary.create_material_expression(
    mat, unreal.MaterialExpressionConstant3Vector, -420, 0)
col.set_editor_property("constant", unreal.LinearColor(450.0, 520.0, 700.0, 1.0))

unreal.MaterialEditingLibrary.connect_material_property(
    col, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
unreal.MaterialEditingLibrary.recompile_material(mat)
unreal.EditorAssetLibrary.save_asset(path)

with open(r"C:\Users\25227\Documents\robot_game\docs\spark_mat.txt", "w") as f:
    f.write("M_Spark_Flash created\nSPARKMAT_DONE\n")
unreal.log("M_Spark_Flash done")
