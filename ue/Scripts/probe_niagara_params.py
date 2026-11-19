# -*- coding: utf-8 -*-
"""查 NS_WaterSplash 的用户暴露参数（决定能否用 Python 调成水花）。"""
import unreal

EAL = unreal.EditorAssetLibrary
out = []

sysm = EAL.load_asset("/Game/RobotGame/FX/NS_WaterSplash")
out.append("system = %s" % (sysm.get_class().get_name() if sysm else "None"))

# 尝试各种 API
for fn in ("get_exposed_parameters", "get_editor_property"):
    out.append("  有 %s: %s" % (fn, hasattr(sysm, fn)))

# 列出所有 UPROPERTY 名字（找参数相关）
out.append("")
out.append("=== 属性里含 param/expose 的 ===")
for n in dir(sysm):
    if any(k in n.lower() for k in ("param", "expose", "emitter", "user")):
        out.append("  " + n)

# 尝试 get_exposed_parameters
try:
    ep = sysm.get_exposed_parameters()
    out.append("")
    out.append("get_exposed_parameters() = %s (%s)" % (
        ep, ep.get_class().get_name() if ep else "None"))
except Exception as e:
    out.append("get_exposed_parameters err: %s" % str(e)[:80])

# EditorScripting 是否有 Niagara 辅助
out.append("")
out.append("=== Niagara 相关函数库 ===")
for n in dir(unreal):
    if "Niagara" in n and ("Library" in n or "Function" in n or "Editor" in n or "Scripting" in n):
        out.append("  " + n)

with open(r"C:\Users\25227\Documents\robot_game\docs\niagara_params.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("NIAGARA_PARAMS_DONE")
