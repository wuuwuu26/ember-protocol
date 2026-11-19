# -*- coding: utf-8 -*-
"""对比两份 SM_IdolMech：以前导入的（StaticMeshes/）与这次导入的（根目录）。"""
import unreal

BASE = "/Game/RobotGame/Art/Props/IdolMech"
cands = [
    BASE + "/StaticMeshes/SM_IdolMech",
    BASE + "/SM_IdolMech",
]
out = []

for p in cands:
    out.append("== %s ==" % p)
    m = unreal.EditorAssetLibrary.load_asset(p)
    if not m:
        out.append("  加载失败")
        out.append("")
        continue
    try:
        bb = m.get_bounding_box()
        out.append("  包围盒 size=(%.2f, %.2f, %.2f)"
                   % (bb.max.x - bb.min.x, bb.max.y - bb.min.y, bb.max.z - bb.min.z))
    except Exception as e:
        out.append("  包围盒失败 %s" % e)
    try:
        sm = m.get_editor_property("static_materials")
        out.append("  材质槽 %d 个" % len(sm))
        for i, x in enumerate(sm):
            mi = x.get_editor_property("material_interface")
            out.append("    slot%d -> %s" % (i, mi.get_path_name() if mi else "None"))
    except Exception as e:
        out.append("  材质槽失败 %s" % e)
    try:
        lg = m.get_editor_property("lod_group")
        out.append("  nanite=%s" % lg.get_editor_property("nanite_settings").get_editor_property("enabled"))
    except Exception:
        pass
    out.append("")

# 材质对比
for p in (BASE + "/Materials/M_IdolMech_VC", BASE + "/Materials/IdolMechMat"):
    out.append("== %s ==" % p)
    a = unreal.EditorAssetLibrary.load_asset(p)
    if not a:
        out.append("  加载失败")
    else:
        out.append("  class=%s" % a.get_class().get_name())
        if a.get_class().get_name() == "MaterialInstanceConstant":
            try:
                par = a.get_editor_property("parent")
                out.append("  parent=%s" % (par.get_path_name() if par else "None"))
            except Exception as e:
                out.append("  parent 失败 %s" % e)
        else:
            try:
                exprs = unreal.MaterialEditingLibrary.get_material_expressions(a)
                out.append("  表达式 %d 个" % len(exprs))
                for e in exprs:
                    out.append("    %-30s" % e.get_class().get_name())
            except Exception as e:
                out.append("  表达式失败 %s" % e)
    out.append("")

with open(r"C:\Users\25227\Documents\robot_game\docs\idol_cmp.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("IDOL_CMP_DONE")
