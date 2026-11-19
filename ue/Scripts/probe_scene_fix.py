# -*- coding: utf-8 -*-
"""第一百零九轮诊断：移除机甲前的现状盘点。

三件事：
  1) 列出 IdolMech 雕像（待移除对象）及其资产
  2) Cosmos 道具：位置 + 世界包围盒 + 两两重叠（找穿模）+ 是否陷地
  3) 材质覆盖：找空 override / 回落白色 BasicShapeMaterial 的 actor
     （"纹理没加载出来"通常是这个：第102轮白线坑）
只读，不改动任何东西。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

out = []

# ── 1. IdolMech 雕像 ──
out.append("═══ 1. IdolMech 雕像（待移除）═══")
idols = []
for a in actor_sub.get_all_level_actors():
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        tags = []
    if any("idol" in t.lower() for t in tags) or "idol" in a.get_actor_label().lower():
        idols.append(a)
        loc = a.get_actor_location()
        out.append("  %-24s (%.0f, %.0f, %.1f) tags=%s" %
                   (a.get_actor_label(), loc.x, loc.y, loc.z, tags))
if not idols:
    out.append("  （没找到 IdolMech actor）")

# ── 2. Cosmos 道具穿模检测 ──
out.append("")
out.append("═══ 2. Cosmos 道具（穿模 / 陷地检测）═══")
props = []
for a in actor_sub.get_all_level_actors():
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        continue
    if "CosmosProp" not in tags:
        continue
    try:
        org, ext = a.get_actor_bounds(False)
    except Exception:
        continue
    loc = a.get_actor_location()
    props.append({
        "label": a.get_actor_label(),
        "slug": tags[-1] if len(tags) > 1 else "?",
        "loc": (loc.x, loc.y, loc.z),
        "min": (org.x-ext.x, org.y-ext.y, org.z-ext.z),
        "max": (org.x+ext.x, org.y+ext.y, org.z+ext.z),
        "tag": a,
    })
out.append("Cosmos 道具 %d 个" % len(props))

# 陷地：脚底（minZ）明显低于 0
out.append("")
out.append("-- 陷入地面（minZ < -5cm，会穿地）--")
sunk = [p for p in props if p["min"][2] < -5.0]
for p in sunk:
    out.append("  %-22s minZ=%.1f  locZ=%.1f  slug=%s" %
               (p["label"], p["min"][2], p["loc"][2], p["slug"]))
if not sunk:
    out.append("  （无）")

# 悬空：脚底明显高于 0 且不是墙挂件
out.append("")
out.append("-- 悬空（minZ > 30cm 且非贴墙件）--")
float_ = [p for p in props if p["min"][2] > 30.0]
for p in float_:
    out.append("  %-22s minZ=%.1f  locZ=%.1f  slug=%s" %
               (p["label"], p["min"][2], p["loc"][2], p["slug"]))
if not float_:
    out.append("  （无）")

# 两两 XY 重叠（AABB 相交，且 Z 也交叠 → 真穿模）
out.append("")
out.append("-- 两两包围盒相交（疑似穿模，仅列 XY 重叠>40cm 且 Z 交叠）--")
def overlap(a, b):
    ox = min(a["max"][0], b["max"][0]) - max(a["min"][0], b["min"][0])
    oy = min(a["max"][1], b["max"][1]) - max(a["min"][1], b["min"][1])
    oz = min(a["max"][2], b["max"][2]) - max(a["min"][2], b["min"][2])
    return ox, oy, oz
pairs = []
for i in range(len(props)):
    for j in range(i+1, len(props)):
        ox, oy, oz = overlap(props[i], props[j])
        if ox > 40 and oy > 40 and oz > 5:
            pairs.append((props[i]["label"], props[j]["label"], ox, oy, oz))
for a1, b1, ox, oy, oz in sorted(pairs, key=lambda t: -(t[2]*t[3]))[:30]:
    out.append("  %-20s × %-20s  重叠 X%.0f Y%.0f Z%.0f" % (a1, b1, ox, oy, oz))
if not pairs:
    out.append("  （无）")
out.append("  合计 %d 对" % len(pairs))

# ── 3. 材质覆盖 ──
out.append("")
out.append("═══ 3. 材质覆盖（找纹理没加载 / 白色回退）═══")
stats = {}
white_actors = []
for a in actor_sub.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    c = a.static_mesh_component
    m = c.get_editor_property("static_mesh") if c else None
    if not m:
        continue
    loc = a.get_actor_location()
    region = "EXT" if loc.x >= 1800 else "ORIG"
    ov = c.get_editor_property("override_materials")
    names = [x.get_name() if x else "None" for x in ov]
    has_basic = any("basicshape" in n.lower() for n in names)
    empty = len(names) == 0
    key = (region, "basic" if has_basic else ("empty" if empty else "ok"))
    stats[key] = stats.get(key, 0) + 1
    if has_basic or empty:
        white_actors.append((a.get_actor_label(), region,
                             (loc.x, loc.y, loc.z), names, m.get_name()))
for k, v in sorted(stats.items()):
    out.append("  %-5s %-6s : %d 块" % (k[0], k[1], v))
out.append("")
out.append("-- 疑似纹理问题 actor（空覆盖 或 BasicShapeMaterial）--")
for label, reg, l, names, mesh in white_actors[:40]:
    out.append("  [%s] %-22s (%.0f,%.0f,%.0f) mesh=%s ov=%s" %
               (reg, label, l[0], l[1], l[2], mesh, names))
if not white_actors:
    out.append("  （无）")

# ── 4. Poly Haven 材质资产是否完整 ──
out.append("")
out.append("═══ 4. Poly Haven 材质贴图连线 ═══")
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
for p in EAL.list_assets("/Game/RobotGame/Art/Materials/PolyHaven", recursive=True):
    a = EAL.load_asset(p)
    if a and a.get_class().get_name() == "Material":
        try:
            exprs = MEL.get_material_expressions(a)
            tex = [e for e in exprs if "TextureSample" in e.get_class().get_name()]
            withtex = 0
            for e in tex:
                t = e.get_editor_property("texture")
                if t:
                    withtex += 1
            out.append("  %-40s 节点%d 贴图采样%d(有贴图%d)" %
                       (a.get_name(), len(exprs), len(tex), withtex))
        except Exception as ex:
            out.append("  %s err %s" % (a.get_name(), ex))

with open(r"C:\Users\25227\Documents\robot_game\docs\scenefix_diag.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("SCENEFIX_DIAG_DONE")
