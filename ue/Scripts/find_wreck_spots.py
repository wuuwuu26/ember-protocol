# -*- coding: utf-8 -*-
"""给 4 个 MechWreck 碎骸找不穿模的空地：网格搜索新区域 X 2400..5400,
Y -900..900，检查候选点包围盒与所有现存道具/结构是否相交。

碎骸目标尺寸(cm，按 place_mechwreck 的缩放后高度估)：
  torso ~300高 宽~270 | arm ~150高 宽~90 | head ~130高 宽~140 | debris ~110高 宽~150
输出每个碎骸的若干候选空位（按"离原主题区域近 + 靠边不挡通道"排序）。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
ELL.load_level(LEVEL)

# 收集所有"实心占位" actor 的世界包围盒（含结构，避免塞进墙里）
OBST = []
for a in ELL.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    comp = a.static_mesh_component
    if not comp:
        continue
    try:
        sm = comp.get_editor_property("static_mesh")
    except Exception:
        continue
    if not sm:
        continue
    mn = sm.get_name()
    lbl = a.get_actor_label()
    # 碎骸自己不算障碍（要重摆）
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        tags = []
    if "MechWreck" in tags:
        continue
    try:
        cen, ext = a.get_actor_bounds(False)
    except Exception:
        continue
    # 地面/天空/大结构：地面只当"地面"不当障碍（ext.z 很小的跳过碰撞）
    if mn == "Sphere" and "Sky" in lbl:
        continue
    if ext.z < 20:      # 地板等扁平件，不算垂直障碍
        continue
    # 墙 / 龙门 / 立柱 / 天桥 / 背景 / 大型结构：bbox 太大，是"背景"不是"道具"，
    # 不能当占位障碍（否则覆盖整条边，搜索永远无解）。碎骸只要不塞进它们中心即可。
    if ext.x > 300 or ext.y > 300:
        continue
    if any(k in mn for k in ("wall", "Pillar", "Catwalk", "Gantry",
                             "Doorframe", "bg_", "Floor")):
        continue
    OBST.append((lbl, cen.x, cen.y, cen.z, ext.x, ext.y, ext.z, mn))

# 碎骸尺寸（半宽, 半深, 高）cm
WRECKS = [
    ("mech_torso_wreck", 150, 60, 300),
    ("severed_mech_arm", 60, 50, 150),
    ("mech_head_wreck", 90, 90, 130),
    ("armor_debris", 100, 95, 110),
]

# 中轴通道 |y|<220 留空；贴墙 |y|>840 是墙内侧
lines = ["障碍数 %d" % len(OBST), ""]


def overlaps(x, y, hw, hd, h, pad=15):
    """候选碎骸 bbox 是否与任一障碍相交（水平 + 垂直都重叠才算）。"""
    # 碎骸落地：底 z≈0，顶 z≈h
    z0, z1 = -10, h
    hit = []
    for (lbl, ox, oy, oz, ex, ey, ez, mn) in OBST:
        o_z0, o_z1 = oz - ez, oz + ez
        if z1 < o_z0 - pad or z0 > o_z1 + pad:
            continue
        if abs(x - ox) < hw + ex + pad and abs(y - oy) < hd + ey + pad:
            hit.append((lbl, ox, oy))
    return hit


for (name, hw, hd, h) in WRECKS:
    cands = []
    for x in range(2500, 5350, 150):
        for y in list(range(-780, -220, 120)) + list(range(240, 800, 120)):
            hit = overlaps(x, y, hw, hd, h)
            if hit:
                continue
            # 打分：靠边(y 绝对值大)好、离墙(y≈840)留 60 边距、中轴附近略罚
            edge = abs(y)
            score = edge
            cands.append((score, x, y))
    cands.sort(key=lambda c: (-c[0], c[1]))
    lines.append("=== %s (半宽%d 半深%d 高%d) 空位候选 ===" % (name, hw, hd, h))
    for s, x, y in cands[:8]:
        lines.append("  (%d,%d) 边距分%d" % (x, y, s))
    lines.append("")

with open(r"C:\Users\25227\Documents\robot_game\docs\free_spots.txt", "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("FREE_SPOTS_DONE")
