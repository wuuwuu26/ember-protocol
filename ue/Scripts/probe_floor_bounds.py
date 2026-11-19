# -*- coding: utf-8 -*-
"""查地面块的世界包围盒，找接缝真正的原因。
SM_Env_Floor 的网格包围盒是 400x400x42，min=(-200,-200,-30)。
若某些块的缩放不是 1，或旋转后尺寸变了，接缝就会出现。
同时统计每个块的 actor 缩放与旋转。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)

out = []
bad = []
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    c = a.static_mesh_component
    m = c.get_editor_property("static_mesh") if c else None
    if not m or "floor" not in m.get_name().lower():
        continue
    loc = a.get_actor_location()
    sc = a.get_actor_scale3d()
    rot = a.get_actor_rotation()
    if abs(sc.x - 1.0) > 1e-4 or abs(sc.y - 1.0) > 1e-4:
        bad.append("scale %s at (%.0f,%.0f)" % (sc, loc.x, loc.y))
    if abs(rot.yaw) > 1e-4 or abs(rot.pitch) > 1e-4 or abs(rot.roll) > 1e-4:
        bad.append("rot %s at (%.0f,%.0f)" % (rot, loc.x, loc.y))
    # 世界包围盒
    try:
        bb = a.get_editor_property("static_mesh_component").bounds
        box = bb.get_editor_property("box_extent")
        org = bb.get_editor_property("origin")
        out.append("%.0f,%.0f  extent=(%.2f,%.2f,%.2f) origin=(%.2f,%.2f,%.2f)"
                   % (loc.x, loc.y, box.x, box.y, box.z, org.x, org.y, org.z))
    except Exception:
        pass

lines = ["floor actors: %d" % len(out), "anomalies: %d" % len(bad)]
lines += bad[:20]
lines.append("")
lines.append("== 前 8 块的世界包围盒 ==")
lines += out[:8]
lines.append("")
lines.append("== 关键：X=1600 与 X=2000 两块（原区域与新区域的交界）==")
for s in out:
    if s.startswith("1600,") or s.startswith("2000,"):
        lines.append(s)

with open(r"C:\Users\25227\Documents\robot_game\docs\ext_floor3.txt", "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("EXT_FLOOR3_DONE")
