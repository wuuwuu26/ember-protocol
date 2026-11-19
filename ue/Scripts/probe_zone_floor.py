# -*- coding: utf-8 -*-
"""对比场景1（原竞技场 X<1800）与场景2（新区域 X>=1800）的地面材质（第一百一十二轮）。

同时定位"水渠"相关物件及其材质。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

out = []

# ── 1. 地面材质分布（按区域）──
out.append("═══ 1. 地面材质分布 ═══")
stats = {}
samples = {}
for a in sub.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    c = a.static_mesh_component
    m = c.get_editor_property("static_mesh") if c else None
    if not m or "floor" not in m.get_name().lower():
        continue
    loc = a.get_actor_location()
    zone = "场景1(原)" if loc.x < 1800 else "场景2(新)"
    ov = c.get_editor_property("override_materials")
    names = tuple(x.get_name() if x else "None" for x in ov)
    key = (zone, names)
    stats[key] = stats.get(key, 0) + 1
    if key not in samples:
        samples[key] = (loc.x, loc.y)

for k in sorted(stats):
    out.append("  %-10s %3d 块  ->  %s" % (k[0], stats[k], list(k[1])))
    out.append("              样例 (%.0f, %.0f)" % samples[k])

# ── 2. 水渠相关物件 ──
out.append("")
out.append("═══ 2. 水渠 / 水池 相关物件 ═══")
KW = ("channel", "canal", "water", "pool", "basin", "gutter", "trench", "drain")
found = 0
for a in sub.get_all_level_actors():
    label = a.get_actor_label()
    cls = a.get_class().get_name()
    mesh_name = ""
    if cls == "StaticMeshActor":
        c = a.static_mesh_component
        m = c.get_editor_property("static_mesh") if c else None
        mesh_name = m.get_name() if m else ""
    blob = (label + " " + mesh_name + " " + cls).lower()
    if any(k in blob for k in KW):
        loc = a.get_actor_location()
        found += 1
        ov_names = ""
        if cls == "StaticMeshActor":
            ov = a.static_mesh_component.get_editor_property("override_materials")
            ov_names = [x.get_name() if x else "None" for x in ov]
        out.append("  %-28s %-22s mesh=%-28s (%.0f,%.0f,%.0f)" %
                   (cls, label[:28], mesh_name[:28], loc.x, loc.y, loc.z))
        if ov_names:
            out.append("      ov=%s" % ov_names)
out.append("  共 %d 个相关物件" % found)

with open(r"C:\Users\25227\Documents\robot_game\docs\zone_floor_cmp.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("ZONE_FLOOR_CMP_DONE")
