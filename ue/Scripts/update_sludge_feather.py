# -*- coding: utf-8 -*-
"""更新 M_Sludge_Fluid 材质：支持半透明软羽化与自然融合。"""
import unreal

MAT_DIR = "/Game/RobotGame/Art/Materials"
TEX_DIR = r"C:\Users\25227\Documents\robot_game\assets\tex"
tools = unreal.AssetToolsHelpers.get_asset_tools()

# 1. 导入 Opacity 与更新后的贴图
textures = [
    ("sludge_diffuse.png", "T_Sludge_D", False),
    ("sludge_normal.png", "T_Sludge_N", True),
    ("sludge_emissive.png", "T_Sludge_E", False),
    ("sludge_opacity.png", "T_Sludge_O", False),
]

for fname, aname, is_norm in textures:
    task = unreal.AssetImportTask()
    task.filename = f"{TEX_DIR}\\{fname}"
    task.destination_path = MAT_DIR
    task.destination_name = aname
    task.automated = True
    task.save = True
    task.replace_existing = True
    tools.import_asset_tasks([task])
    
    tex = unreal.EditorAssetLibrary.load_asset(f"{MAT_DIR}/{aname}")
    if tex:
        if is_norm:
            tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        else:
            tex.set_editor_property("srgb", not is_norm)
        unreal.EditorAssetLibrary.save_loaded_asset(tex)

# 2. 重构 M_Sludge_Fluid：设置为 Translucent (半透明混合)
mat_path = f"{MAT_DIR}/M_Sludge_Fluid"
mat = unreal.EditorAssetLibrary.load_asset(mat_path)
mel = unreal.MaterialEditingLibrary

for e in mel.get_material_expressions(mat):
    mel.delete_material_expression(mat, e)

# 半透明无光照/高光
mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
mat.set_editor_property("two_sided", False)

def make_tex_sample(param_name, tex_asset_name, x, y):
    s = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
    s.set_editor_property("parameter_name", param_name)
    tex = unreal.EditorAssetLibrary.load_asset(f"{MAT_DIR}/{tex_asset_name}")
    if tex:
        s.set_editor_property("texture", tex)
    return s

panner = mel.create_material_expression(mat, unreal.MaterialExpressionPanner, -600, 0)
panner.set_editor_property("speed_x", 0.012)
panner.set_editor_property("speed_y", 0.018)

# BaseColor
s_diff = make_tex_sample("BaseTex", "T_Sludge_D", -300, -300)
mel.connect_material_expressions(panner, "", s_diff, "UVs")
mel.connect_material_property(s_diff, "", unreal.MaterialProperty.MP_BASE_COLOR)

# Normal
s_norm = make_tex_sample("NormalTex", "T_Sludge_N", -300, 0)
mel.connect_material_expressions(panner, "", s_norm, "UVs")
mel.connect_material_property(s_norm, "", unreal.MaterialProperty.MP_NORMAL)

# Emissive
s_emiss = make_tex_sample("EmissiveTex", "T_Sludge_E", -450, 300)
mel.connect_material_expressions(panner, "", s_emiss, "UVs")
mult_emiss = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -150, 300)
c_boost = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 450)
c_boost.set_editor_property("r", 160.0)
mel.connect_material_expressions(s_emiss, "", mult_emiss, "A")
mel.connect_material_expressions(c_boost, "", mult_emiss, "B")
mel.connect_material_property(mult_emiss, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

# Opacity (静态羽化遮罩，不流动，使边缘始终平滑贴合地面)
s_opac = make_tex_sample("OpacityTex", "T_Sludge_O", -200, 600)
mel.connect_material_property(s_opac, "", unreal.MaterialProperty.MP_OPACITY)

# Roughness
c_rough = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -150, 150)
c_rough.set_editor_property("r", 0.08)
mel.connect_material_property(c_rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

mel.recompile_material(mat)
unreal.EditorAssetLibrary.save_asset(mat_path)
unreal.log("M_Sludge_Fluid 透明羽化材质更新成功！")

with open(r"C:\Users\25227\Documents\robot_game\docs\sludge_feathered.txt", "w", encoding="utf-8") as f:
    f.write("SLUDGE_FEATHERED_DONE\n")
