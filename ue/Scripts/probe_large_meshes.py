# -*- coding: utf-8 -*-
"""扫描大尺寸场景构件，找天空遮挡物。"""
import unreal

unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
rows = []
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    cn = a.get_class().get_name()
    if cn != "StaticMeshActor":
        continue
    c = a.static_mesh_component
    if not c or not c.static_mesh:
        continue
    b = a.get_actor_bounds(False)
    o, e = b[0], b[1]
    if e.x < 800 and e.y < 800 and e.z < 400:
        continue
    mats = []
    for m in c.get_materials():
        mats.append(m.get_name() if m else "None")
    rows.append((a.get_actor_label(), c.static_mesh.get_name(), o, e, mats, c.is_visible()))
rows.sort(key=lambda r: (r[3].z, r[3].x), reverse=True)
unreal.log("[遮挡扫描] 大构件 %d 个" % len(rows))
for lbl, mesh, o, e, mats, vis in rows:
    unreal.log("[遮挡扫描] %-22s mesh=%-24s loc=(%.0f,%.0f,%.0f) ext=(%.0f,%.0f,%.0f) vis=%s mat=%s" % (
        lbl, mesh, o.x, o.y, o.z, e.x, e.y, e.z, vis, mats))
unreal.log("[遮挡扫描] 完成")