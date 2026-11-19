# -*- coding: utf-8 -*-
"""探测 UE5.8 材质编辑 API 的正确用法（ComponentMask / connect / 表达式输出名）。"""
import unreal

out = []
# ComponentMask 属性
m = unreal.MaterialExpressionComponentMask
out.append("ComponentMask 属性：")
for n in ("r", "g", "b", "a"):
    try:
        out.append("  %s -> %s" % (n, m.get_default_object().get_editor_property(n)))
    except Exception as e:
        out.append("  %s err %s" % (n, e))

# MaterialEditingLibrary 的连接方法签名
out.append("")
out.append("MaterialEditingLibrary 方法：")
for n in dir(unreal.MaterialEditingLibrary):
    if "connect" in n.lower() or "expression" in n.lower() or "recompile" in n.lower():
        out.append("  %s" % n)

# TextureSample 的输出 socket 名（看源码 stub 里 connect 的 output_name 常用值）
out.append("")
out.append("MaterialProperty 枚举：")
try:
    for e in unreal.MaterialProperty:
        out.append("  %s" % e)
except Exception as ex:
    out.append("  %s" % ex)

# MaterialExpressionTextureSample 有哪些输出引脚属性
ts = unreal.MaterialExpressionTextureSample
out.append("")
out.append("TextureSample 引脚相关属性：")
for n in dir(ts):
    if n.lower() in ("r", "g", "b", "a", "rgb", "rgba", "outputs"):
        out.append("  %s" % n)

with open(r"C:\Users\25227\Documents\robot_game\docs\mat_api_probe.txt",
          "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("MAT_API_DONE")
