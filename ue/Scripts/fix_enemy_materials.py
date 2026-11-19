# -*- coding: utf-8 -*-
"""
补齐敌人骨骼网格上的空材质槽。

症状：敌人走近之后是一个巨大的灰色棋盘格方块 —— 因为 SK_Enemy_* 的
部分材质槽是空的（material_interface = None），UE 会用默认材质渲染那些面。
（探针实测：Hauler 的 0/4 槽、Colossus 的 0/5 槽、Patrol 的 0 槽都是空的。）
"""
import unreal

def L(s): print("[补材质] %s" % s)

FALLBACKS = ["/Game/RobotGame/Art/Materials/M_Steel",
             "/Game/RobotGame/Art/Characters/M_Steel"]
steel = None
for p in FALLBACKS:
    steel = unreal.EditorAssetLibrary.load_asset(p)
    if steel:
        L("兜底材质: %s" % p)
        break
if not steel:
    L("❌ 找不到 M_Steel，放弃")
else:
    for n in ("Guard", "Patrol", "Hauler", "Gardener", "Colossus"):
        path = "/Game/RobotGame/Art/Characters/SK_Enemy_%s" % n
        m = unreal.EditorAssetLibrary.load_asset(path)
        if not m:
            L("  %s 加载失败" % n); continue
        fixed = 0
        total = 0
        for i in range(0, 12):
            try:
                cur = m.get_material(i)
            except Exception:
                break
            total = i + 1
            if cur is None:
                try:
                    m.set_material(i, steel)
                    fixed += 1
                except Exception as e:
                    L("  %s 槽%d 写入失败: %s" % (n, i, str(e)[:50]))
        if fixed:
            unreal.EditorAssetLibrary.save_loaded_asset(m)
        L("  SK_Enemy_%-9s 共 %d 槽，补齐 %d 个空槽" % (n, total, fixed))
