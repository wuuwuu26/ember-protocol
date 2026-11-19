import unreal

EAL = unreal.EditorAssetLibrary
reg = unreal.AssetRegistryHelpers.get_asset_registry()
lines = []

for ad in reg.get_assets_by_path("/Game/RobotGame/Art/Characters", recursive=True):
    n = str(ad.asset_name)
    if n.startswith("M_Steel") or n.startswith("M_Joint") or n.startswith("M_Copper") \
       or n.startswith("M_Accent") or n.startswith("M_Frame") or n.startswith("M_SteelLight"):
        lines.append("MAT %s path=%s" % (n, str(ad.package_name)))

# 列出所有材质名（去重）
seen = {}
for ad in reg.get_assets_by_path("/Game/RobotGame/Art", recursive=True):
    n = str(ad.asset_name)
    if n.startswith("M_"):
        seen.setdefault(n, str(ad.package_name))
lines.append("--- all M_ ---")
for k in sorted(seen):
    lines.append("  %-30s %s" % (k, seen[k]))

open(r"C:\Users\25227\AppData\Local\Temp\opencode\mats.txt", "w", encoding="utf-8").write("\n".join(lines))
unreal.log("MATS_OK")
