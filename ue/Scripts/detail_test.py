# -*- coding: utf-8 -*-
import unreal
L = "[细节测试]"
mel = unreal.MaterialEditingLibrary
for p in ("/Game/RobotGame/Art/Characters/M_Steel",
          "/Game/RobotGame/Art/Characters/M_SteelLight"):
    mi = unreal.EditorAssetLibrary.load_asset(p)
    if not mi:
        continue
    mel.set_material_instance_scalar_parameter_value(mi, "TextureSize", 40.0)
    mel.set_material_instance_scalar_parameter_value(mi, "SeamDarken", 0.02)
    mel.set_material_instance_scalar_parameter_value(mi, "WearAmount", 1.0)
    mel.set_material_instance_vector_parameter_value(
        mi, "WearTint", unreal.LinearColor(1.0, 0.0, 0.0, 1.0))
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    unreal.log("%s %s 已设为 40cm/强缝/红磨损" % (L, p))
