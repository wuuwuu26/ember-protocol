# -*- coding: utf-8 -*-
"""缩小新区域里几个"过大"的 Gen3D 填充件，消除与 Cosmos 道具的穿模。

overlap_diag 剩余的新区域真穿模：
  油桶组B × 管道接头A (225×98×100) 大
  沙袋A2 × 工业发电机 / 灭火器A × 工业发电机
根因：place_gen3d.py 给这些填充件设了 240~260cm 目标高，比周围
50~150cm 的 Cosmos 道具大一圈，包围盒自然互相吞。

修法：**只缩小、不移位**（位置不动 → 保持"管道组旁/墙角"叙事，
且绝不引入新碰撞），按新 scale 重算落地 Z 保证底部贴地。
幂等：按 tag Gen3D + 名字定位。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
EAL = unreal.EditorAssetLibrary
BASE = "/Game/RobotGame/Art/Props/Gen3D"
lines = []


def log(s):
    unreal.log("[Gen3DShrink] %s" % s)
    lines.append(str(s))


ELL.load_level(LEVEL)

# 名字 -> 新目标高度（原值：pipe_junction 250/240, generator 200, mech_core 240）
# 统一缩到与周围 Cosmos 道具(50~160cm)协调的尺度
NEW_H = {"pipe_junction": 165, "generator": 140, "mech_core": 165}
LONGEST = set()          # 这些都按高度定义尺寸（与 place_gen3d 一致）

for a in ELL.get_all_level_actors():
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        continue
    nm = next((t for t in tags if t in NEW_H), None)
    if not nm:
        continue
    m = EAL.load_asset("%s/%s/SM_%s" % (BASE, nm, nm))
    if not m:
        continue
    bb = m.get_bounding_box()
    raw_h = bb.max.z - bb.min.z
    raw_w = max(bb.max.x - bb.min.x, bb.max.y - bb.min.y)
    ref = raw_w if nm in LONGEST and raw_w > raw_h else raw_h
    scale = NEW_H[nm] / ref
    z = raw_h * 0.5 * scale
    loc = a.get_actor_location()
    a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    a.set_actor_location(unreal.Vector(loc.x, loc.y, float(z)), False, False)
    log("%-16s %-14s 目标高%d 缩放%.2f 落地Z%.0f 位置不变(%.0f,%.0f)"
        % (nm, a.get_actor_label()[:14], NEW_H[nm], scale, z, loc.x, loc.y))

ELL.save_current_level()
log("关卡已保存")
with open(r"C:\Users\25227\Documents\robot_game\docs\gen3d_shrink.txt", "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("GEN3D_SHRINK_DONE")
