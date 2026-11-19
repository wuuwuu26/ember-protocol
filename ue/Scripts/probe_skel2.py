# -*- coding: utf-8 -*-
import unreal
L = "[骨架2]"
ar = unreal.AssetRegistryHelpers.get_asset_registry()
f = unreal.ARFilter(package_paths=["/Game/RobotGame/Art/Characters"],
                    recursive_paths=False, class_names=["Skeleton"])
unreal.log("%s 骨架资产: %s" % (L, [str(a.asset_name) for a in ar.get_assets(f)]))
for nm in ("SK_Chassis_Light", "SK_Chassis_Medium", "SK_Chassis_Heavy"):
    m = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Characters/%s" % nm)
    if not m:
        unreal.log("%s ❌ %s 不存在" % (L, nm))
        continue
    info = []
    for p in ("skeleton", "Skeleton"):
        try:
            v = m.get_editor_property(p)
            info.append("%s=%s" % (p, v.get_name() if v else "空"))
        except Exception as e:
            info.append("%s=?" % p)
    try:
        nl = m.get_editor_property("lod_info")
        info.append("LOD组=%d" % len(nl))
    except Exception:
        pass
    unreal.log("%s %-20s %s" % (L, nm, " ".join(info)))
