# -*- coding: utf-8 -*-
import unreal
L = "[UV检查]"
for nm in ("SK_Chassis_Medium", "SK_Enemy_Guard"):
    m = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Characters/%s" % nm)
    if not m:
        continue
    try:
        n = unreal.EditorStaticMeshLibrary.get_num_uv_channels(m, 0)
        unreal.log("%s %-20s LOD0 UV 通道数 = %s" % (L, nm, n))
    except Exception as e:
        unreal.log("%s %-20s 查询失败: %s" % (L, nm, str(e)[:80]))
