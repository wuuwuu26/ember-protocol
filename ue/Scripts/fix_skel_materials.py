# -*- coding: utf-8 -*-
"""修 SkeletalMesh 的空/默认材质槽（静态网格那批已经修过，属性名不一样）。"""
import unreal

def L(s): print("[修骨骼材质] %s" % s)

BAD = ("BasicShapeMaterial", "WorldGridMaterial")
FB = "/Game/RobotGame/Art/Characters/M_Steel"
steel = unreal.EditorAssetLibrary.load_asset(FB)
if not steel:
    L("❌ 找不到 %s" % FB)
else:
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = ar.get_assets_by_path("/Game/RobotGame/Art/Characters", recursive=True)
    n_asset = n_slot = 0
    for ad in assets:
        if str(ad.asset_class_path.asset_name) != "SkeletalMesh":
            continue
        name = str(ad.asset_name)
        if "_LOD" in name or name.endswith("_Skeleton"):
            continue
        m = ad.get_asset()
        if not m:
            continue
        try:
            arr = m.get_editor_property("materials")
        except Exception as e:
            L("  %-24s 读不到 materials: %s" % (name, str(e)[:50]))
            continue
        dump = []
        changed = 0
        for i in range(len(arr)):
            try:
                mi = arr[i].get_editor_property("material_interface")
            except Exception:
                dump.append("%d:?" % i); continue
            mn = mi.get_name() if mi else "空"
            dump.append("%d:%s" % (i, mn))
            if mi is None or mn in BAD:
                arr[i].set_editor_property("material_interface", steel)
                changed += 1
        if changed:
            m.set_editor_property("materials", arr)
            unreal.EditorAssetLibrary.save_loaded_asset(m)
            n_asset += 1; n_slot += changed
        L("  %-24s 槽%d 修复%d  %s" % (name, len(arr), changed, "  ".join(dump)))
    L("完成：%d 个资产、%d 个槽" % (n_asset, n_slot))
