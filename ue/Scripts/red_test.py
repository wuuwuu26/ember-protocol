# -*- coding: utf-8 -*-
import unreal
L = "[红色测试]"
mel = unreal.MaterialEditingLibrary
for p in ("/Game/RobotGame/Art/Environment/M_SteelLight",
          "/Game/RobotGame/Art/Environment/M_Steel",
          "/Game/RobotGame/Art/Characters/M_Steel"):
    mi = unreal.EditorAssetLibrary.load_asset(p)
    if not mi:
        unreal.log("%s 找不到 %s" % (L, p)); continue
    mel.set_material_instance_vector_parameter_value(
        mi, "BaseTint", unreal.LinearColor(1.0, 0.0, 0.0, 1.0))
    par = mi.get_editor_property("parent")
    unreal.log("%s %s 父=%s 已设红" % (L, p, par.get_name() if par else "空"))
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
