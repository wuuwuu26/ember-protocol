# -*- coding: utf-8 -*-
"""强制重编 Art/Materials 下所有母材质，修复“全场景 d1 字符贴图”的陈旧 shader map。"""
import unreal

L = "[重编材质]"
MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary

roots = [
    "/Game/RobotGame/Art/Materials",
    "/Game/RobotGame/Art/Characters",
]
seen = set()
for root in roots:
    for p in EAL.list_assets(root, recursive=False):
        if p in seen:
            continue
        seen.add(p)
        a = EAL.load_asset(p)
        if not a:
            continue
        if isinstance(a, unreal.Material):
            try:
                MEL.recompile_material(a)
                EAL.save_loaded_asset(a)
                unreal.log("%s OK %s" % (L, p))
            except Exception as e:
                unreal.log("%s FAIL %s %s" % (L, p, str(e)[:100]))
unreal.log("RECOMPILEMATS_OK")
