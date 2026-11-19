# -*- coding: utf-8 -*-
"""查 M_Splash_Foam_V2 实际节点与连线，判断为何渲染成纯白。"""
import unreal
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
m = EAL.load_asset("/Game/RobotGame/Art/Materials/M_Splash_Foam_V2")
out = []
if not m:
    out.append("!! 材质不存在")
else:
    exprs = MEL.get_material_expressions(m)
    out.append("节点 %d 个：" % len(exprs))
    for i, e in enumerate(exprs):
        cls = e.get_class().get_name()
        extra = ""
        if "TextureSample" in cls:
            t = e.get_editor_property("texture")
            extra = " tex=%s" % (t.get_name() if t else "None")
        if cls == "MaterialExpressionConstant":
            extra = " r=%s" % e.get_editor_property("r")
        if cls == "MaterialExpressionConstant3Vector":
            c = e.get_editor_property("constant")
            extra = " (%.2f,%.2f,%.2f)" % (c.r, c.g, c.b)
        if cls == "MaterialExpressionTextureCoordinate":
            extra = " u=%s v=%s" % (e.get_editor_property("u_tiling"), e.get_editor_property("v_tiling"))
        out.append("  [%02d] %-44s%s" % (i, cls, extra))
    out.append("")
    out.append("属性连接：")
    for pname, prop in [("BaseColor", unreal.MaterialProperty.MP_BASE_COLOR),
                        ("Emissive", unreal.MaterialProperty.MP_EMISSIVE_COLOR),
                        ("Roughness", unreal.MaterialProperty.MP_ROUGHNESS),
                        ("Opacity", unreal.MaterialProperty.MP_OPACITY)]:
        nd = MEL.get_material_property_input_node(m, prop)
        out.append("  %-10s <- %s" % (pname, nd.get_class().get_name() if nd else "未连接"))
    # blend
    out.append("  blend=%s" % m.get_editor_property("blend_mode"))
with open(r"C:\Users\25227\Documents\robot_game\docs\splash_v2_probe.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("SPLASH_V2_PROBE_DONE")
