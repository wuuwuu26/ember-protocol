# -*- coding: utf-8 -*-
"""确认 M_Basin_Concrete 的贴图采样用的是「网格 UV」还是「TextureCoordinate 节点」。"""
import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
MAT = "/Game/RobotGame/Art/Materials/M_Basin_Concrete"

out = []
m = EAL.load_asset(MAT)
exprs = MEL.get_material_expressions(m)

# 找 TextureSample 节点
samples = [e for e in exprs if "TextureSample" in e.get_class().get_name()]
out.append("贴图采样节点 %d 个" % len(samples))

for s in samples:
    t = s.get_editor_property("texture")
    out.append("")
    out.append("=== %s (tex=%s) ===" % (s.get_name(), t.get_name() if t else "None"))
    # 检查 UV 输入连接
    try:
        src = MEL.get_input_node_output_name_for_material_expression(s, "UVs")
        out.append("  UVs 输入 <- %s" % (src if src else "**未连接（用网格 UV，正确）**"))
    except Exception as e:
        out.append("  查询失败: %s" % str(e)[:60])

    # 坐标/平铺设置
    for p in ("coordinates", "texture"):
        try:
            v = s.get_editor_property(p)
            if p != "texture":
                out.append("  %s = %s" % (p, v))
        except Exception:
            pass

# 全部 TC 节点的 tiling
out.append("")
out.append("=== TextureCoordinate 节点 ===")
for e in exprs:
    if "TextureCoordinate" in e.get_class().get_name():
        try:
            out.append("  %s  u=%s v=%s" % (
                e.get_name(),
                e.get_editor_property("u_tiling"),
                e.get_editor_property("v_tiling")))
        except Exception as ex:
            out.append("  %s err %s" % (e.get_name(), str(ex)[:40]))
        # 它连到哪
        # 遍历所有节点找输入来源
        for other in exprs:
            if other is e:
                continue
            try:
                for inp in MEL.get_material_expression_input_names(other):
                    try:
                        src = MEL.get_input_node_output_name_for_material_expression(
                            other, inp)
                        if src and e.get_name() in str(src):
                            out.append("     -> %s.%s" % (
                                other.get_class().get_name(), inp))
                    except Exception:
                        pass
            except Exception:
                pass

with open(r"C:\Users\25227\Documents\robot_game\docs\basin_uv_wiring.txt",
          "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("BASIN_UV_WIRING_DONE")
