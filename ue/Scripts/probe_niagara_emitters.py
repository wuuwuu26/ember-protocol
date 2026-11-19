# -*- coding: utf-8 -*-
"""诊断 NS_TestB 里是否真的有 emitter（决定粒子为何不出现）。"""
import unreal

EAL = unreal.EditorAssetLibrary
out = []
for name in ("NS_TestA", "NS_TestB", "NS_TestC"):
    p = "/Game/RobotGame/FX/" + name
    a = EAL.load_asset(p)
    out.append("=== %s ===" % name)
    if not a:
        out.append("  None")
        continue
    out.append("  class=%s" % a.get_class().get_name())
    # 资产注册表依赖
    try:
        reg = unreal.AssetRegistryHelpers.get_asset_registry()
        deps = reg.get_dependencies(p, unreal.AssetRegistryDependencyOptions(
            include_soft_package_references=True,
            include_hard_package_references=True,
            include_searchable_names=False,
            include_soft_management_references=False,
            include_hard_management_references=False))
        out.append("  依赖 %d 个：" % len(deps))
        for d in deps[:20]:
            out.append("    " + str(d))
    except Exception as e:
        out.append("  依赖读取: %s" % str(e)[:70])
    # 尝试所有含 emitter 的方法
    for fn in ("get_num_emitters", "get_emitter_handles"):
        out.append("  %s: %s" % (fn, hasattr(a, fn)))

# NiagaraSystem 的 static/class default 有没有 emitter 访问
out.append("")
out.append("=== NiagaraEditor 子系统 / 脚本库 ===")
for n in dir(unreal):
    if "Niagara" in n and ("System" in n or "Editor" in n or "Library" in n):
        if "Subsystem" in n or "Library" in n or "Utilities" in n:
            out.append("  " + n)

with open(r"C:\Users\25227\Documents\robot_game\docs\niagara_emitters.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("NIAGARA_EMITTERS_DONE")
