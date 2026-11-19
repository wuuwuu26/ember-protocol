# -*- coding: utf-8 -*-
import unreal
L = "[角色材质]"
MEL = unreal.MaterialEditingLibrary
for p in ("/Game/RobotGame/Art/Characters/M_Steel",
          "/Game/RobotGame/Art/Characters/M_SteelLight",
          "/Game/RobotGame/Art/Characters/M_Accent"):
    mi = unreal.EditorAssetLibrary.load_asset(p)
    if not mi:
        unreal.log("%s ❌ %s" % (L, p))
        continue
    unreal.log("%s ── %s" % (L, p.split("/")[-1]))
    for it in mi.get_editor_property("scalar_parameter_values"):
        n = it.get_editor_property("parameter_info").get_editor_property("name")
        v = it.get_editor_property("parameter_value")
        if n in ("DetailAmount", "SeamDarken", "Roughness", "Metallic",
                 "NormalStrength", "RoughDetail", "WearAmount", "SeamAO",
                 "EmissivePower", "VertexColorAmount"):
            unreal.log("%s   %-18s = %.3f" % (L, n, v))
    for it in mi.get_editor_property("vector_parameter_values"):
        n = it.get_editor_property("parameter_info").get_editor_property("name")
        v = it.get_editor_property("parameter_value")
        if n in ("BaseTint", "WearTint"):
            unreal.log("%s   %-18s = (%.3f, %.3f, %.3f)" % (L, n, v.r, v.g, v.b))
    for it in mi.get_editor_property("texture_parameter_values"):
        n = it.get_editor_property("parameter_info").get_editor_property("name")
        v = it.get_editor_property("parameter_value")
        unreal.log("%s   %-18s = %s" % (L, n, v.get_name() if v else "空"))
