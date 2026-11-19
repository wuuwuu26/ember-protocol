# -*- coding: utf-8 -*-
"""摆放第一百一十八轮的机甲碎骸资产（独立脚本，不动已有 Gen3D 布局）。

叙事：被击毁的机甲散落在新区域 —— 躯干半倚墙边、断臂在旁、
头盔掉在掩体边、装甲碎片堆在角落。避开中央通道(y≈0)与已有掩体。

⚠️ Hunyuan3D 模型轴心在几何中心（minZ≈-100），actor Z = 半高×缩放。
⚠️ 单图版背面靠猜 -> 正面朝玩家来的方向(-X)，yaw=180 附近微调。
幂等：tag MechWreck。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
BASE = "/Game/RobotGame/Art/Props/Gen3D"
TAG = "MechWreck"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\mechwreck_place.txt"

EAL = unreal.EditorAssetLibrary
lines = []


def log(s):
    unreal.log("[MechWreck] %s" % s)
    lines.append(str(s))


# (资产名, x, y, yaw, 目标高度cm, 说明)
# ⚠️ 第一百一十九轮·续 4 修复：旧坐标(4400,620)/(4050,700)/(3200,-760)/
#    (4900,-760) 与 Gen3D 大件、Cosmos 掩体/栅栏 bbox 相交 → 断臂被野战栅栏
#    横穿、头盔插进发电机/沙袋（穿模+悬空观感）。以下坐标由
#    fix_wreck_overlap.py 的碰撞校验搜索得出，互不重叠且不撞其它资产，
#    底部贴地 zmin≈0。请勿改回旧值（重跑会重新引入穿模）。
LAYOUT = [
    # 破损机甲躯干：左侧贴墙空地，半倚的主体残骸（较高，做焦点）
    ("mech_torso_wreck", 3900, -760, 200, 300, "破损机甲躯干"),
    # 断裂机械臂：躯干旁空地，不再被栅栏横穿
    ("severed_mech_arm", 3600, -760, 170, 150, "断裂机械臂"),
    # 机甲头盔：右上贴墙空地的小焦点（青色面罩朝玩家）
    ("mech_head_wreck", 4700, 680, 20, 130, "废弃机甲头盔"),
    # 装甲碎片堆：右上头盔旁，落地散落
    ("armor_debris", 4500, 680, 40, 110, "装甲碎片堆"),
]

# 这些碎骸多为横向/不规则，按最长边定尺寸更自然
LONGEST_EDGE = {"severed_mech_arm", "armor_debris"}


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(LEVEL)
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    killed = 0
    for a in list(sub.get_all_level_actors()):
        try:
            tags = [str(t) for t in a.get_editor_property("tags")]
        except Exception:
            continue
        if TAG in tags:
            sub.destroy_actor(a)
            killed += 1
    log("清理旧碎骸 %d 个" % killed)

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
        ref = raw_w if name in LONGEST_EDGE and raw_w > raw_h else raw_h
        scale = target_h / ref
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
        log("%-20s (%.0f,%.0f) 缩放%.2f 高%.0fcm 原高%.0fcm" %
            (desc, x, y, scale, target_h, raw_h))

    log("摆放 %d 个；跳过 %s" % (placed, skipped))
    les.save_current_level()
    log("已保存关卡")
    with open(REPORT, "wb") as f:
        f.write("\n".join(lines).encode("utf-8"))
    unreal.log("MECHWRECK_PLACE_DONE")


main()
