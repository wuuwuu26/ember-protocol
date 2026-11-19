# -*- coding: utf-8 -*-
"""查复制出的 Niagara 系统的 User Exposed 参数与 emitter，寻找可调项。"""
import unreal

EAL = unreal.EditorAssetLibrary
out = []

sysm = EAL.load_asset("/Game/RobotGame/FX/NS_TestB")
out.append("== NS_TestB ==")
out.append("class=%s" % sysm.get_class().get_name())

# 全部 dir 里的属性名
props = [n for n in dir(sysm) if not n.startswith("_")]
out.append("属性/方法 %d 个（含参数相关）：" % len(props))
for n in props:
    if any(k in n.lower() for k in ("param", "expose", "emitter", "user", "spawn", "effect", "system")):
        out.append("  " + n)

# 试 NiagaraEditorParametersAdapterBase / get_exposed_parameters 等
out.append("")
out.append("== 参数读取尝试 ==")
for attr in ("get_exposed_parameters", "exposed_parameters",
             "get_editor_property", "get_user_exposed_parameters"):
    out.append("  %s: %s" % (attr, hasattr(sysm, attr)))

# 用 get_editor_property 直接尝试常见字段名
out.append("")
out.append("== get_editor_property 试探 ==")
for p in ("exposed_parameters", "emitter_handles", "emitters",
          "system_spawn_script", "user_exposed_parameters",
          "effect_type", "b_fixed_bounds", "fixed_bounds"):
    try:
        v = sysm.get_editor_property(p)
        out.append("  %-28s = %s" % (p, str(v)[:70]))
    except Exception as e:
        out.append("  %-28s err" % p)

# NiagaraFunctionLibrary 的 spawn 方法（挂到场景用）
out.append("")
out.append("== NiagaraFunctionLibrary 方法 ==")
for n in dir(unreal.NiagaraFunctionLibrary):
    if not n.startswith("_") and ("spawn" in n.lower() or "system" in n.lower()):
        out.append("  " + n)

with open(r"C:\Users\25227\Documents\robot_game\docs\niagara_exposed.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("NIAGARA_EXPOSED_DONE")
