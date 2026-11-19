# -*- coding: utf-8 -*-
"""决定性测试：给穹顶换一个"纯红自发光"的极简材质。

如果天空变红 → 穹顶渲染没问题，问题在渐变材质的表达式上；
如果天空还是黑的 → 穹顶根本没进渲染（被剔除 / 尺寸 / 远裁剪）。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
DIR = "/Game/RobotGame/Art/Materials"
NAME = "M_SkyTest"
PATH = "%s/%s" % (DIR, NAME)
mel = unreal.MaterialEditingLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()


def log(s):
    unreal.log("[红色测试] %s" % s)


if unreal.EditorAssetLibrary.does_asset_exist(PATH):
    unreal.EditorAssetLibrary.delete_asset(PATH)
mat = at.create_asset(NAME, DIR, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
mat.set_editor_property("two_sided", True)
e = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -300, 0)
e.set_editor_property("constant", unreal.LinearColor(1.0, 0.05, 0.05, 1.0))
mel.connect_material_property(e, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.recompile_material(mat)
unreal.EditorAssetLibrary.save_loaded_asset(mat)
log("测试材质已建立")

unreal.EditorLevelLibrary.load_level(LEVEL)
dome = None
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == "SkyDome":
        dome = a
        break
if not dome:
    log("❌ 没有 SkyDome")
    raise SystemExit(1)
dome.static_mesh_component.set_material(0, mat)
dome.set_actor_scale3d(unreal.Vector(60.0, 60.0, 60.0))   # 半径 30m
dome.set_actor_location(unreal.Vector(-200, 0, 0), False, False)
unreal.EditorLevelLibrary.save_current_level()
log("穹顶已换成红色测试材质，半径 30m")
