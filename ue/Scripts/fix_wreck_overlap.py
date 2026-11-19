# -*- coding: utf-8 -*-
"""修复第一百一十九轮续：机甲碎骸穿模/悬空（第...轮）。

问题：place_mechwreck.py 把 4 个碎骸摆在 (4400,620)/(4050,700)/
(3200,-760)/(4900,-760)，正好落进 Gen3D 大件、Cosmos 掩体/栅栏的
包围盒里 → 断臂被野战栅栏横穿、头盔插进发电机/沙袋、碎片撞机甲核心，
平视图里看着像"穿模 + 悬空"。

修复：在关卡里直接重摆这 4 个已存在的 MechWreck actor（幂等，不动资产、
不重建别的批次），坐标取自 find_wreck_spots 的空地，并逐个校验：
  - 不与任何"道具级"现存资产 bbox 相交
  - 不与已摆好的其它碎骸相交
  - 落地 Z 用"轴心在几何中心"公式 z = (raw_h/2)*scale，保证底部贴 z=0
  - 避开中轴通道 |y|<220

方法：对所有候选点打分（离墙适中、彼此分散），贪心选最优无碰撞组合。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
EAL = unreal.EditorAssetLibrary
lines = []


def log(s):
    unreal.log("[WreckFix] %s" % s)
    lines.append(str(s))


ELL.load_level(LEVEL)

# ── 收集现存道具障碍（排除碎骸自己、墙/地面/柱等大结构）──
OBST = []
for a in ELL.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        tags = []
    if "MechWreck" in tags:
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
    try:
        cen, ext = a.get_actor_bounds(False)
    except Exception:
        continue
    if ext.z < 20 or ext.x > 300 or ext.y > 300:
        continue
    if any(k in mn for k in ("wall", "Pillar", "Catwalk", "Gantry",
                             "Doorframe", "bg_", "Floor", "Sphere")):
        continue
    OBST.append((a.get_actor_label(), cen.x, cen.y, cen.z, ext.x, ext.y, ext.z))

log("障碍道具 %d 个" % len(OBST))

# ── 4 个碎骸的 mesh（读局部 bbox 求落地 Z）──
NAMES = ["mech_torso_wreck", "severed_mech_arm",
         "mech_head_wreck", "armor_debris"]
BASE = "/Game/RobotGame/Art/Props/Gen3D"
# 目标高度（沿用 place_mechwreck 的 LAYOUT，保持一致视觉尺寸）
TARGET_H = {"mech_torso_wreck": 300, "severed_mech_arm": 150,
            "mech_head_wreck": 130, "armor_debris": 110}
LONGEST = {"severed_mech_arm", "armor_debris"}

meshes = {}
for n in NAMES:
    m = EAL.load_asset("%s/%s/SM_%s" % (BASE, n, n))
    if not m:
        log("!! 缺 mesh %s" % n)
        continue
    bb = m.get_bounding_box()
    raw_h = bb.max.z - bb.min.z
    raw_w = max(bb.max.x - bb.min.x, bb.max.y - bb.min.y)
    ref = raw_w if n in LONGEST and raw_w > raw_h else raw_h
    scale = TARGET_H[n] / ref
    z = (raw_h * 0.5) * scale
    # 世界半尺寸
    hw = (bb.max.x - bb.min.x) * 0.5 * scale
    hd = (bb.max.y - bb.min.y) * 0.5 * scale
    h = raw_h * scale
    meshes[n] = dict(mesh=m, scale=scale, z=z, hw=hw, hd=hd, h=h,
                     minz=bb.min.z)
    log("%s 缩放%.2f 落地Z=%.1f 半尺寸(%.0f,%.0f) 高%.0f"
        % (n, scale, z, hw, hd, h))


def hits(x, y, hw, hd, h, placed, pad=25):
    """候选 bbox 是否与障碍或已摆碎骸相交（水平+垂直都重叠）。"""
    z0, z1 = -5, h + 5
    for (lbl, ox, oy, oz, ex, ey, ez) in OBST:
        if z1 < oz - ez - pad or z0 > oz + ez + pad:
            continue
        if abs(x - ox) < hw + ex + pad and abs(y - oy) < hd + ey + pad:
            return True
    for (px, py, phw, phd) in placed:
        if abs(x - px) < hw + phw + pad and abs(y - py) < hd + phd + pad:
            return True
    return False


# ── 候选点：新区域两侧空地，贴边但离墙留 60，避开中轴 ──
CAND = []
for x in range(2600, 5300, 100):
    for y in list(range(-760, -260, 100)) + list(range(280, 760, 100)):
        CAND.append((x, y))
# 打分：靠边(y 绝对值大)优先；同时偏好"远离其它碎骸已占区域"由贪心保证
CAND.sort(key=lambda c: -abs(c[1]))

# 摆放顺序：大件优先
ORDER = ["mech_torso_wreck", "mech_head_wreck",
         "severed_mech_arm", "armor_debris"]

placed = []       # (x,y,hw,hd)
result = {}
for n in ORDER:
    if n not in meshes:
        continue
    d = meshes[n]
    hw, hd = d["hw"], d["hd"]
    chosen = None
    for (x, y) in CAND:
        if hits(x, y, hw, hd, d["h"], placed):
            continue
        chosen = (x, y)
        break
    if not chosen:
        log("!! %s 找不到空位" % n)
        continue
    placed.append((chosen[0], chosen[1], hw, hd))
    result[n] = chosen
    log("%-20s -> (%d,%d)" % (n, chosen[0], chosen[1]))

# ── 应用到关卡里已存在的 MechWreck actor ──
applied = 0
for a in ELL.get_all_level_actors():
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        continue
    if "MechWreck" not in tags:
        continue
    # tags 第二个是 name
    nm = next((t for t in tags if t in NAMES), None)
    if not nm or nm not in result or nm not in meshes:
        continue
    x, y = result[nm]
    d = meshes[nm]
    a.set_actor_location(unreal.Vector(float(x), float(y), float(d["z"])),
                         False, False)
    a.set_actor_scale3d(unreal.Vector(d["scale"], d["scale"], d["scale"]))
    applied += 1
    log("应用 %-20s (%d,%d,Z%.0f)" % (nm, x, y, d["z"]))

ELL.save_current_level()
log("已保存关卡，应用 %d 个" % applied)
with open(r"C:\Users\25227\Documents\robot_game\docs\wreck_fix.txt", "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("WRECK_FIX_DONE")
