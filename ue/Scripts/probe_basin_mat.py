# -*- coding: utf-8 -*-
"""查水渠材质的 UV 与贴图设置，并判断程序化网格的 UV 是否异常。"""
import unreal

out = []
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary

# 1. 材质节点
for mat_path in ["/Game/RobotGame/Art/Materials/M_Basin_Concrete",
                 "/Game/RobotGame/Art/Materials/MI_Basin_Coolant",
                 "/Game/RobotGame/Art/Materials/M_GeoCache_Water"]:
    m = EAL.load_asset(mat_path)
    out.append("=== %s ===" % mat_path.split("/")[-1])
    if not m:
        out.append("  !! 加载失败")
        continue
    out.append("  class=%s" % m.get_class().get_name())
    if m.get_class().get_name() == "Material":
        exprs = MEL.get_material_expressions(m)
        has_tc = any("TextureCoordinate" in e.get_class().get_name() for e in exprs)
        out.append("  节点 %d，TC节点=%s" % (len(exprs), has_tc))
        for e in exprs:
            ec = e.get_class().get_name()
            extra = ""
            if "TextureSample" in ec:
                t = e.get_editor_property("texture")
                extra = " tex=%s" % (t.get_name() if t else "None")
            if "TextureCoordinate" in ec:
                extra = " u=%s v=%s" % (
                    e.get_editor_property("u_tiling") if hasattr(e, "u_tiling") else "?",
                    e.get_editor_property("v_tiling") if hasattr(e, "v_tiling") else "?")
            out.append("    %-42s%s" % (ec, extra))
    else:
        try:
            par = m.get_editor_property("parent")
            out.append("  parent=%s" % (par.get_name() if par else "None"))
        except Exception as e:
            out.append("  parent err %s" % e)
    out.append("")

# 2. 贴图设置
for tex_path in ["/Game/RobotGame/Art/Materials/T_ConcreteDetail",
                 "/Game/RobotGame/Art/Materials/T_ConcreteDetail_N"]:
    t = EAL.load_asset(tex_path)
    out.append("=== %s ===" % tex_path.split("/")[-1])
    if not t:
        out.append("  !! 加载失败")
        continue
    try:
        out.append("  size=%dx%d  srgb=%s  group=%s" % (
            t.blueprint_get_size_x(), t.blueprint_get_size_y(),
            t.get_editor_property("srgb"),
            t.get_editor_property("lod_group")))
    except Exception as e:
        out.append("  err %s" % e)

with open(r"C:\Users\25227\Documents\robot_game\docs\basin_mat.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("BASIN_MAT_DONE")
