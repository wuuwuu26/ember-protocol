# -*- coding: utf-8 -*-
"""找覆盖场地上方的大块水平网格（顶棚 / 天桥 / 桁架）。"""
import unreal
L = "[顶棚]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
rows = []
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    b = a.get_actor_bounds(False)
    c, e = b[0], b[1]
    # 中心在场地上方、横向跨度大、纵向薄
    if c.z > 300 and e.x > 800 and e.y > 800:
        rows.append((e.x, e.y, e.z, c.z, a.get_actor_label()))
rows.sort(reverse=True)
unreal.log("%s 上方大件 %d 个" % (L, len(rows)))
for ex, ey, ez, cz, lbl in rows[:10]:
    unreal.log("%s %-22s 跨度=(%.0f,%.0f) 中心Z=%.0f 厚度=%.0f"
               % (L, lbl, ex, ey, cz, ez))
