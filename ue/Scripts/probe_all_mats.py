# -*- coding: utf-8 -*-
"""扫描关卡里所有静态网格，统计材质使用情况，找出没有材质/默认材质的。"""
import unreal
L = "[材质扫描]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")

use = {}
missing = []
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    c = a.get_property_value if False else a.static_mesh_component
    try:
        mesh = c.get_editor_property("static_mesh")
    except Exception:
        continue
    nslots = 0
    try:
        nslots = len(mesh.get_editor_property("static_materials"))
    except Exception:
        nslots = 1
    for i in range(max(1, nslots)):
        try:
            m = c.get_material(i)
        except Exception:
            m = None
        if m is None:
            missing.append((a.get_actor_label(), mesh.get_name() if mesh else "?", i))
            continue
        nm = m.get_name()
        use[nm] = use.get(nm, 0) + 1

for k in sorted(use, key=lambda x: -use[x]):
    unreal.log("%s %-30s %d 处" % (L, k, use[k]))
unreal.log("%s ── 共 %d 种材质，%d 个空槽 ──" % (L, len(use), len(missing)))
for lbl, mesh, i in missing[:12]:
    unreal.log("%s ❌ 空槽 %s / %s 槽%d" % (L, lbl, mesh, i))
