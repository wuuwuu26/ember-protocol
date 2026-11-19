# -*- coding: utf-8 -*-
"""重建 M_Coolant_Fluid：深色水体 + 菲涅尔反射 + 泡沫斑块 + 细密波纹。"""
import unreal

MAT_DIR = "/Game/RobotGame/Art/Materials"
TEX_DIR = r"C:\Users\25227\Documents\robot_game\assets\tex"
MAT_PATH = f"{MAT_DIR}/M_Coolant_Fluid"
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

# ── 1. 导入贴图 ──
for fname, aname, is_norm, gray in [
    ("coolant_normal.png", "T_Coolant_N", True, False),
    ("coolant_opacity.png", "T_Coolant_O", False, True),
    ("coolant_foam.png", "T_Coolant_F", False, True),
]:
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
            tex.set_editor_property("srgb", False)
        elif gray:
            tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_GRAYSCALE)
            tex.set_editor_property("srgb", False)
        unreal.EditorAssetLibrary.save_loaded_asset(tex)

# ── 2. 材质 ──
if unreal.EditorAssetLibrary.does_asset_exist(MAT_PATH):
    unreal.EditorAssetLibrary.delete_asset(MAT_PATH)

mat = tools.create_asset("M_Coolant_Fluid", MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
if not mat:
    raise RuntimeError("材质创建失败")
mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
mat.set_editor_property("two_sided", False)


def c3(x, y, z, px, py):
    e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, px, py)
    e.set_editor_property("constant", unreal.LinearColor(x, y, z, 1.0))
    return e


def c1(v, px, py):
    e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, px, py)
    e.set_editor_property("r", v)
    return e


def tex(name, px, py):
    e = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, px, py)
    e.set_editor_property("parameter_name", name)
    e.set_editor_property("texture", unreal.EditorAssetLibrary.load_asset(f"{MAT_DIR}/{name}"))
    return e


# 顶点色泡沫（R）
vc = mel.create_material_expression(mat, unreal.MaterialExpressionVertexColor, -1250, -420)
vc_mask = mel.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -1080, -420)
vc_mask.set_editor_property("r", True)
vc_mask.set_editor_property("g", False)
vc_mask.set_editor_property("b", False)
vc_mask.set_editor_property("a", False)
mel.connect_material_expressions(vc, "", vc_mask, "")

# 泡沫纹理（平铺 + 缓慢漂移）
foam_uv = mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -1250, -240)
foam_uv.set_editor_property("u_tiling", 2.0)
foam_uv.set_editor_property("v_tiling", 2.0)
foam_pan = mel.create_material_expression(mat, unreal.MaterialExpressionPanner, -1080, -240)
foam_pan.set_editor_property("speed_x", 0.010)
foam_pan.set_editor_property("speed_y", 0.016)
mel.connect_material_expressions(foam_uv, "", foam_pan, "Coordinate")
foam_tex = tex("T_Coolant_F", -880, -240)
mel.connect_material_expressions(foam_pan, "", foam_tex, "UVs")

foam_mul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -640, -360)
mel.connect_material_expressions(vc_mask, "", foam_mul, "A")
mel.connect_material_expressions(foam_tex, "", foam_mul, "B")
foam_mask = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -470, -360)
mel.connect_material_expressions(foam_mul, "", foam_mask, "A")
mel.connect_material_expressions(c1(0.85, -640, -480), "", foam_mask, "B")

# 基础色
deep = c3(0.050, 0.180, 0.220, -640, 40)
foam_col = c3(0.42, 0.68, 0.76, -640, 160)
base_lerp = mel.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -420, 80)
mel.connect_material_expressions(deep, "", base_lerp, "A")
mel.connect_material_expressions(foam_col, "", base_lerp, "B")
mel.connect_material_expressions(foam_mask, "", base_lerp, "Alpha")
mel.connect_material_property(base_lerp, "", unreal.MaterialProperty.MP_BASE_COLOR)

# 菲涅尔天光反射
fres = mel.create_material_expression(mat, unreal.MaterialExpressionFresnel, -640, 360)
fres.set_editor_property("exponent", 2.6)
fres.set_editor_property("base_reflect_fraction", 0.06)
refl = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -420, 360)
mel.connect_material_expressions(fres, "", refl, "A")
mel.connect_material_expressions(c3(0.100, 0.260, 0.360, -640, 480), "", refl, "B")

foam_glow = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -200, 260)
mel.connect_material_expressions(foam_mask, "", foam_glow, "A")
mel.connect_material_expressions(c3(0.30, 0.95, 1.15, -420, 240), "", foam_glow, "B")

emiss_a = mel.create_material_expression(mat, unreal.MaterialExpressionAdd, -10, 330)
mel.connect_material_expressions(refl, "", emiss_a, "A")
mel.connect_material_expressions(foam_glow, "", emiss_a, "B")
emiss_b = mel.create_material_expression(mat, unreal.MaterialExpressionAdd, 160, 330)
mel.connect_material_expressions(emiss_a, "", emiss_b, "A")
mel.connect_material_expressions(c3(0.025, 0.110, 0.140, 0, 470), "", emiss_b, "B")
mel.connect_material_property(emiss_b, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

# 法线（3x 平铺 + 双速漂移）
n_uv = mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -1250, 620)
n_uv.set_editor_property("u_tiling", 4.5)
n_uv.set_editor_property("v_tiling", 4.5)
n_pan = mel.create_material_expression(mat, unreal.MaterialExpressionPanner, -1080, 620)
n_pan.set_editor_property("speed_x", 0.022)
n_pan.set_editor_property("speed_y", 0.031)
mel.connect_material_expressions(n_uv, "", n_pan, "Coordinate")
n_tex = tex("T_Coolant_N", -860, 620)
mel.connect_material_expressions(n_pan, "", n_tex, "UVs")
mel.connect_material_property(n_tex, "", unreal.MaterialProperty.MP_NORMAL)

# 透明度（静态岸线）
o_tex = tex("T_Coolant_O", -640, 860)
o_mul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -400, 860)
mel.connect_material_expressions(o_tex, "", o_mul, "A")
mel.connect_material_expressions(c1(0.85, -540, 960), "", o_mul, "B")
mel.connect_material_property(o_mul, "", unreal.MaterialProperty.MP_OPACITY)

# 粗糙度
rough = mel.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -200, 620)
mel.connect_material_expressions(c1(0.02, -400, 620), "", rough, "A")
mel.connect_material_expressions(c1(0.46, -400, 700), "", rough, "B")
mel.connect_material_expressions(foam_mask, "", rough, "Alpha")
mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

mel.connect_material_property(c1(0.0, -200, 780), "", unreal.MaterialProperty.MP_METALLIC)
mel.connect_material_property(c1(1.0, -200, 850), "", unreal.MaterialProperty.MP_SPECULAR)

mel.recompile_material(mat)
unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log("COOLANT_MAT_OK v2")

with open(r"C:\Users\25227\Documents\robot_game\docs\coolant_mat.txt", "w", encoding="utf-8") as f:
    f.write("COOLANT_MAT_OK\n")
