# -*- coding: utf-8 -*-
"""查清两件事（第一百零三轮）：
1) 摆在关卡里的雕像实际的 (Pitch, Yaw, Roll) 是多少
2) unreal.Rotator(a, b, c) 的三个位置参数到底对应哪个轴
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)

out = []

# ── 1. 在读回的 Rotator 上看属性名 ──
r = unreal.Rotator(10.0, 20.0, 30.0)
out.append("unreal.Rotator(10, 20, 30) 读回：")
out.append("  pitch=%.1f  yaw=%.1f  roll=%.1f" % (r.pitch, r.yaw, r.roll))
out.append("  → 三个位置参数依次对应上面的顺序（自己看哪个是 10/20/30）")

# ── 2. 关卡的雕像当前旋转 ──
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        continue
    if "IdolMech" in tags:
        rot = a.get_actor_rotation()
        loc = a.get_actor_location()
        sc = a.get_actor_scale3d()
        out.append("")
        out.append("雕像实例 %s" % a.get_actor_label())
        out.append("  loc=(%.1f, %.1f, %.1f)  scale=(%.2f, %.2f, %.2f)"
                   % (loc.x, loc.y, loc.z, sc.x, sc.y, sc.z))
        out.append("  pitch=%.1f  yaw=%.1f  roll=%.1f" % (rot.pitch, rot.yaw, rot.roll))
        # 世界包围盒（判断是否上下颠倒：比较上下半的体积不方便，
        # 但可以看包围盒中心是否接近 loc.z）
        org, ext = a.get_actor_bounds(False)
        out.append("  world bounds: centerZ=%.1f extentZ=%.1f  → 脚底 %.1f 头顶 %.1f"
                   % (org.z, ext.z, org.z - ext.z, org.z + ext.z))

with open(r"C:\Users\25227\Documents\robot_game\docs\idol_rot.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("IDOL_ROT_DONE")
