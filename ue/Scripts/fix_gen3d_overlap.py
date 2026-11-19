# -*- coding: utf-8 -*-
"""最小修复：把"废弃吊臂"crane_arm 挪出插在管道接头/栅栏的位置。

overlap_diag 里 crane_arm 制造了两对最刺眼的大穿模：
  管道接头B × 废弃吊臂 (75×273×226)
  野战栅栏A × 废弃吊臂 (124×48×180)
  壁灯C × 废弃吊臂 (小)
只挪这一个 actor 到附近无碰撞空位，即可同时消除这几对，风险最低。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
EAL = unreal.EditorAssetLibrary
lines = []


def log(s):
    unreal.log("[CraneFix] %s" % s)
    lines.append(str(s))


ELL.load_level(LEVEL)

# 障碍：除 crane_arm 自己外的所有道具级资产
OBST = []
for a in ELL.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        tags = []
    if "crane_arm" in tags:
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
    if ext.z < 15 or ext.x > 320 or ext.y > 320:
        continue
    if any(k in mn for k in ("wall", "Pillar", "Catwalk", "Gantry",
                             "Doorframe", "bg_", "Floor", "Sphere")):
        continue
    OBST.append((a.get_actor_label(), cen.x, cen.y, cen.z, ext.x, ext.y, ext.z))

# crane_arm 尺寸：原 place_gen3d 用 320cm 横向（半宽160），在满是道具的
# 贴墙带里是个"巨无霸"，怎么挪都擦碰。缩到 190cm（半宽95）更贴合周围
# 50~150cm 道具的尺度，也更容易找到不穿模的空位。
m = EAL.load_asset("/Game/RobotGame/Art/Props/Gen3D/crane_arm/SM_crane_arm")
bb = m.get_bounding_box()
raw_h = bb.max.z - bb.min.z
raw_w = max(bb.max.x - bb.min.x, bb.max.y - bb.min.y)
scale = 190.0 / raw_w            # LONGEST_EDGE（缩小）
z = raw_h * 0.5 * scale
hw = (bb.max.x - bb.min.x) * 0.5 * scale
hd = (bb.max.y - bb.min.y) * 0.5 * scale
h = raw_h * scale
log("crane_arm 缩放%.2f Z%.0f 半(%.0f,%.0f) 高%.0f" % (scale, z, hw, hd, h))

# 找空位：贴墙带太挤（吊臂半宽 160cm），y=-800 线上同时有管道接头B和栅栏A，
# 无解。放宽到两侧整片空地，按"真正无碰撞"挑，优先靠边且离原位近。
ORIG = (4350, -780)
CAND = []
for x in range(2600, 5250, 60):
    for y in list(range(-800, -300, 60)) + list(range(300, 800, 60)):
        CAND.append((x, y))
# 先按"离墙适中(贴边)"再按"离原位近"排序；真正判定靠 hits
CAND.sort(key=lambda c: (abs(abs(c[1]) - 780) * 0.3 +
                         abs(c[0]-ORIG[0]) * 0.5 + abs(c[1]-ORIG[1]) * 0.2))

chosen = None
for (x, y) in CAND:
    z0, z1 = -5, h + 5
    ok = True
    for (lbl, ox, oy, oz, ex, ey, ez) in OBST:
        if z1 < oz - ez - 25 or z0 > oz + ez + 25:
            continue
        if abs(x-ox) < hw+ex+25 and abs(y-oy) < hd+ey+25:
            ok = False
            break
    if ok:
        chosen = (x, y)
        break

if not chosen:
    log("!! 找不到空位，保持不变")
else:
    for a in ELL.get_all_level_actors():
        try:
            tags = [str(t) for t in a.get_editor_property("tags")]
        except Exception:
            continue
        if "crane_arm" not in tags:
            continue
        a.set_actor_location(
            unreal.Vector(float(chosen[0]), float(chosen[1]), float(z)),
            False, False)
        a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
        old = a.get_actor_label()
        log("废弃吊臂 %s -> (%d,%d,Z%.0f)" % (old, chosen[0], chosen[1], z))
    ELL.save_current_level()
    log("关卡已保存")

with open(r"C:\Users\25227\Documents\robot_game\docs\crane_fix.txt", "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("CRANE_FIX_DONE")
