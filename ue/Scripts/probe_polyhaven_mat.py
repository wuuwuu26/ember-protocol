# -*- coding: utf-8 -*-
"""验证 Poly Haven 材质是否真的连好了（节点 + 连线 + 贴图）。"""
import unreal

DEST = "/Game/RobotGame/Art/Materials/PolyHaven"
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
out = []

for aid in ["concrete_floor_02", "concrete_wall_001", "factory_wall",
            "rusty_metal", "corrugated_iron", "metal_grate_rusty"]:
    p = "%s/M_%s" % (DEST, aid)
    m = EAL.load_asset(p)
    out.append("=== M_%s ===" % aid)
    if not m:
        out.append("  !! 加载失败")
        continue
    try:
        exprs = MEL.get_material_expressions(m)
        out.append("  节点 %d 个" % len(exprs))
        for e in exprs:
            cls = e.get_class().get_name()
            extra = ""
            if "TextureSample" in cls:
                t = e.get_editor_property("texture")
                extra = " tex=%s" % (t.get_name() if t else "None")
            if "ComponentMask" in cls:
                extra = " r=%s g=%s b=%s a=%s" % (
                    e.get_editor_property("r"), e.get_editor_property("g"),
                    e.get_editor_property("b"), e.get_editor_property("a"))
            out.append("    %-46s%s" % (cls, extra))
    except Exception as ex:
        out.append("  节点读取失败 %s" % ex)
    # 检查各材质属性的连接
    for prop_name in ("base_color", "normal", "roughness", "metallic",
                      "ambient_occlusion"):
        try:
            v = m.get_editor_property(prop_name)
            if hasattr(v, "expression"):
                out.append("  %-20s -> %s" % (
                    prop_name, v.expression.get_class().get_name()
                    if v.expression else "None"))
            else:
                out.append("  %-20s = %s" % (prop_name, str(v)[:50]))
        except Exception as ex:
            out.append("  %-20s err %s" % (prop_name, str(ex)[:40]))
    out.append("")

with open(r"C:\Users\25227\Documents\robot_game\docs\polyhaven_matcheck.txt",
          "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("POLY_MATCHECK_DONE")
