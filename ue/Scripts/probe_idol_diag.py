# -*- coding: utf-8 -*-
"""第一百零三轮诊断：
1) SM_IdolMech 是否真的带上了顶点色
2) M_IdolMech_VC 基材质里有没有 VertexColor 节点、有没有贴图
3) 实例 IdolMechMat 覆盖了哪些参数
"""
import unreal

DEST = "/Game/RobotGame/Art/Props/IdolMech"
out = []

# ── 1. 网格是否有顶点色 ──
mesh = unreal.EditorAssetLibrary.load_asset(DEST + "/SM_IdolMech")
if mesh:
    out.append("== SM_IdolMech ==")
    for attr in ("has_vertex_colors", "vertex_colors"):
        try:
            out.append("  %s = %s" % (attr, mesh.get_editor_property(attr)))
        except Exception:
            pass
    # 用 get_default_mesh_description / 统计顶点色
    try:
        lod = mesh.get_editor_property("lod_group")
        imp = lod.get_editor_property("imported_meshes") if lod else None
        out.append("  lod_group ok, imported=%s" % (len(imp) if imp else 0))
    except Exception as e:
        out.append("  lod_group 读取失败 %s" % e)

# ── 2. 基材质 ──
mat = None
for p in (DEST + "/M_IdolMech_VC", DEST + "/M_IdolMech_VC.M_IdolMech_VC"):
    mat = unreal.EditorAssetLibrary.load_asset(p)
    if mat:
        break
if mat:
    out.append("")
    out.append("== 基材质 %s (%s) ==" % (mat.get_name(), mat.get_class().get_name()))
    try:
        exprs = unreal.MaterialEditingLibrary.get_material_expressions(mat)
        out.append("  表达式 %d 个：" % len(exprs))
        for e in exprs:
            out.append("    %-32s %s" % (e.get_class().get_name(), e.get_name()))
    except Exception as e:
        out.append("  表达式读取失败 %s" % e)
else:
    out.append("")
    out.append("!! 基材质加载不到（可能还没保存到磁盘）")

# ── 3. 实例参数 ──
inst = unreal.EditorAssetLibrary.load_asset(DEST + "/IdolMechMat")
if inst:
    out.append("")
    out.append("== 实例 IdolMechMat ==")
    try:
        parent = inst.get_editor_property("parent")
        out.append("  parent = %s" % (parent.get_path_name() if parent else "None"))
    except Exception as e:
        out.append("  parent 读取失败 %s" % e)
    try:
        names = inst.get_editor_property("scalar_parameter_values")
        out.append("  标量参数 %d 个" % len(names))
        for v in names:
            out.append("    %s = %s" % (v.get_editor_property("parameter_name"),
                                       v.get_editor_property("parameter_value")))
    except Exception as e:
        out.append("  标量参数读取失败 %s" % e)
    try:
        tv = inst.get_editor_property("texture_parameter_values")
        out.append("  贴图参数 %d 个" % len(tv))
        for v in tv:
            out.append("    %s" % v.get_editor_property("parameter_name"))
    except Exception as e:
        out.append("  贴图参数读取失败 %s" % e)

with open(r"C:\Users\25227\Documents\robot_game\docs\idol_diag.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("IDOL_DIAG_DONE")
