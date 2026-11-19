# -*- coding: utf-8 -*-
"""探测 UE5.8 Python 能创建哪些 Niagara 资产（第一百一十五轮）。"""
import unreal

out = []

# 1. Niagara 相关类
niagara_classes = [n for n in dir(unreal) if "Niagara" in n]
out.append("=== unreal 里 Niagara 类共 %d 个 ===" % len(niagara_classes))
for n in niagara_classes[:60]:
    out.append("  " + n)

# 2. 关键工厂类是否存在
out.append("")
out.append("=== 关键工厂/资产类 ===")
for n in ("NiagaraSystem", "NiagaraEmitter", "NiagaraSystemFactoryNew",
          "NiagaraEmitterFactoryNew", "NiagaraScript", "NiagaraComponent",
          "NiagaraDataInterface", "NiagaraParameterCollection",
          "NiagaraSpriteRendererProperties", "NiagaraMeshRendererProperties"):
    out.append("  %-40s = %s" % (n, hasattr(unreal, n)))

# 3. AssetTools 能否找到 Niagara 工厂
out.append("")
out.append("=== AssetToolsHelper 可用工厂 ===")
try:
    at = unreal.AssetToolsHelpers.get_asset_tools()
    # 列出能创建 .uasset 的工厂（名字含 niagara / particle）
    for n in dir(at):
        if "factory" in n.lower():
            out.append("  AT." + n)
except Exception as e:
    out.append("  err %s" % e)

# 4. 现有引擎 Niagara 模板/示例（可复制）
out.append("")
out.append("=== 引擎自带 Niagara 资产（可作为复制源）===")
EAL = unreal.EditorAssetLibrary
try:
    paths = EAL.list_assets("/Niagara", recursive=True, include_folder=False)
    out.append("  /Niagara 下资产 %d 个" % len(paths))
    for p in paths[:10]:
        out.append("    " + p)
except Exception as e:
    out.append("  /Niagara 读取: %s" % str(e)[:60])

with open(r"C:\Users\25227\Documents\robot_game\docs\niagara_api.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("NIAGARA_API_DONE")
