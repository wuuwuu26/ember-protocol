# -*- coding: utf-8 -*-
"""探针：精确定位地板所用的 Actor、StaticMesh、材质槽与 MaterialInstance。"""
import unreal

L = "[地面探针]"
unreal.log(L + " start")
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
world = unreal.EditorLevelLibrary.get_editor_world()

out = []


def record(msg):
    out.append(msg)
    unreal.log(L + " " + msg)


record("=== 1. 射线检测 ===")
for x, y in ((0, 0), (500, 500), (-500, -500), (0, 1000)):
    try:
        start = unreal.Vector(x, y, 200.0)
        end = unreal.Vector(x, y, -200.0)
        hit_tuple = unreal.SystemLibrary.line_trace_single(
            world, start, end,
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            False, [], unreal.DrawDebugTrace.NONE, True)

        b_hit = hit_tuple[0]
        hit_res = hit_tuple[1]
        if not b_hit:
            record("坐标 (%d,%d) 无命中" % (x, y))
            continue

        actor = hit_res.get_actor() if hasattr(hit_res, "get_actor") else None
        comp = hit_res.get_component() if hasattr(hit_res, "get_component") else None
        loc = hit_res.get_editor_property("impact_point")

        actor_name = actor.get_actor_label() if actor else "None"
        comp_name = comp.get_name() if comp else "None"

        # 读取材质
        mat_names = []
        if comp and hasattr(comp, "get_num_materials"):
            for i in range(comp.get_num_materials()):
                m = comp.get_material(i)
                mat_names.append(m.get_path_name() if m else "None")

        mesh_name = "None"
        if comp and hasattr(comp, "get_editor_property"):
            try:
                sm = comp.get_editor_property("static_mesh")
                if sm:
                    mesh_name = sm.get_path_name()
            except Exception:
                pass

        record("命中 (%d,%d) Z=%.1f actor=%s mesh=%s comp_mats=%s" % (
            x, y, loc.z if loc else 0.0, actor_name, mesh_name, mat_names))
    except Exception as e:
        record("坐标 (%d,%d) 探测异常: %s" % (x, y, str(e)))

record("\n=== 2. 关卡内 Z <= 50 且 X/Y 覆盖原点的大型静态网格 ===")
actors = unreal.EditorLevelLibrary.get_all_level_actors()
floor_candidates = []
for a in actors:
    if not isinstance(a, unreal.StaticMeshActor):
        continue
    comp = a.static_mesh_component
    if not comp or not comp.static_mesh:
        continue
    loc = a.get_actor_location()
    origin, box_extent = a.get_actor_bounds(False)
    # 覆盖中心区域、Z 接近 0 的平面
    if origin.z < 100 and box_extent.x > 300 and box_extent.y > 300:
        mats = []
        for i in range(comp.get_num_materials()):
            m = comp.get_material(i)
            mats.append(m.get_path_name() if m else "None")
        floor_candidates.append(
            "label=%s mesh=%s loc=(%.0f,%.0f,%.0f) extent=(%.0f,%.0f,%.0f) mats=%s" % (
                a.get_actor_label(), comp.static_mesh.get_path_name(),
                loc.x, loc.y, loc.z, box_extent.x, box_extent.y, box_extent.z, mats))

for c in sorted(floor_candidates):
    record(c)

with open(r"C:\Users\25227\Documents\robot_game\docs\floor_hit.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
    f.write("\nFLOORHIT_DONE\n")

unreal.log(L + " finished")
