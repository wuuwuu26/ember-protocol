# -*- coding: utf-8 -*-
"""SM_Env_Floor 的几何构成：顶点数、材质槽、是否带独立边框。
判断接缝白线是"网格自带边框"还是"拼接缝"的直接方法：
  统计网格的三角面数 —— 若只有 12 个（一个盒子），说明是纯盒子，接缝来自拼接；
  若面数很多，说明有细节几何，边缘可能自带高光条。"""
import unreal

m = unreal.EditorAssetLibrary.load_asset(
    "/Game/RobotGame/Art/Environment/SM_Env_Floor")
out = []
if not m:
    out.append("load fail")
else:
    out.append("name=%s" % m.get_name())
    try:
        out.append("num_lods=%s" % m.get_editor_property("number_of_lods"))
    except Exception:
        pass
    mats = m.get_editor_property("static_materials")
    out.append("material slots=%d" % len(mats))
    for i, mi in enumerate(mats):
        mi2 = mi.get_editor_property("material_interface")
        out.append("  slot%d -> %s" % (
            i, mi2.get_path_name() if mi2 else "None"))
    try:
        bb = m.get_bounding_box()
        out.append("bbox size=(%.1f,%.1f,%.1f)" % (
            bb.max.x - bb.min.x, bb.max.y - bb.min.y, bb.max.z - bb.min.z))
    except Exception as e:
        out.append("bbox err %s" % e)

with open(r"C:\Users\25227\Documents\robot_game\docs\ext_floor_mesh.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("FLOORMESH_DONE")
