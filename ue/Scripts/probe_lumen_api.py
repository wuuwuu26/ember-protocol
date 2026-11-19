# -*- coding: utf-8 -*-
"""查 Lumen/反射相关枚举与 PPV 字段在 UE5.8 Python 里的正确名字。"""
import unreal

out = []
# 枚举
for n in dir(unreal):
    if any(k in n for k in ("ReflectionMethod", "GlobalIllumination", "Lumen")):
        out.append(n)

out.append("")
out.append("=== ReflectionMethod ===")
try:
    for e in dir(unreal.ReflectionMethod):
        if not e.startswith("_"):
            out.append("  RM.%s = %s" % (e, getattr(unreal.ReflectionMethod, e)))
except Exception as ex:
    out.append("  err %s" % ex)

out.append("")
out.append("=== DynamicGlobalIlluminationMethod ===")
try:
    for e in dir(unreal.DynamicGlobalIlluminationMethod):
        if not e.startswith("_"):
            out.append("  %s = %s" % (e, getattr(unreal.DynamicGlobalIlluminationMethod, e)))
except Exception as ex:
    out.append("  err %s" % ex)

# PPV settings 所有 override_ 字段里和反射/gi/lumen 相关的
out.append("")
out.append("=== FPostProcessSettings 相关字段 ===")
s = unreal.PostProcessSettings()
for n in dir(s):
    if n.startswith("override_") and any(k in n.lower() for k in
            ("reflection", "lumen", "global_illum", "ssr", "ray", "ambient", "bloom", "exposure", "fog", "volumetric")):
        out.append("  " + n)

with open(r"C:\Users\25227\Documents\robot_game\docs\lumen_api.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("LUMEN_API_DONE")
