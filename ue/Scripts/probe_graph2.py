# -*- coding: utf-8 -*-
import unreal
L = "[材质节点]"
m = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Materials/M_RobotSurface")
mel = unreal.MaterialEditingLibrary
for e in mel.get_material_expressions(m):
    cn = e.get_class().get_name()
    extra = ""
    for a in ("parameter_name", "function_name"):
        try:
            v = e.get_editor_property(a)
            if v:
                extra += " %s=%s" % (a, v)
        except Exception:
            pass
    unreal.log("%s %-48s%s" % (L, cn, extra))
