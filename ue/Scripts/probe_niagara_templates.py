# -*- coding: utf-8 -*-
"""在引擎 Niagara 资产里找水花/飞沫/液滴相关的模板与默认材质。"""
import unreal

EAL = unreal.EditorAssetLibrary
out = []

paths = EAL.list_assets("/Niagara", recursive=True, include_folder=False)
out.append("引擎 Niagara 资产 %d 个" % len(paths))

KW = ("splash", "water", "droplet", "foam", "spray", "particle", "burst",
      "fountain", "rain", "spark", "default", "sprite", "simple", "emit")

# 按关键词分组
for kw in ("splash", "water", "droplet", "foam", "spray", "fountain", "rain"):
    hits = [p for p in paths if kw in p.lower()]
    out.append("")
    out.append("=== %s: %d ===" % (kw, len(hits)))
    for p in hits[:15]:
        out.append("  " + p)

# 默认 sprite 材质 / 默认系统
out.append("")
out.append("=== DefaultAssets 里的关键默认资源 ===")
for p in paths:
    pl = p.lower()
    if "/defaultassets/" in pl and any(k in pl for k in
            ("sprite", "material", "system", "emitter", "texture", "default")):
        out.append("  " + p)

# NiagaraSystem 类型的引擎资产（可复制的系统）
out.append("")
out.append("=== 引擎里 NiagaraSystem 类型资产（前 30）===")
n = 0
for p in paths:
    a = EAL.load_asset(p)
    if a and a.get_class().get_name() == "NiagaraSystem":
        out.append("  " + p)
        n += 1
        if n >= 30:
            break
out.append("  (共列 %d)" % n)

with open(r"C:\Users\25227\Documents\robot_game\docs\niagara_templates.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("NIAGARA_TEMPLATES_DONE")
