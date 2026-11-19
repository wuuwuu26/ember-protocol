# -*- coding: utf-8 -*-
import unreal
L = "[测试图]"
MEL = unreal.MaterialEditingLibrary
tp = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Materials/T_MechDetail")
for p in ("/Game/RobotGame/Art/Characters/M_Steel",
          "/Game/RobotGame/Art/Characters/M_SteelLight"):
    mi = unreal.EditorAssetLibrary.load_asset(p)
    if mi and tp:
        MEL.set_material_instance_texture_parameter_value(mi, "DetailTex", tp)
        MEL.set_material_instance_scalar_parameter_value(mi, "SeamDarken", 0.3)
        unreal.EditorAssetLibrary.save_loaded_asset(mi)
        unreal.log("%s %s → T_MechDetail" % (L, p.split("/")[-1]))
