# -*- coding: utf-8 -*-
"""查 M_Splash_Foam 的完整连线（判断贴图当前用在哪个通道）。"""
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
m = EAL.load_asset("/Game/RobotGame/Art/Materials/M_Splash_Foam")
out = []

exprs = MEL.get_material_expressions(m)
idx = {id(e): i for i, e in enumerate(exprs)}

for i, e in enumerate(exprs):
    cls = e.get_class().get_name()
    out.append("[%02d] %s  name=%s" % (i, cls, e.get_name()))
    # 列出输入连线
    try:
        for inp in MEL.get_material_expression_input_names(e):
            try:
                src = MEL.get_input_node_output_name_for_material_expression(e, inp)
                if src:
                    out.append("      in %-10s <- %s" % (inp, src))
            except Exception:
                pass
    except Exception:
        pass

# 材质属性
out.append("")
out.append("材质属性：")
for pname, prop in [("BaseColor", unreal.MaterialProperty.MP_BASE_COLOR),
                    ("Emissive", unreal.MaterialProperty.MP_EMISSIVE_COLOR),
                    ("Opacity", unreal.MaterialProperty.MP_OPACITY),
                    ("Roughness", unreal.MaterialProperty.MP_ROUGHNESS),
                    ("Normal", unreal.MaterialProperty.MP_NORMAL)]:
    try:
        node = MEL.get_material_property_input_node(m, prop)
        out.append("  %-10s <- %s" % (pname, node.get_class().get_name() if node else "未连接"))
    except Exception as ex:
        out.append("  %-10s err %s" % (pname, str(ex)[:40]))

with open(r"C:\Users\25227\Documents\robot_game\docs\splash_wiring.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("SPLASH_WIRING_DONE")
