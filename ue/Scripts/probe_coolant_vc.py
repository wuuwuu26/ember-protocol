# -*- coding: utf-8 -*-
"""查 M_Coolant_Fluid 里 VertexColor 各通道（R=Foam,G=Height,B=Churn）的使用。"""
import unreal
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
m = EAL.load_asset("/Game/RobotGame/Art/Materials/M_Coolant_Fluid")
out = []
exprs = MEL.get_material_expressions(m)
vcs = [e for e in exprs if "VertexColor" in e.get_class().get_name()]
out.append("VertexColor 节点 %d 个" % len(vcs))
masks = [e for e in exprs if "ComponentMask" in e.get_class().get_name()]
out.append("ComponentMask 节点 %d 个：" % len(masks))
for e in masks:
    try:
        out.append("  r=%s g=%s b=%s a=%s" % (
            e.get_editor_property("r"), e.get_editor_property("g"),
            e.get_editor_property("b"), e.get_editor_property("a")))
    except Exception:
        pass

# 材质属性输入链
out.append("")
out.append("材质属性：")
for pname, prop in [("BaseColor", unreal.MaterialProperty.MP_BASE_COLOR),
                    ("Emissive", unreal.MaterialProperty.MP_EMISSIVE_COLOR),
                    ("Opacity", unreal.MaterialProperty.MP_OPACITY),
                    ("Roughness", unreal.MaterialProperty.MP_ROUGHNESS),
                    ("Normal", unreal.MaterialProperty.MP_NORMAL)]:
    nd = MEL.get_material_property_input_node(m, prop)
    out.append("  %-10s <- %s" % (pname, nd.get_class().get_name() if nd else "未连接"))
with open(r"C:\Users\25227\Documents\robot_game\docs\coolant_vc.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("COOLANT_VC_DONE")
