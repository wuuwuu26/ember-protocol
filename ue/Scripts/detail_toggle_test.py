import json
import os
import unreal

MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
AR = unreal.AssetRegistryHelpers.get_asset_registry()
STATE = r"C:\Users\25227\AppData\Local\Temp\opencode\detail_backup.json"

mode = os.environ.get("DTEST", "off")

paths = []
for folder in ("/Game/RobotGame/Art/Characters", "/Game/RobotGame/Art/Environment",
               "/Game/RobotGame/Art/Props"):
    for ad in AR.get_assets_by_path(folder, recursive=False):
        n = str(ad.asset_name)
        if n.startswith("M_"):
            p = str(ad.package_name)
            a = EAL.load_asset(p)
            if isinstance(a, unreal.MaterialInstanceConstant):
                paths.append(p)

if mode == "off":
    backup = {}
    for p in paths:
        mi = EAL.load_asset(p)
        try:
            d = MEL.get_material_instance_scalar_parameter_value(mi, "DetailAmount")
            nm = MEL.get_material_instance_scalar_parameter_value(mi, "NormalStrength")
        except Exception:
            continue
        backup[p] = [d, nm]
        try:
            MEL.set_material_instance_scalar_parameter_value(mi, "DetailAmount", 0.0)
            MEL.set_material_instance_scalar_parameter_value(mi, "NormalStrength", 0.0)
        except Exception:
            pass
        EAL.save_asset(p)
    json.dump(backup, open(STATE, "w", encoding="utf-8"))
    unreal.log("DTEST off on %d MI" % len(backup))
else:
    backup = json.load(open(STATE, "r", encoding="utf-8"))
    for p, (d, nm) in backup.items():
        mi = EAL.load_asset(p)
        try:
            MEL.set_material_instance_scalar_parameter_value(mi, "DetailAmount", d)
            MEL.set_material_instance_scalar_parameter_value(mi, "NormalStrength", nm)
        except Exception:
            pass
        EAL.save_asset(p)
    unreal.log("DTEST restored %d MI" % len(backup))

unreal.log("DTEST_DONE")
