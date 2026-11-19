# -*- coding: utf-8 -*-
"""摆放 Hunyuan3D 生成的资产（第一百一十轮）。

⚠️ 这些模型**轴心在几何中心**（bbox min z ≈ -100），摆放时 actor Z
   必须 = 半高 × 缩放，否则半个身子埋进地里。

⚠️ 单图版背面是模型"猜"的 → 一律让**正面朝向玩家来的方向(-X)**，
   即 yaw = 180（按 Blender 预览里正面朝 +X 判断）。

幂等：tag `Gen3D`，重跑先清理。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
BASE = "/Game/RobotGame/Art/Props/Gen3D"
TAG = "Gen3D"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\gen3d_place.txt"

EAL = unreal.EditorAssetLibrary
lines = []


def log(s):
    unreal.log("[Gen3DPlace] %s" % s)
    lines.append(str(s))


# (资产名, x, y, yaw, 目标高度cm, 说明)
# 目标高度：按真实物体尺寸设定，脚本自动算缩放
# ⚠️ 第一百一十九轮·续 4 修复：原目标高(接头260/240、吊臂320、核心240、
#    发电机200)比周围 Cosmos 道具(50~160cm)大一圈，bbox 互相吞 → 油桶组×
#    接头A、沙袋A2×发电机、吊臂×管道接头B/栅栏 等穿模。已把这些填充件
#    统一缩小、吊臂挪位：见 fix_gen3d_shrink.py / fix_gen3d_overlap.py。
#    这里同步为修复后的尺寸/坐标，避免重跑本脚本重新放大、引入穿模。
LAYOUT = [
    # 气闸门：远端闸门位置，做视觉终点（原闸门墙在 x=5400）
    ("airlock", 5150, 0, 180, 420, "气闸门（远端焦点）"),

    # 管道接头：两侧管道组旁（缩小到 165cm，避免吞掉油桶组/壁灯）
    ("pipe_junction", 3450, 800, 200, 165, "管道接头 A"),
    ("pipe_junction", 4620, -800, 160, 165, "管道接头 B"),

    # 以下模型生成后自动加入（脚本会跳过不存在的资产）
    # ⚠️ 吊臂是横向的（宽 2.0 > 高 1.5），按"最长边"定尺寸更合理；
    #    缩到 190cm 并挪到 (4340,-800) 避开管道接头B与野战栅栏A
    ("crane_arm", 4340, -800, 150, 190, "废弃吊臂"),
    ("bunker_vent", 2750, 820, 0, 220, "地堡通风机组"),
    ("mech_core", 4950, -700, 170, 165, "废弃机甲核心"),
    ("generator", 2950, -820, 20, 140, "工业发电机"),
]

# 按"最长边"而非"高度"缩放的资产（横向物件）
LONGEST_EDGE = {"crane_arm", "bunker_vent"}


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(LEVEL)
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # 幂等清理
    killed = 0
    for a in list(sub.get_all_level_actors()):
        try:
            tags = [str(t) for t in a.get_editor_property("tags")]
        except Exception:
            continue
        if TAG in tags:
            sub.destroy_actor(a)
            killed += 1
    log("清理旧 Gen3D 道具 %d 个" % killed)

    placed = 0
    skipped = []
    for (name, x, y, yaw, target_h, desc) in LAYOUT:
        mesh = EAL.load_asset("%s/%s/SM_%s" % (BASE, name, name))
        if not mesh:
            skipped.append(name)
            continue
        bb = mesh.get_bounding_box()
        raw_h = bb.max.z - bb.min.z
        raw_w = max(bb.max.x - bb.min.x, bb.max.y - bb.min.y)
        if raw_h <= 1.0:
            skipped.append(name + "(尺寸异常)")
            continue
        # 横向物件按最长边定尺寸，避免被压得过小
        ref = raw_w if name in LONGEST_EDGE and raw_w > raw_h else raw_h
        scale = target_h / ref
        # 轴心在中心 → Z = 半高 * 缩放
        z = (raw_h * 0.5) * scale

        a = sub.spawn_actor_from_class(
            unreal.StaticMeshActor,
            unreal.Vector(float(x), float(y), float(z)),
            unreal.Rotator(roll=0.0, pitch=0.0, yaw=float(yaw)))
        if not a:
            log("!! spawn 失败 %s" % desc)
            continue
        c = a.static_mesh_component
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        c.set_static_mesh(mesh)
        a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
        a.set_editor_property("tags", [TAG, name])
        a.set_actor_label(desc)
        placed += 1
        log("%-22s (%.0f,%.0f) 缩放 %.2f  实际高 %.0fcm  原始高 %.0fcm" %
            (desc, x, y, scale, target_h, raw_h))

    log("摆放 %d 个；跳过 %s" % (placed, skipped))
    les.save_current_level()
    log("已保存关卡")
    with open(REPORT, "wb") as f:
        f.write("\n".join(lines).encode("utf-8"))
    unreal.log("GEN3D_PLACE_DONE")


main()
