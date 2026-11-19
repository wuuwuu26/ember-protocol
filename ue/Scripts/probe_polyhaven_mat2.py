# -*- coding: utf-8 -*-
"""验证修正版材质：ComponentMask 通道 + 材质属性是否真的连上节点。"""
import unreal

DEST = "/Game/RobotGame/Art/Materials/PolyHaven"
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
out = []

for aid in ["concrete_floor_02", "rusty_metal"]:
    m = EAL.load_asset("%s/M_%s" % (DEST, aid))
    out.append("=== M_%s ===" % aid)
    exprs = MEL.get_material_expressions(m)
    for e in exprs:
        cls = e.get_class().get_name()
        if "ComponentMask" in cls:
            out.append("  mask r=%s g=%s b=%s a=%s" % (
                e.get_editor_property("r"), e.get_editor_property("g"),
                e.get_editor_property("b"), e.get_editor_property("a")))
    # 材质属性的输入连线：用 get_material_property_input_node（若存在）
    for pname, prop in [("BaseColor", unreal.MaterialProperty.MP_BASE_COLOR),
                        ("Normal", unreal.MaterialProperty.MP_NORMAL),
                        ("Roughness", unreal.MaterialProperty.MP_ROUGHNESS),
                        ("Metallic", unreal.MaterialProperty.MP_METALLIC),
                        ("AO", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)]:
        try:
            node = MEL.get_material_property_input_node(m, prop)
            out.append("  %-12s -> %s" % (
                pname, node.get_class().get_name() if node else "**未连接**"))
        except Exception as ex:
            out.append("  %-12s (API 无 get_material_property_input_node: %s)" %
                       (pname, str(ex)[:50]))
    out.append("")

with open(r"C:\Users\25227\Documents\robot_game\docs\polyhaven_matcheck2.txt",
          "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("POLY_MATCHECK2_DONE")
