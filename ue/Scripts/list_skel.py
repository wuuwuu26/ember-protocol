# -*- coding: utf-8 -*-
import unreal
L = "[骨架]"
ar = unreal.AssetRegistryHelpers.get_asset_registry()
f = unreal.ARFilter(package_paths=["/Game/RobotGame"], recursive_paths=True,
                    class_names=["Skeleton"])
for a in ar.get_assets(f):
    unreal.log("%s %s" % (L, a.package_name))
for nm in ("SK_Chassis_Light", "SK_Chassis_Medium"):
    m = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Characters/%s" % nm)
    if m:
        try:
            sk = m.get_editor_property("skeleton")
            unreal.log("%s %-20s 当前骨架=%s" % (L, nm, sk.get_name() if sk else "❌ 空"))
        except Exception as e:
            unreal.log("%s %s 读取失败 %s" % (L, nm, str(e)[:50]))
