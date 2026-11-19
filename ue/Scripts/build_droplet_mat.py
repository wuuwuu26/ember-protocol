# -*- coding: utf-8 -*-
"""建专用水珠材质 M_SplashDroplet（青白半透明发光）。"""
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
MP = unreal.MaterialProperty
DIR = "/Game/RobotGame/Art/Materials"
PATH = DIR + "/M_SplashDroplet"
out = []

if EAL.does_asset_exist(PATH):
    EAL.delete_asset(PATH)

m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    "M_SplashDroplet", DIR, unreal.Material, unreal.MaterialFactoryNew())
if not m:
    out.append("创建失败")
else:
    # 半透明
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("two_sided", True)

    def add(cls, x, y):
        return MEL.create_material_expression(m, cls, x, y)

    # BaseColor：青白
    bc = add(unreal.MaterialExpressionConstant3Vector, -400, -100)
    bc.set_editor_property("constant", unreal.LinearColor(0.45, 0.85, 1.0, 1.0))
    MEL.connect_material_property(bc, "", MP.MP_BASE_COLOR)

    # Emissive：淡青自发光（水珠在暗场里也能看见）
    em = add(unreal.MaterialExpressionConstant3Vector, -400, 60)
    em.set_editor_property("constant", unreal.LinearColor(0.15, 0.55, 0.75, 1.0))
    MEL.connect_material_property(em, "", MP.MP_EMISSIVE_COLOR)

    # Opacity 0.85
    op = add(unreal.MaterialExpressionConstant, -400, 220)
    op.set_editor_property("r", 0.85)
    MEL.connect_material_property(op, "", MP.MP_OPACITY)

    # Roughness 0.15（水润高光）
    rg = add(unreal.MaterialExpressionConstant, -400, 360)
    rg.set_editor_property("r", 0.15)
    MEL.connect_material_property(rg, "", MP.MP_ROUGHNESS)

    MEL.recompile_material(m)
    EAL.save_asset(PATH, only_if_is_dirty=False)
    out.append("M_SplashDroplet 建好（半透明青白 + 自发光）")

with open(r"C:\Users\25227\Documents\robot_game\docs\droplet_mat.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("DROPLET_MAT_DONE")
