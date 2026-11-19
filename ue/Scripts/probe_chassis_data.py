# -*- coding: utf-8 -*-
import unreal
L = "[机体数据]"
root = "/Game/RobotGame"
ar = unreal.AssetRegistryHelpers.get_asset_registry()
f = unreal.ARFilter(package_paths=[root], recursive_paths=True,
                    class_names=["RobotChassisData"])
assets = ar.get_assets(f)
unreal.log("%s 找到 %d 个机体数据资产" % (L, len(assets)))
for a in assets:
    obj = a.get_asset()
    if not obj:
        continue
    try:
        cm = obj.get_editor_property("chassis_mesh")
        if cm is None:
            p = "空"
        else:
            try:
                p = cm.get_path_name()
            except Exception:
                p = str(cm)
    except Exception as e:
        p = "读取失败 %s" % str(e)[:50]
    unreal.log("%s %-28s → %s" % (L, a.asset_name, p))
