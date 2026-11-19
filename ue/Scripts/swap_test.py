# -*- coding: utf-8 -*-
"""把角色 M_Steel 的贴图临时换成地面的混凝土图，用于隔离"纹理坏"还是"UV 坏"。"""
import unreal
L = "[换图测试]"
MEL = unreal.MaterialEditingLibrary
mi = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Characters/M_Steel")
td = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Materials/T_ConcreteDetail")
tn = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Materials/T_ConcreteDetail_N")
if not (mi and td and tn):
    unreal.log("%s ❌ 资产缺失" % L)
else:
    MEL.set_material_instance_texture_parameter_value(mi, "DetailTex", td)
    MEL.set_material_instance_texture_parameter_value(mi, "NormalTex", tn)
    MEL.set_material_instance_scalar_parameter_value(mi, "SeamDarken", 0.25)
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    unreal.log("%s M_Steel → T_ConcreteDetail（SeamDarken 0.25）" % L)
