# -*- coding: utf-8 -*-
import unreal
L = "[UV检查]"
m = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Characters/SK_Chassis_Medium")
if not m:
    unreal.log("%s ❌" % L)
else:
    cand = [x for x in dir(m) if "uv" in x.lower() or "channel" in x.lower()]
    unreal.log("%s 可用方法: %s" % (L, cand))
    try:
        rd = m.get_editor_property("skeletal_mesh_render_data")
        unreal.log("%s render_data=%s" % (L, rd))
    except Exception as e:
        unreal.log("%s render_data 读取失败 %s" % (L, str(e)[:60]))
    # 尝试静态网格库的 UV 通道查询
    for fn in ("get_number_uv_channels", "get_num_uv_channels"):
        f = getattr(unreal.EditorStaticMeshLibrary, fn, None)
        if f:
            try:
                unreal.log("%s %s(SkeletalMesh) → %s" % (L, fn, f(m)))
            except Exception as e:
                unreal.log("%s %s 失败: %s" % (L, fn, str(e)[:70]))
