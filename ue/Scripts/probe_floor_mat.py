# -*- coding: utf-8 -*-
"""查 Poly Haven 地面材质的节点结构，为"加湿感/反射"改造做准备。"""
import unreal

PH = "/Game/RobotGame/Art/Materials/PolyHaven"
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
out = []

mat = EAL.load_asset(PH + "/M_concrete_floor_02")
if not mat:
    out.append("材质加载失败")
else:
    out.append("材质 %s" % mat.get_name())
    exprs = MEL.get_material_expressions(mat)
    out.append("节点 %d：" % len(exprs))
    for e in exprs:
        cls = e.get_class().get_name()
        name = e.get_name()
        extra = ""
        if "TextureSample" in cls:
            t = e.get_editor_property("texture")
            extra = " tex=%s" % (t.get_name() if t else "None")
        if "ComponentMask" in cls:
            extra = " r=%s g=%s b=%s" % (
                e.get_editor_property("r"), e.get_editor_property("g"),
                e.get_editor_property("b"))
        out.append("  %-40s %s%s" % (cls, name, extra))

    # 各属性输入节点
    for pname, prop in [("BaseColor", unreal.MaterialProperty.MP_BASE_COLOR),
                        ("Roughness", unreal.MaterialProperty.MP_ROUGHNESS),
                        ("Metallic", unreal.MaterialProperty.MP_METALLIC),
                        ("Normal", unreal.MaterialProperty.MP_NORMAL),
                        ("AO", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)]:
        try:
            node = MEL.get_material_property_input_node(mat, prop)
            out.append("  %-12s <- %s" % (pname, node.get_class().get_name() if node else "未连接"))
        except Exception as ex:
            out.append("  %-12s err %s" % (pname, ex))

    # 材质全局设置
    for p in ("shading_model", "two_sided", "blend_mode"):
        try:
            out.append("  %s = %s" % (p, mat.get_editor_property(p)))
        except Exception:
            pass

with open(r"C:\Users\25227\Documents\robot_game\docs\floor_mat_probe.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("FLOOR_MAT_PROBE_DONE")
