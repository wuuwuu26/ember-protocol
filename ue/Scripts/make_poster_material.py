# -*- coding: utf-8 -*-
"""海报材质：Unlit + Masked（一个材质 + 纹理参数，所有海报共用一个）。

为什么 Unlit：海报是"印刷品"，它的可读性来自自身色彩对比，
不该被场景的夜色/雾/点光源改亮度。用 Lit 会让墙角的告示牌黑成一块。
Masked 而不是 Translucent：海报是矩形硬边，遮罩够用，且没有排序问题。
"""
import unreal

MAT_DIR = "/Game/RobotGame/Art/Materials"
TEX_DIR = "/Game/RobotGame/Art/Materials/Posters"
NAME = "M_Poster"
path = "%s/%s" % (MAT_DIR, NAME)

for d in (TEX_DIR,):
    if not unreal.EditorAssetLibrary.does_directory_exist(d):
        unreal.EditorAssetLibrary.make_directory(d)

if unreal.EditorAssetLibrary.does_asset_exist(path):
    mat = unreal.EditorAssetLibrary.load_asset(path)
    for e in unreal.MaterialEditingLibrary.get_material_expressions(mat):
        unreal.MaterialEditingLibrary.delete_material_expression(mat, e)
    unreal.log("重建 %s" % NAME)
else:
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        NAME, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    unreal.log("新建 %s" % NAME)

mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
# ⚠️ 海报是**矩形硬边**，不需要任何透明。
#    之前用 BLEND_MASKED 并把贴图默认输出接到 OpacityMask —— 那个引脚取的是
#    **R 通道**（不是 alpha），于是深色区域被遮掉：海报看起来"透过去只剩投影"。
mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
mat.set_editor_property("two_sided", False)
mat.set_editor_property("used_with_static_lighting", False)

# 参数纹理
tex = unreal.MaterialEditingLibrary.create_material_expression(
    mat, unreal.MaterialExpressionTextureSampleParameter2D, -600, 0)
tex.set_editor_property("parameter_name", "PosterTex")
tex.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)

# 自发光 = 贴图颜色 × 亮度系数（Unlit 下自发光就是最终颜色）。
# 系数 >1：告示牌在夜景里要能读得清，同时保留印刷品的暗部层次。
mul = unreal.MaterialEditingLibrary.create_material_expression(
    mat, unreal.MaterialExpressionMultiply, -340, 0)
mul.set_editor_property("const_a", 1.0)
bright = unreal.MaterialEditingLibrary.create_material_expression(
    mat, unreal.MaterialExpressionScalarParameter, -560, 180)
bright.set_editor_property("parameter_name", "Brightness")
bright.set_editor_property("default_value", 8.0)

unreal.MaterialEditingLibrary.connect_material_expressions(
    tex, "RGB", mul, "A")
unreal.MaterialEditingLibrary.connect_material_expressions(
    bright, "", mul, "B")
unreal.MaterialEditingLibrary.connect_material_property(
    mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

# 不透明：不接 OpacityMask（接了会按 R 通道抠掉暗部）

unreal.MaterialEditingLibrary.recompile_material(mat)
unreal.EditorAssetLibrary.save_asset(path)
unreal.log("M_Poster done")
