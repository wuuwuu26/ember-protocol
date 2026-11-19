# -*- coding: utf-8 -*-
"""最小调试材质：贴图 R 通道直接进自发光，用来判断"贴图有没有被采样"。

如果机体现在显示装甲纹理 → 说明 UV 和贴图都好，问题在 M_RobotSurface 的节点图；
如果仍然是一块纯色 → UV 或贴图本身有问题。
"""
import unreal
L = "[调试材质]"
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
PATH = "/Game/RobotGame/Art/Materials"
NAME = "M_DebugTex"

if unreal.EditorAssetLibrary.does_asset_exist("%s/%s" % (PATH, NAME)):
    unreal.EditorAssetLibrary.delete_asset("%s/%s" % (PATH, NAME))

mat = AT.create_asset(NAME, PATH, unreal.Material, unreal.MaterialFactoryNew())
tex = unreal.EditorAssetLibrary.load_asset("%s/T_MechDetail" % PATH)
if not mat or not tex:
    unreal.log("%s ❌ 创建失败" % L)
else:
    ts = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, -400, 0)
    ts.set_editor_property("parameter_name", "DetailTex")
    ts.set_editor_property("texture", tex)
    MEL.connect_material_property(ts, "R", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    unreal.log("%s 已建 M_DebugTex（DetailTex.R → 自发光）" % L)

    # 把机体所有材质槽临时换成它
    for mp in ("/Game/RobotGame/Art/Characters/SK_Chassis_Medium",
               "/Game/RobotGame/Art/Characters/SK_Chassis_Light",
               "/Game/RobotGame/Art/Characters/SK_Chassis_Heavy"):
        m = unreal.EditorAssetLibrary.load_asset(mp)
        if not m:
            continue
        try:
            mats = m.get_editor_property("materials")
            for it in mats:
                it.set_editor_property("material_interface", mat)
            m.set_editor_property("materials", mats)
            unreal.EditorAssetLibrary.save_loaded_asset(m)
            unreal.log("%s %s 全部槽 → M_DebugTex" % (L, mp.split("/")[-1]))
        except Exception as e:
            unreal.log("%s ⚠️ %s: %s" % (L, mp.split("/")[-1], str(e)[:60]))
