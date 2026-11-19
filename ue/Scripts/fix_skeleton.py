# -*- coding: utf-8 -*-
"""把机体骨骼网格重新绑回它的 Skeleton 资产。

背景：`--no-lod` 那次重导入后，SK_Chassis_* 的 skeleton 引用变成空，
运行时报 "SK_Chassis_Light missing skeleton" 直接 Assertion 崩溃。
"""
import unreal
L = "[骨骼绑定]"
for code in ("light", "medium", "heavy"):
    m = unreal.EditorAssetLibrary.load_asset(
        "/Game/RobotGame/Art/Characters/SK_Chassis_%s" % code.capitalize())
    s = unreal.EditorAssetLibrary.load_asset(
        "/Game/RobotGame/Art/Characters/chassis_%s_Skeleton" % code)
    if not m or not s:
        unreal.log("%s ❌ %s: 网格=%s 骨架=%s" % (L, code, bool(m), bool(s)))
        continue
    try:
        cur = m.get_editor_property("skeleton")
    except Exception:
        cur = None
    unreal.log("%s %-20s 原骨架=%s" % (L, m.get_name(), cur.get_name() if cur else "空"))
    if not cur:
        try:
            m.set_editor_property("skeleton", s)
            unreal.EditorAssetLibrary.save_loaded_asset(m)
            nk = m.get_editor_property("skeleton")
            unreal.log("%s %-20s → 已绑定 %s" % (L, m.get_name(),
                                                nk.get_name() if nk else "❌ 仍为空"))
        except Exception as e:
            unreal.log("%s %s 绑定失败: %s" % (L, m.get_name(), str(e)[:70]))
