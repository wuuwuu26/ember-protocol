# -*- coding: utf-8 -*-
"""给圆形毒液池建一个精简、可控、绝不产生暖色镜面反射的液面材质
M_Toxic_Fluid_Fixed，并把 ToxicFluid_0 的 SurfaceMaterial 指向它。

背景：原 M_Toxic_Fluid 修好 sampler 后能编译了，但它含 Fresnel +
ReflectionVectorWS 的强镜面反射链路，在 Lumen/暖色灯光下把
右半边液面反射成满屏金色铜斑（A/B 换 M_Coolant_Fluid 后金色消失，
证明是材质反射链路而非场景/贴图/池底问题）。

新材质刻意**不用 Fresnel / ReflectionVectorWS / 低粗糙度镜面**，
改纯 emissive 冷绿 + 流动条纹 + 半透明 + 温和法线：
  - BaseColor 深墨绿，Roughness 固定偏高(0.45)，Specular 低 → 不产生强镜面
  - Emissive = 墨绿底 + T_Coolant_F 冷青条纹（沿 V 缓慢流动）
  - Opacity 0.85 左右，能透出一点点池底但不做玻璃镜面
  - 所有 TextureSample 用与贴图匹配的 sampler（SM5 可编译）
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
MAT_DIR = "/Game/RobotGame/Art/Materials"
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
ELL = unreal.EditorLevelLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()

NAME = "M_Toxic_Fluid_Fixed"
PATH = "%s/%s" % (MAT_DIR, NAME)
lines = []


def log(s):
    unreal.log("[ToxicFix] %s" % s)
    lines.append(str(s))


def ex(m, cls, x, y):
    return MEL.create_material_expression(m, cls, x, y)


def link(a, b, pin):
    MEL.connect_material_expressions(a, "", b, pin)


def c1(m, v, x, y):
    n = ex(m, unreal.MaterialExpressionConstant, x, y)
    n.set_editor_property("r", float(v))
    return n


def c3(m, r, g, b, x, y):
    n = ex(m, unreal.MaterialExpressionConstant3Vector, x, y)
    n.set_editor_property("constant", unreal.LinearColor(r, g, b, 1.0))
    return n


def sampler_for(tex):
    S = unreal.MaterialSamplerType
    C = unreal.TextureCompressionSettings
    comp = tex.get_editor_property("compression_settings")
    srgb = tex.get_editor_property("srgb")
    if comp == C.TC_NORMALMAP:
        return S.SAMPLERTYPE_NORMAL
    if comp == C.TC_GRAYSCALE:
        return (S.SAMPLERTYPE_GRAYSCALE if srgb
                else S.SAMPLERTYPE_LINEAR_GRAYSCALE)
    return (S.SAMPLERTYPE_COLOR if srgb else S.SAMPLERTYPE_LINEAR_COLOR)


# ── 建材质 ──
if EAL.does_asset_exist(PATH):
    EAL.delete_asset(PATH)
m = TOOLS.create_asset(NAME, MAT_DIR, unreal.Material,
                       unreal.MaterialFactoryNew())
m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
m.set_editor_property("two_sided", True)

tex_flow = EAL.load_asset("%s/T_Coolant_F" % MAT_DIR)  # 黑白流动条纹, srgb关

# 流动条纹 UV（沿 V 缓慢向下）
uv = ex(m, unreal.MaterialExpressionTextureCoordinate, -900, 0)
uv.set_editor_property("u_tiling", 2.0)
uv.set_editor_property("v_tiling", 2.0)
pan = ex(m, unreal.MaterialExpressionPanner, -720, 0)
pan.set_editor_property("speed_x", 0.02)
pan.set_editor_property("speed_y", -0.15)
link(uv, pan, "Coordinate")

samp = ex(m, unreal.MaterialExpressionTextureSample, -520, 0)
samp.set_editor_property("texture", tex_flow)
samp.set_editor_property("sampler_type", sampler_for(tex_flow))
link(pan, samp, "UVs")
mask = ex(m, unreal.MaterialExpressionComponentMask, -340, 0)
mask.set_editor_property("r", True)
link(samp, mask, "")

# Emissive = 墨绿底 + 冷青条纹（条纹弱提亮，保持"毒液"暗绿不刺眼）
mul = ex(m, unreal.MaterialExpressionMultiply, -160, 100)
link(mask, mul, "A")
link(c3(m, 0.06, 0.22, 0.14, -340, 200), mul, "B")
add = ex(m, unreal.MaterialExpressionAdd, 40, 120)
link(c3(m, 0.010, 0.045, 0.025, -340, 340), add, "A")
link(mul, add, "B")
MEL.connect_material_property(add, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

# BaseColor 深墨绿
MEL.connect_material_property(
    c3(m, 0.015, 0.055, 0.030, -160, -160), "",
    unreal.MaterialProperty.MP_BASE_COLOR)

# 不接 Normal：用默认平面法线。既避开 SM5 的 float2×float3 编译错误，
# 又彻底没有法线扰动放大的镜面高光（金色斑驳的成因之一）。

# 高粗糙度 + 低高光 → 不产生金色镜面反射
MEL.connect_material_property(c1(m, 0.55, -100, 280), "",
                              unreal.MaterialProperty.MP_ROUGHNESS)
MEL.connect_material_property(c1(m, 0.10, -100, 380), "",
                              unreal.MaterialProperty.MP_SPECULAR)
MEL.connect_material_property(c1(m, 0.0, -100, 480), "",
                              unreal.MaterialProperty.MP_METALLIC)

# Opacity：0.80 + 0.15×条纹（有疏密，能隐约透池底）
omul = ex(m, unreal.MaterialExpressionMultiply, -160, -60)
link(mask, omul, "A")
link(c1(m, 0.15, -340, -40), omul, "B")
oadd = ex(m, unreal.MaterialExpressionAdd, 40, -40)
link(omul, oadd, "A")
link(c1(m, 0.80, -160, 20), oadd, "B")
MEL.connect_material_property(oadd, "", unreal.MaterialProperty.MP_OPACITY)

MEL.recompile_material(m)
EAL.save_loaded_asset(m)
log("创建 %s（无 Fresnel/Reflection，SM5 可编译）" % NAME)

# ── 指到圆形毒液池液面 ──
ELL.load_level(LEVEL)
n = 0
for a in ELL.get_all_level_actors():
    if a.get_actor_label() == "ToxicFluid_0":
        a.set_editor_property("surface_material", m)
        log("ToxicFluid_0.SurfaceMaterial -> %s" % NAME)
        n += 1
ELL.save_current_level()
log("关卡已保存，命中 %d 个液面" % n)

with open(r"C:\Users\25227\Documents\robot_game\docs\toxic_fix.txt", "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("TOXIC_FIX_DONE")
