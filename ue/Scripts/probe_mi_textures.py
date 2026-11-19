import unreal

MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
AR = unreal.AssetRegistryHelpers.get_asset_registry()

MIS = [
    "/Game/RobotGame/Art/Characters/M_Steel",
    "/Game/RobotGame/Art/Characters/M_SteelLight",
    "/Game/RobotGame/Art/Characters/M_Joint",
    "/Game/RobotGame/Art/Characters/M_Copper",
    "/Game/RobotGame/Art/Characters/M_Accent_heavy",
    "/Game/RobotGame/Art/Characters/M_Accent_enemy_guard",
    "/Game/RobotGame/Art/Environment/M_Steel",
    "/Game/RobotGame/Art/Environment/M_SteelLight",
    "/Game/RobotGame/Art/Environment/M_Joint",
    "/Game/RobotGame/Art/Props/M_Steel",
    "/Game/RobotGame/Art/Props/M_Copper",
]

out = []


def peek(p):
    if not EAL.does_asset_exist(p):
        out.append("%-52s MISSING" % p.split("/")[-1])
        return
    a = EAL.load_asset(p)
    if not isinstance(a, unreal.MaterialInstanceConstant):
        out.append("%-52s not MI: %s" % (p.split("/")[-1], a.get_class().get_name()))
        return
    row = ["%-22s" % p.split("/")[-1]]
    for tp in ("DetailTex", "NormalTex"):
        try:
            t = MEL.get_material_instance_texture_parameter_value(a, tp)
            row.append("%s=%s" % (tp, t.get_name() if t else "None"))
        except Exception:
            row.append("%s=<err>" % tp)
    for sp in ("TextureSize", "Metallic", "Roughness", "WearAmount", "DetailAmount"):
        try:
            v = MEL.get_material_instance_scalar_parameter_value(a, sp)
            row.append("%s=%.2f" % (sp, v))
        except Exception:
            row.append("%s=<err>" % sp)
    out.append("  ".join(row))


for p in MIS:
    peek(p)

out.append("")
out.append("--- 现有贴图资产 ---")
for folder in ("/Game/RobotGame/Art/Characters", "/Game/RobotGame/Art/Materials",
               "/Game/RobotGame/Art/Environment", "/Game/RobotGame/Art/Props"):
    for ad in AR.get_assets_by_path(folder, recursive=False):
        n = str(ad.asset_name)
        if n.startswith(("T_", "TEX_", "tx_")):
            out.append("   %-40s %s" % (n, folder.split("/")[-1]))

open(r"C:\Users\25227\AppData\Local\Temp\opencode\mitex.txt", "w",
     encoding="utf-8").write("\n".join(out))
unreal.log("MIS_OK")
