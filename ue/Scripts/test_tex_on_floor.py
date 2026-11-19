# -*- coding: utf-8 -*-
import unreal
L = "[地面换图]"
MEL = unreal.MaterialEditingLibrary
mi = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Environment/M_Steel")
td = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Materials/T_MechDetail")
tn = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Materials/T_MechDetail_N")
if mi and td:
    MEL.set_material_instance_texture_parameter_value(mi, "DetailTex", td)
    if tn:
        MEL.set_material_instance_texture_parameter_value(mi, "NormalTex", tn)
    MEL.set_material_instance_scalar_parameter_value(mi, "SeamDarken", 0.35)
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    unreal.log("%s 环境 M_Steel → T_MechDetail" % L)
else:
    unreal.log("%s ❌ 缺资产" % L)
