# -*- coding: utf-8 -*-
"""
扫描所有 StaticMesh / SkeletalMesh 资产，把"空槽"或"引擎默认材质槽"
（BasicShapeMaterial / WorldGridMaterial）换成同目录下的正经材质。

背景：这批资产是脚本从 Blender 导入的，部分槽没绑上材质。
StaticMesh 用引擎默认 BasicShapeMaterial（灰白）→ 地板/集装箱一片死白，
整个画面泛白；SkeletalMesh 用默认棋盘格 → 敌人走近是个灰方块。
之前只在运行时逐个打补丁，这次直接修资产，一劳永逸。
"""
import unreal

def L(s): print("[修材质] %s" % s)

BAD = ("BasicShapeMaterial", "WorldGridMaterial")

# 按资产所在目录挑兜底材质
FALLBACK = {
    "/Game/RobotGame/Art/Environment": "/Game/RobotGame/Art/Environment/M_Steel",
    "/Game/RobotGame/Art/Props":       "/Game/RobotGame/Art/Props/M_Steel",
    "/Game/RobotGame/Art/Characters":  "/Game/RobotGame/Art/Characters/M_Steel",
    "/Game/RobotGame/Art/Modules":     "/Game/RobotGame/Art/Modules/M_Steel",
}
_fb_cache = {}
def fallback_for(asset_path):
    folder = str(asset_path).rsplit("/", 1)[0]
    p = FALLBACK.get(folder)
    if not p:
        return None
    if p not in _fb_cache:
        _fb_cache[p] = unreal.EditorAssetLibrary.load_asset(p)
    return _fb_cache[p]

ar = unreal.AssetRegistryHelpers.get_asset_registry()
assets = ar.get_assets_by_path("/Game/RobotGame/Art", recursive=True)

fixed_assets = 0
fixed_slots = 0
skipped = 0
for ad in assets:
    cls = str(ad.asset_class_path.asset_name)
    if cls not in ("StaticMesh", "SkeletalMesh"):
        continue
    path = str(ad.package_name)
    name = str(ad.asset_name)
    # 跳过 LOD / Skeleton 附属资产
    if "_LOD" in name or name.endswith("_Skeleton"):
        continue

    m = ad.get_asset()
    if not m:
        continue
    try:
        arr = m.get_editor_property("static_materials")
    except Exception:
        skipped += 1
        continue

    fb = fallback_for(path)
    changed = 0
    for i in range(len(arr)):
        try:
            mi = arr[i].get_editor_property("material_interface")
        except Exception:
            continue
        need = (mi is None) or (mi.get_name() in BAD)
        if need:
            if fb is None:
                L("  %-28s 槽%d 需要兜底材质但目录没有 M_Steel" % (name, i))
                continue
            arr[i].set_editor_property("material_interface", fb)
            changed += 1

    if changed:
        m.set_editor_property("static_materials", arr)
        unreal.EditorAssetLibrary.save_loaded_asset(m)
        fixed_assets += 1
        fixed_slots += changed
        L("  %-28s 修复 %d 槽" % (name, changed))

L("完成：修复 %d 个资产、共 %d 个槽（跳过 %d 个读不到材质的）"
  % (fixed_assets, fixed_slots, skipped))
