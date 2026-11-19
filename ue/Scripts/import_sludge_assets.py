# -*- coding: utf-8 -*-
"""
导入毒性废液流体网格与 PBR 贴图，并创建 M_Sludge_Fluid 动态流动材质。
"""
import unreal

L = "[流体资产导入]"
MAT_DIR = "/Game/RobotGame/Art/Materials"
ENV_DIR = "/Game/RobotGame/Art/Environment"
TEX_DIR = r"C:\Users\25227\Documents\robot_game\assets\tex"
FBX_PATH = r"C:\Users\25227\Documents\robot_game\assets\out\env_sludge_pool.fbx"

# 1. 导入 4 张流体贴图
tools = unreal.AssetToolsHelpers.get_asset_tools()
textures = [
    ("sludge_diffuse.png", "T_Sludge_D", False),
    ("sludge_normal.png", "T_Sludge_N", True),
    ("sludge_emissive.png", "T_Sludge_E", False),
    ("sludge_mask.png", "T_Sludge_M", False),
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
    unreal.log(f"{L} 贴图 {aname} 导入成功")

# 2. 导入 Blender 生成的流体网格
fbx_task = unreal.AssetImportTask()
fbx_task.filename = FBX_PATH
fbx_task.destination_path = ENV_DIR
fbx_task.destination_name = "SM_Env_SludgePool"
fbx_task.automated = True
fbx_task.save = True
fbx_task.replace_existing = True

fbx_ui = unreal.FbxImportUI()
fbx_ui.import_mesh = True
fbx_ui.import_materials = False
fbx_ui.import_textures = False
fbx_ui.import_animations = False
fbx_ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
fbx_task.options = fbx_ui

tools.import_asset_tasks([fbx_task])
unreal.log(f"{L} SM_Env_SludgePool 静态网格导入成功")

# 3. 创建动态自发光流体材质 M_Sludge_Fluid
mat_path = f"{MAT_DIR}/M_Sludge_Fluid"
if unreal.EditorAssetLibrary.does_asset_exist(mat_path):
    mat = unreal.EditorAssetLibrary.load_asset(mat_path)
    for e in unreal.MaterialEditingLibrary.get_material_expressions(mat):
        unreal.MaterialEditingLibrary.delete_material_expression(mat, e)
else:
    mat = tools.create_asset("M_Sludge_Fluid", MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())

mat.set_editor_property("two_sided", False)
mel = unreal.MaterialEditingLibrary

# 贴图采样节点
def make_tex_sample(param_name, tex_asset_name, x, y):
    s = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
    s.set_editor_property("parameter_name", param_name)
    tex = unreal.EditorAssetLibrary.load_asset(f"{MAT_DIR}/{tex_asset_name}")
    if tex:
        s.set_editor_property("texture", tex)
    return s

# Panner 动态流动 UV (缓慢旋转流动)
panner = mel.create_material_expression(mat, unreal.MaterialExpressionPanner, -600, 0)
panner.set_editor_property("speed_x", 0.015)
panner.set_editor_property("speed_y", 0.025)

# Diffuse
s_diff = make_tex_sample("BaseTex", "T_Sludge_D", -300, -300)
mel.connect_material_expressions(panner, "", s_diff, "UVs")
mel.connect_material_property(s_diff, "", unreal.MaterialProperty.MP_BASE_COLOR)

# Normal
s_norm = make_tex_sample("NormalTex", "T_Sludge_N", -300, 0)
mel.connect_material_expressions(panner, "", s_norm, "UVs")
mel.connect_material_property(s_norm, "", unreal.MaterialProperty.MP_NORMAL)

# Emissive (乘以 180.0 形成高动态荧光废液 HDR 效果)
s_emiss = make_tex_sample("EmissiveTex", "T_Sludge_E", -450, 300)
mel.connect_material_expressions(panner, "", s_emiss, "UVs")
mult_emiss = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -150, 300)
c_boost = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 450)
c_boost.set_editor_property("r", 220.0)

mel.connect_material_expressions(s_emiss, "", mult_emiss, "A")
mel.connect_material_expressions(c_boost, "", mult_emiss, "B")
mel.connect_material_property(mult_emiss, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

# Roughness: 液体极度光滑 0.12
c_rough = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -150, 150)
c_rough.set_editor_property("r", 0.12)
mel.connect_material_property(c_rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

mel.recompile_material(mat)
unreal.EditorAssetLibrary.save_asset(mat_path)
unreal.log(f"{L} M_Sludge_Fluid 动态流动材质编译保存成功！")

with open(r"C:\Users\25227\Documents\robot_game\docs\sludge_imported.txt", "w", encoding="utf-8") as f:
    f.write("SLUDGE_IMPORT_DONE\n")
