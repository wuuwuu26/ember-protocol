# -*- coding: utf-8 -*-
import unreal
L = "[网格材质]"
unreal.log(L + " 开始")
ar = unreal.AssetRegistryHelpers.get_asset_registry()
n = 0
for ad in ar.get_assets_by_path("/Game/RobotGame/Art/Environment", recursive=True):
    if str(ad.asset_class_path.asset_name) != "StaticMesh":
        continue
    sm = ad.get_asset()
    if not sm:
        continue
    mats = sm.get_editor_property("static_materials")
    names = []
    for m in mats:
        mi = None
        try:
            mi = m.get_editor_property("material_interface")
        except Exception:
            pass
        names.append(mi.get_name() if mi else "空")
    unreal.log("%s   %-28s 槽%d: %s" % (L, str(ad.asset_name), len(mats), " | ".join(names)))
    n += 1
    if n > 25:
        break
