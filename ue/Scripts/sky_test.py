# -*- coding: utf-8 -*-
"""把穹顶材质换成一个纯绿自发光，验证"天空到底是不是穹顶在画"。"""
import unreal
L = "[天空测试]"
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
P, N = "/Game/_Probe", "M_SkyTest"
if unreal.EditorAssetLibrary.does_asset_exist("%s/%s" % (P, N)):
    unreal.EditorAssetLibrary.delete_asset("%s/%s" % (P, N))
mat = AT.create_asset(N, P, unreal.Material, unreal.MaterialFactoryNew())
if mat:
    c = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, 0, 0)
    c.set_editor_property("constant", unreal.LinearColor(0.0, 1.0, 0.0, 1.0))
    MEL.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)

unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
n = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    if "SkyDome" not in a.get_actor_label():
        continue
    smc = a.static_mesh_component
    smc.set_material(0, mat)
    n += 1
    unreal.log("%s %s → 纯绿" % (L, a.get_actor_label()))
unreal.EditorLevelLibrary.save_current_level()
unreal.log("%s 替换 %d 个" % (L, n))
