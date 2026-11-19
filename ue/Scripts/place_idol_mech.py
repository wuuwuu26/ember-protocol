# -*- coding: utf-8 -*-
"""把 SM_IdolMech 摆进新扩建区域（第一百零三轮）

为什么放在新区域：
  竞技场（X -1300..1800）已经很满（255 个 actor），新区域（X 2400..5400）
  刚建好骨架、中间是空的 —— 一座 9 米高的机甲雕像正好当它的视觉落点。

放置参数：
  原名 1 米高 → 用户要求放大 8~10 倍，取 9.0（9 米高）
  ⚠️ 轴心在几何中心：放大 9 倍后向下延伸 450cm，
     所以 actor 的 Z 必须 = 450 才能让脚踩在 z=0 的地面上。

tag 用 IdolMech，可重复执行（幂等）。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
MESH = "/Game/RobotGame/Art/Props/IdolMech/SM_IdolMech"
TAG = "IdolMech"

# ── 摆放参数 ──
SCALE = 9.0             # 8~10 倍，取中
POS = (4750.0, 0.0)     # 新区域靠远端闸门，居中
# ⚠️ 模型的自然姿态就是**站立的**（网格里脚在 -Z、头在 +Z），不需要翻转。
#    前几轮之所以看起来倒着，是因为下面这个坑：
#
#    `unreal.Rotator(a, b, c)` 的位置参数顺序是 **(Roll, Pitch, Yaw)**，
#    不是 C++ FRotator 的 (Pitch, Yaw, Roll)。
#    实测：unreal.Rotator(10, 20, 30) 读回来是 pitch=20 / yaw=30 / roll=10。
#    我之前按 (Pitch, Yaw, Roll) 传，把 180 送进了 pitch/roll，
#    于是每次都多翻了 180° —— 这就是"模型倒着"的真正原因。
#
#    现在一律用**关键字参数**，不再依赖位置顺序。
#
#    朝向来源：在 Blender 里渲染了四个方向（docs/idol_views/），
#      +X 方向看到的是正面（胸甲、面部、爪状手），-X 是背面（脊柱分段），
#      +Y 侧视能看出脚尖朝 +X —— 所以模型正面朝 +X。
#    玩家从 -X 侧的通道进来，因此这里转 180°。
PITCH = 0.0
YAW = 180.0             # 模型正面本来朝 +X，转 180° 让它面对通道/玩家
ROLL = 0.0

REPORT = r"C:\Users\25227\Documents\robot_game\docs\idol_place.txt"
lines = []


def log(s):
    unreal.log("[IdolPlace] %s" % s)
    lines.append(str(s))


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(LEVEL)
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    mesh = unreal.EditorAssetLibrary.load_asset(MESH)
    if not mesh:
        log("!! 资产缺失 %s" % MESH)
        return

    # ⚠️ 实测这个模型的轴心**不在正中**：minZ=-53.87 / maxZ=+50.09，
    #    所以"脚底到轴心"是 53.87cm，不是半高。
    #    摆进关卡时 actor 的 Z 必须 = 53.87 * scale，否则会浮空或埋地。
    bb = mesh.get_bounding_box()
    height = bb.max.z - bb.min.z
    below_pivot = -bb.min.z          # 轴心到脚底的距离
    log("网格实测：高 %.2f cm，轴心到脚底 %.2f cm" % (height, below_pivot))

    # 幂等：删掉上一次摆的
    killed = 0
    for a in list(actor_sub.get_all_level_actors()):
        try:
            tags = [str(t) for t in a.get_editor_property("tags")]
        except Exception:
            continue
        if TAG in tags:
            actor_sub.destroy_actor(a)
            killed += 1
    log("清理旧的雕像 %d 个" % killed)

    z = below_pivot * SCALE
    loc = unreal.Vector(POS[0], POS[1], z)
    a = actor_sub.spawn_actor_from_class(
        unreal.StaticMeshActor, loc,
        unreal.Rotator(roll=ROLL, pitch=PITCH, yaw=YAW))
    if not a:
        log("!! spawn 失败")
        return

    c = a.static_mesh_component
    c.set_mobility(unreal.ComponentMobility.STATIC)
    c.set_static_mesh(mesh)
    a.set_actor_scale3d(unreal.Vector(SCALE, SCALE, SCALE))
    a.set_editor_property("tags", [TAG])
    a.set_actor_label("SM_IdolMech")

    # ⚠️ 旋转会改变"最低点"，所以不能直接用网格的 minZ 算 Z。
    #    这里摆完先读一次**世界包围盒**，再把 actor 抬高/压低到脚底正好 z=0。
    #    （翻转 180° 时最低点会从 -53.87 变成 -50.09，手算容易出错。）
    try:
        org, ext = a.get_actor_bounds(False)
        foot_z = org.z - ext.z
        a.set_actor_location(unreal.Vector(POS[0], POS[1], z - foot_z), False, False)
        org2, ext2 = a.get_actor_bounds(False)
        log("世界包围盒：脚底 Z=%.2f  头顶 Z=%.2f  高 %.1f cm"
            % (org2.z - ext2.z, org2.z + ext2.z, ext2.z * 2))
    except Exception as e:
        log("包围盒校正失败（沿用估算值）: %s" % e)

    final = a.get_actor_location()
    log("摆放位置 (%.0f, %.0f, %.1f)  缩放 %.2f  Rot(P=%.0f Y=%.0f R=%.0f)"
        % (final.x, final.y, final.z, SCALE, PITCH, YAW, ROLL))

    les.save_current_level()
    log("已保存关卡")

    with open(REPORT, "wb") as f:
        f.write("\n".join(lines).encode("utf-8"))
    unreal.log("IDOL_PLACE_DONE")


main()
