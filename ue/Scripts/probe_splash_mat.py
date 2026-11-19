# -*- coding: utf-8 -*-
"""详查 M_Splash_Foam 材质节点（第一百一十二轮）。

Splash_FoamRing / Splash_FoamDisc 用它，落水点两个圆盘显示为纯浅色无纹理。
查：贴图节点是否有有效贴图、UV 输入、BaseColor 连接、平铺。
"""
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
out = []

for path in ["/Game/RobotGame/Art/Materials/M_Splash_Foam",
             "/Game/RobotGame/Art/Materials/M_Splash_Spray"]:
    m = EAL.load_asset(path)
    out.append("═══ %s ═══" % path.split("/")[-1])
    if not m:
        out.append("  !! 加载失败")
        out.append("")
        continue
    exprs = MEL.get_material_expressions(m)
    out.append("  节点 %d 个：" % len(exprs))
    for i, e in enumerate(exprs):
        cls = e.get_class().get_name()
        extra = ""
        if "TextureSample" in cls:
            t = e.get_editor_property("texture")
            if t:
                try:
                    sz = "%dx%d" % (t.blueprint_get_size_x(), t.blueprint_get_size_y())
                except Exception:
                    sz = "?"
                extra = " tex=%s %s srgb=%s" % (
                    t.get_name(), sz, t.get_editor_property("srgb"))
            else:
                extra = " tex=**None**"
        if "TextureCoordinate" in cls:
            try:
                extra = " u=%.2f v=%.2f" % (e.get_editor_property("u_tiling"),
                                            e.get_editor_property("v_tiling"))
            except Exception:
                pass
        if cls == "MaterialExpressionConstant":
            try:
                extra = " r=%s" % e.get_editor_property("r")
            except Exception:
                pass
        if cls == "MaterialExpressionConstant3Vector":
            try:
                extra = " c=%s" % e.get_editor_property("constant")
            except Exception:
                pass
        out.append("    [%02d] %-44s%s" % (i, cls, extra))

    out.append("  材质属性输入：")
    for pname, prop in [("BaseColor", unreal.MaterialProperty.MP_BASE_COLOR),
                        ("Opacity", unreal.MaterialProperty.MP_OPACITY),
                        ("Emissive", unreal.MaterialProperty.MP_EMISSIVE_COLOR),
                        ("Roughness", unreal.MaterialProperty.MP_ROUGHNESS)]:
        try:
            node = MEL.get_material_property_input_node(m, prop)
            out.append("    %-10s <- %s" % (
                pname, node.get_class().get_name() if node else "未连接"))
        except Exception as ex:
            out.append("    %-10s err" % pname)
    try:
        out.append("    blend_mode = %s" % m.get_editor_property("blend_mode"))
    except Exception:
        pass
    out.append("")

with open(r"C:\Users\25227\Documents\robot_game\docs\splash_mat.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("SPLASH_MAT_DONE")
