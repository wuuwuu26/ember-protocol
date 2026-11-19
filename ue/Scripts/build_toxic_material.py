# -*- coding: utf-8 -*-
"""重建剧毒废液材质 M_Toxic_Fluid —— 修掉“地板黑洞 + 绿芯”的错误观感。

根本原因：T_Sludge_D / T_Sludge_E 是“黑底 + 中间一团绿”的贴图，
直接铺满整块池面时，黑色底把地板盖成一块硬黑圆斑，看起来像穿了个洞。

这里改用**世界坐标径向遮罩**（不依赖网格 UV）：
    中心 → 亮墨绿；边缘 → 深绿并羽化透明
配菲涅尔油膜反光，读成黏稠发光的废液，而不是洞。
"""
import unreal

MAT_DIR = "/Game/RobotGame/Art/Materials"
MAT_PATH = f"{MAT_DIR}/M_Toxic_Fluid"
POOL_RADIUS = 137.0  # 池网格半径 190cm × 关卡缩放 0.72
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

if unreal.EditorAssetLibrary.does_asset_exist(MAT_PATH):
    unreal.EditorAssetLibrary.delete_asset(MAT_PATH)

mat = tools.create_asset("M_Toxic_Fluid", MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
if not mat:
    raise RuntimeError("创建 M_Toxic_Fluid 失败")
mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
mat.set_editor_property("two_sided", True)


def c3(x, y, z, px, py):
    e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, px, py)
    e.set_editor_property("constant", unreal.LinearColor(x, y, z, 1.0))
    return e


def c1(v, px, py):
    e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, px, py)
    e.set_editor_property("r", v)
    return e


def op(cls, px, py):
    return mel.create_material_expression(mat, cls, px, py)


# ── 径向遮罩：像素到 actor 原点的水平距离 ──
wp = op(unreal.MaterialExpressionWorldPosition, -1500, 0)
actor_pos = op(unreal.MaterialExpressionObjectPositionWS, -1500, 120)
dist = op(unreal.MaterialExpressionDistance, -1300, 40)
mel.connect_material_expressions(wp, "", dist, "A")
mel.connect_material_expressions(actor_pos, "", dist, "B")

radius = c1(POOL_RADIUS, -1300, 180)
rnorm = op(unreal.MaterialExpressionDivide, -1120, 60)
mel.connect_material_expressions(dist, "", rnorm, "A")
mel.connect_material_expressions(radius, "", rnorm, "B")

one = c1(1.0, -1120, 220)
inv = op(unreal.MaterialExpressionSubtract, -950, 100)
mel.connect_material_expressions(one, "", inv, "A")
mel.connect_material_expressions(rnorm, "", inv, "B")
m = op(unreal.MaterialExpressionSaturate, -790, 100)
mel.connect_material_expressions(inv, "", m, "")

# ── 基础色：深绿边缘 → 墨绿池心 ──
deep = c3(0.006, 0.022, 0.010, -790, -320)
goo = c3(0.070, 0.340, 0.110, -790, -200)
base = op(unreal.MaterialExpressionLinearInterpolate, -560, -240)
mel.connect_material_expressions(deep, "", base, "A")
mel.connect_material_expressions(goo, "", base, "B")
mel.connect_material_expressions(m, "", base, "Alpha")
mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)

# ── 自发光：池心浓绿发光，向外衰减 ──
m2 = op(unreal.MaterialExpressionMultiply, -620, 140)
mel.connect_material_expressions(m, "", m2, "A")
mel.connect_material_expressions(m, "", m2, "B")
m3 = op(unreal.MaterialExpressionMultiply, -470, 140)
mel.connect_material_expressions(m2, "", m3, "A")
mel.connect_material_expressions(m, "", m3, "B")

glow_col = c3(0.05, 0.38, 0.10, -620, 260)
glow = op(unreal.MaterialExpressionMultiply, -300, 140)
mel.connect_material_expressions(m3, "", glow, "A")
mel.connect_material_expressions(glow_col, "", glow, "B")
glow_boost = op(unreal.MaterialExpressionMultiply, -140, 140)
mel.connect_material_expressions(glow, "", glow_boost, "A")
mel.connect_material_expressions(c1(1.3, -300, 260), "", glow_boost, "B")

fres = op(unreal.MaterialExpressionFresnel, -620, 380)
fres.set_editor_property("exponent", 3.2)
fres.set_editor_property("base_reflect_fraction", 0.04)
rim = op(unreal.MaterialExpressionMultiply, -430, 380)
mel.connect_material_expressions(fres, "", rim, "A")
mel.connect_material_expressions(c3(0.05, 0.22, 0.09, -620, 500), "", rim, "B")

emiss = op(unreal.MaterialExpressionAdd, 30, 260)
mel.connect_material_expressions(glow_boost, "", emiss, "A")
mel.connect_material_expressions(rim, "", emiss, "B")
mel.connect_material_property(emiss, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

# ── 透明羽化：最后 16% 半径淡出，边界不再像硬黑圆盘 ──
inner_a = c1(0.98, -950, 460)
inner = op(unreal.MaterialExpressionSubtract, -800, 460)
mel.connect_material_expressions(inner_a, "", inner, "A")
mel.connect_material_expressions(rnorm, "", inner, "B")
inner_div = op(unreal.MaterialExpressionDivide, -650, 460)
mel.connect_material_expressions(inner, "", inner_div, "A")
mel.connect_material_expressions(c1(0.16, -800, 560), "", inner_div, "B")
inner_sat = op(unreal.MaterialExpressionSaturate, -500, 460)
mel.connect_material_expressions(inner_div, "", inner_sat, "")
opac = op(unreal.MaterialExpressionMultiply, -340, 460)
mel.connect_material_expressions(inner_sat, "", opac, "A")
mel.connect_material_expressions(c1(0.94, -500, 560), "", opac, "B")
mel.connect_material_property(opac, "", unreal.MaterialProperty.MP_OPACITY)

# ── 法线 / 粗糙度 ──
s_norm = op(unreal.MaterialExpressionTextureSampleParameter2D, -340, 700)
s_norm.set_editor_property("parameter_name", "SludgeNormal")
s_norm.set_editor_property("texture", unreal.EditorAssetLibrary.load_asset(f"{MAT_DIR}/T_Sludge_N"))
mel.connect_material_property(s_norm, "", unreal.MaterialProperty.MP_NORMAL)

rough = c1(0.16, -340, 860)
mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
mel.connect_material_property(c1(0.0, -140, 860), "", unreal.MaterialProperty.MP_METALLIC)
mel.connect_material_property(c1(1.0, -140, 940), "", unreal.MaterialProperty.MP_SPECULAR)

mel.recompile_material(mat)
unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log("TOXIC_MAT_OK v2")

with open(r"C:\Users\25227\Documents\robot_game\docs\toxic_mat.txt", "w", encoding="utf-8") as f:
    f.write("TOXIC_MAT_OK\n")
