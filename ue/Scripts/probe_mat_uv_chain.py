"""导出材质的连接图：只看 DetailTex 采样点的 UV 来源链。

UE 没有直接的"取某个引脚连到哪"的 Python API，
但 MaterialExpression 有 input 结构；这里用
get_inputs / get_outputs 的表达式引用名来还原连线。
"""
import unreal

MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary

P = "/Game/RobotGame/Art/Characters/M_Steel"
mi = EAL.load_asset(P)
mat = mi.get_editor_property("parent")
out = ["material = %s" % mat.get_path_name()]

exprs = MEL.get_material_expressions(mat)
idx = {}
for i, e in enumerate(exprs):
    idx[e.get_name()] = i

out.append("expressions=%d" % len(exprs))

# 找 DetailTex 采样点，看它们的 input 有没有连东西
for e in exprs:
    if e.get_class().get_name() != "MaterialExpressionTextureSampleParameter2D":
        continue
    nm = ""
    try:
        nm = str(e.get_editor_property("parameter_name"))
    except Exception:
        pass
    if nm != "DetailTex":
        continue
    out.append("--- sample %s" % e.get_name())
    ins = MEL.get_inputs(e) if hasattr(MEL, "get_inputs") else []
    for inp in ins:
        try:
            out.append("    input %s" % inp.get_editor_property("input_name"))
        except Exception:
            out.append("    input ?")
    # 输出连接
    try:
        outs = e.get_outputs()
        out.append("    outputs=%d" % len(outs))
    except Exception:
        pass
    # 世界坐标的 UV 是否直连
    for pin in ("coordinates", "uvs"):
        try:
            v = e.get_editor_property(pin)
            out.append("    %s = %s" % (pin, v))
        except Exception:
            pass

open(r"C:\Users\25227\AppData\Local\Temp\opencode\matgraph.txt", "w",
     encoding="utf-8").write("\n".join(out))
unreal.log("MATGRAPH_OK")
