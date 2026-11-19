# -*- coding: utf-8 -*-
import unreal
L = "[场景探测]"
unreal.log(L + " 开始")
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
actors = unreal.EditorLevelLibrary.get_all_level_actors()
unreal.log("%s Actor 总数 %d" % (L, len(actors)))
seen = {}
for a in actors:
    cn = a.get_class().get_name()
    seen[cn] = seen.get(cn, 0) + 1
for k, v in sorted(seen.items(), key=lambda x: -x[1]):
    unreal.log("%s   %-28s %d" % (L, k, v))
# 地面：找 Z 很低且面积大的静态网格
for a in actors:
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    loc = a.get_actor_location()
    if abs(loc.z) > 60:
        continue
    c = a.static_mesh_component
    m = c.get_material(0)
    nm = m.get_name() if m else "无"
    lbl = a.get_actor_label()
    if lbl not in seen:
        seen[lbl] = 0
    if seen[lbl] < 1:
        seen[lbl] += 1
        unreal.log("%s   地面 %-24s @(%.0f,%.0f,%.0f) 材质=%s" %
                   (L, lbl, loc.x, loc.y, loc.z, nm))
