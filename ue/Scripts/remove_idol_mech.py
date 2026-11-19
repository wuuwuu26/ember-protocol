# -*- coding: utf-8 -*-
"""移除关卡里的 IdolMech 机甲雕像（第一百零九轮）。

用户："把之前的机甲模型移除" —— 指中央龙门架下那个 9.36m 的
SM_IdolMech 摆件（第一百零三轮导入）。

只删关卡里的 **actor**（带 IdolMech tag），保留 /Game 下的资产
（SM_IdolMech / 材质），万一以后想恢复还能拖回来。
幂等：没有则跳过。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
TAG = "IdolMech"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\remove_idol.txt"

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

out = []
killed = 0
for a in list(actor_sub.get_all_level_actors()):
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        continue
    # 既按 tag 也按 label/mesh 名兜底，确保清干净
    label = a.get_actor_label()
    is_idol = TAG in tags or "idol" in label.lower()
    if not is_idol:
        c = a.static_mesh_component if a.get_class().get_name() == "StaticMeshActor" else None
        m = c.get_editor_property("static_mesh") if c else None
        is_idol = bool(m and "idol" in m.get_name().lower())
    if is_idol:
        loc = a.get_actor_location()
        out.append("删除 %s  (%.0f, %.0f, %.1f) tags=%s" %
                   (label, loc.x, loc.y, loc.z, tags))
        actor_sub.destroy_actor(a)
        killed += 1

les.save_current_level()
out.insert(0, "共删除 %d 个 IdolMech actor" % killed)
out.append("已保存关卡（资产保留）")
with open(REPORT, "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
for l in out:
    unreal.log("[RemoveIdol] %s" % l)
unreal.log("REMOVE_IDOL_DONE")
