# -*- coding: utf-8 -*-
"""列出 M_Splash_Foam 所有常量的当前值。"""
import unreal
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
m = EAL.load_asset("/Game/RobotGame/Art/Materials/M_Splash_Foam")
out = []
for i, e in enumerate(MEL.get_material_expressions(m)):
    cls = e.get_class().get_name()
    extra = ""
    if cls == "MaterialExpressionConstant":
        extra = " r=%s" % e.get_editor_property("r")
    elif cls == "MaterialExpressionConstant3Vector":
        c = e.get_editor_property("constant")
        extra = " (%.2f, %.2f, %.2f)" % (c.r, c.g, c.b)
    out.append("[%02d] %-42s%s" % (i, cls, extra))
with open(r"C:\Users\25227\Documents\robot_game\docs\splash_consts.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("SPLASH_CONSTS_DONE")
