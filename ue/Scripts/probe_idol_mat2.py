# -*- coding: utf-8 -*-
"""列出 M_IdolMech_VC 与其实例的参数，确认是否用顶点色。"""
import unreal

out = []
base = unreal.EditorAssetLibrary.load_asset(
    "/Game/RobotGame/Art/Props/IdolMech/M_IdolMech_VC")
if base:
    out.append("== M_IdolMech_VC ==")
    out.append("blend=%s  shading=%s  two_sided=%s"
               % (base.get_editor_property("blend_mode"),
                  base.get_editor_property("shading_model"),
                  base.get_editor_property("two_sided")))
    try:
        exprs = unreal.MaterialEditingLibrary.get_material_expressions(base)
        out.append("表达式 %d 个：" % len(exprs))
        for e in exprs:
            out.append("  %-34s %s" % (e.get_class().get_name(), e.get_name()))
    except Exception as e:
        out.append("表达式读取失败 %s" % e)

inst = unreal.EditorAssetLibrary.load_asset(
    "/Game/RobotGame/Art/Props/IdolMech/IdolMechMat")
if inst:
    out.append("")
    out.append("== IdolMechMat (实例) ==")
    try:
        pi = inst.get_parameter_info()
        scalars = pi.get_editor_property("scalar_parameters")
        vectors = pi.get_editor_property("vector_parameters")
        textures = pi.get_editor_property("texture_parameters")
        out.append("标量参数 %d 个: %s" % (len(scalars), [p.get_editor_property("name") for p in scalars]))
        out.append("向量参数 %d 个: %s" % (len(vectors), [p.get_editor_property("name") for p in vectors]))
        out.append("贴图参数 %d 个: %s" % (len(textures), [p.get_editor_property("name") for p in textures]))
    except Exception as e:
        out.append("参数读取失败 %s" % e)

with open(r"C:\Users\25227\Documents\robot_game\docs\idol_mat2.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("IDOL_MAT2_DONE")
