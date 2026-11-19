# -*- coding: utf-8 -*-
"""核查地面材质的 Multiply 系数实际值（防止重复乘导致过滑）。"""
import unreal

PH = "/Game/RobotGame/Art/Materials/PolyHaven"
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
out = []

mat = EAL.load_asset(PH + "/M_concrete_floor_02")
exprs = MEL.get_material_expressions(mat)
out.append("节点清单：")
for e in exprs:
    cls = e.get_class().get_name()
    extra = ""
    if cls == "MaterialExpressionMultiply":
        extra = ""   # Multiply 的 A/B 是 protected，读不了
    if cls == "MaterialExpressionConstant":
        extra = "  r=%s" % e.get_editor_property("r")
    out.append("  %-42s%s" % (cls, extra))

# 数一下有几个 Multiply / Constant
n_mul = sum(1 for e in exprs if e.get_class().get_name() == "MaterialExpressionMultiply")
n_const = sum(1 for e in exprs if e.get_class().get_name() == "MaterialExpressionConstant")
out.append("")
out.append("Multiply 节点数 = %d   Constant 节点数 = %d" % (n_mul, n_const))
out.append("（正常应为 1 和 1；若 Multiply>1 说明重复执行叠加了）")

with open(r"C:\Users\25227\Documents\robot_game\docs\floor_wet_check.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("FLOOR_WET_CHECK_DONE")
