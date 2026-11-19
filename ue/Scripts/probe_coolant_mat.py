# -*- coding: utf-8 -*-
"""查 M_Coolant_Fluid 是否用了顶点色（Foam/Churn 通道）。"""
import unreal
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
out = []
for path in ["/Game/RobotGame/Art/Materials/M_Coolant_Fluid",
             "/Game/RobotGame/Art/Materials/M_Toxic_Fluid"]:
    m = EAL.load_asset(path)
    out.append("═══ %s ═══" % path.split("/")[-1])
    if not m:
        out.append("  !! 加载失败")
        continue
    exprs = MEL.get_material_expressions(m)
    out.append("  节点 %d：" % len(exprs))
    has_vc = False
    for e in exprs:
        cls = e.get_class().get_name()
        if "VertexColor" in cls:
            has_vc = True
        extra = ""
        if "TextureSample" in cls:
            t = e.get_editor_property("texture")
            extra = " tex=%s" % (t.get_name() if t else "None")
        out.append("    %-42s%s" % (cls, extra))
    out.append("  用顶点色: %s" % has_vc)
    out.append("")
with open(r"C:\Users\25227\Documents\robot_game\docs\coolant_mat.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("COOLANT_MAT_DONE")
