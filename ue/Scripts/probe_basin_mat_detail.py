# -*- coding: utf-8 -*-
"""详查 M_Basin_Concrete 的节点连线（第一百一十二轮）。

重点：WorldPosition 驱动的 UV 在圆形/曲面程序化网格上会拉伸、重复、
出摩尔纹。需要看清楚 BaseColor 和 Normal 各走了什么 UV。
"""
import unreal

MAT = "/Game/RobotGame/Art/Materials/M_Basin_Concrete"
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
out = []

m = EAL.load_asset(MAT)
if not m:
    out.append("!! 加载失败")
else:
    exprs = MEL.get_material_expressions(m)
    idx = {e: i for i, e in enumerate(exprs)}

    out.append("节点清单（含输入连线）：")
    for i, e in enumerate(exprs):
        cls = e.get_class().get_name()
        tname = ""
        if "TextureSample" in cls:
            t = e.get_editor_property("texture")
            tname = " tex=%s" % (t.get_name() if t else "None")
        out.append("  [%02d] %-42s%s" % (i, cls, tname))
        # 该节点的输入
        try:
            names = MEL.get_material_expression_input_names(e)
            for inp in names:
                try:
                    src = MEL.get_input_node_output_name_for_material_expression(
                        e, inp)
                except Exception:
                    src = None
                if src:
                    out.append("        in %-12s <- %s" % (inp, src))
        except Exception:
            pass

    out.append("")
    out.append("材质属性输入：")
    for pname, prop in [("BaseColor", unreal.MaterialProperty.MP_BASE_COLOR),
                        ("Normal", unreal.MaterialProperty.MP_NORMAL),
                        ("Roughness", unreal.MaterialProperty.MP_ROUGHNESS),
                        ("Metallic", unreal.MaterialProperty.MP_METALLIC)]:
        try:
            node = MEL.get_material_property_input_node(m, prop)
            out.append("  %-10s <- %s" % (
                pname, node.get_class().get_name() if node else "未连接"))
        except Exception as e:
            out.append("  %-10s err" % pname)

with open(r"C:\Users\25227\Documents\robot_game\docs\basin_mat_detail.txt",
          "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("BASIN_MAT_DETAIL_DONE")
