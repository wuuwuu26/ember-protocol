# -*- coding: utf-8 -*-
"""列出 M_Toxic_Fluid 里的 Fresnel/Reflection 节点 + 所有 Constant3Vector 值
+ Emissive/Roughness 链路溯源，定位金色反射项。"""
import unreal

MAT_DIR = "/Game/RobotGame/Art/Materials"
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
lines = []
def log(s):
    unreal.log("[ToxicTrace] %s" % s); lines.append(str(s))

m = EAL.load_asset("%s/M_Toxic_Fluid" % MAT_DIR)
exprs = list(MEL.get_material_expressions(m))

# 建索引：id -> (cls, 摘要)
info = {}
for i, e in enumerate(exprs):
    cls = e.get_class().get_name().replace("MaterialExpression", "")
    summ = ""
    try:
        c = e.get_editor_property("constant")
        summ = "c=(%.2f,%.2f,%.2f)" % (c.r, c.g, c.b)
    except Exception:
        pass
    try:
        summ += " r=%.2f" % e.get_editor_property("r")
    except Exception:
        pass
    info[i] = (cls, summ)

# 打印 Fresnel / Reflection / 暖色常量
log("=== 特殊节点 ===")
for i, (cls, summ) in info.items():
    if cls in ("Fresnel", "ReflectionVectorWS") or "Constant3Vector" in cls:
        log("  [%02d] %-22s %s" % (i, cls, summ))

# 打印所有连接：expr.get_inputs() 不可靠，用 MEL 遍历 expression input 属性
log("=== 连线（A/B/Base 等输入的上游）===")
for i, e in enumerate(exprs):
    cls = info[i][0]
    # 尝试读 input 结构
    try:
        for pin in ("A", "B", "Alpha", "Base", "Exponent", "Coordinate", "UVs", "Input"):
            try:
                inp = e.get_editor_property(pin.lower()) if False else None
            except Exception:
                pass
    except Exception:
        pass
    # 用 get_editor_property 尝试常见 input 字段名
    for field in ("a", "b", "alpha", "base", "exponent", "coordinate", "uvs", "input"):
        try:
            v = e.get_editor_property(field)
            if v and hasattr(v, "expression"):
                up = v.expression
                if up:
                    j = exprs.index(up) if up in exprs else -1
                    log("  [%02d]%s.%s <- [%d]%s" % (
                        i, cls, field, j,
                        info.get(j, ("?", ""))[0] if j >= 0 else up.get_class().get_name()))
        except Exception:
            pass

with open(r"C:\Users\25227\Documents\robot_game\docs\toxic_trace.txt", "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("TOXIC_TRACE_DONE")
