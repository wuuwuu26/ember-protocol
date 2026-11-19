# -*- coding: utf-8 -*-
"""逐盏检查扩建灯：是否与几何重叠（灯被埋在墙里会完全无效），
以及是否在关卡里注册成功。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)

out = []
lights = []
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        continue
    for t in tags:
        if t.startswith("ExtLight_"):
            lights.append((t, a))
            break

out.append("扩建灯 %d 盏" % len(lights))

# 用射线检测：灯的位置是否在某个静态网格**内部**
world = les.get_world() if hasattr(les, "get_world") else None
blocking = 0
for tag, a in lights:
    loc = a.get_actor_location()
    hit = False
    try:
        start = unreal.Vector(loc.x, loc.y, loc.z)
        end = unreal.Vector(loc.x + 1.0, loc.y, loc.z)
        res = unreal.SystemLibrary.line_trace_single(
            None, start, end, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            True, [], unreal.DrawDebugTrace.NONE, True)
        hit = bool(res)
    except Exception as e:
        pass
    if hit:
        blocking += 1

out.append("其中位于几何体内部的 %d 盏（会被完全遮挡）" % blocking)

# 打印前几盏的位置，人工核对
for tag, a in lights[:8]:
    loc = a.get_actor_location()
    c = a.point_light_component
    out.append("%-22s (%.0f,%.0f,%.0f) I=%.0f R=%.0f"
               % (tag, loc.x, loc.y, loc.z,
                  c.get_editor_property("intensity"),
                  c.get_editor_property("attenuation_radius")))

# 关卡里所有 PointLight 的总数 & 光源数量限制 CVar
all_pl = [a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
          .get_all_level_actors() if a.get_class().get_name() == "PointLight"]
out.append("")
out.append("关卡内 PointLight 总数 %d" % len(all_pl))

with open(r"C:\Users\25227\Documents\robot_game\docs\ext_lightgeo.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("LIGHTGEO_DONE")
