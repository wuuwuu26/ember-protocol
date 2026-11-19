# -*- coding: utf-8 -*-
"""全场景几何诊断：导出每个可见 StaticMeshActor 的世界包围盒。

目的：找"悬空"（底部 Z 明显高于地面）和"穿模/陷地"（底部 Z 明显低于
地面，或 bbox 与地面/其它大件重叠）。地面 Z≈0（脚 Z≈1）。

输出按 底部Z 排序 + 打标签，便于定位批次问题。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
ELL.load_level(LEVEL)

rows = []
for a in ELL.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    comp = a.static_mesh_component
    if not comp:
        continue
    try:
        sm = comp.get_editor_property("static_mesh")
    except Exception:
        try:
            sm = comp.static_mesh
        except Exception:
            sm = None
    if not sm:
        continue
    # 用 actor 的 get_actor_bounds(only_colliding_components=False)
    try:
        cen, ext = a.get_actor_bounds(False)
        zmin = cen.z - ext.z
        zmax = cen.z + ext.z
        xmin, xmax = cen.x - ext.x, cen.x + ext.x
        ymin, ymax = cen.y - ext.y, cen.y + ext.y
    except Exception:
        loc = a.get_actor_location()
        zmin = zmax = loc.z
        xmin = xmax = loc.x
        ymin = ymax = loc.y
    lbl = a.get_actor_label()
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        tags = []
    rows.append((zmin, zmax, xmin, xmax, ymin, ymax, lbl,
                 sm.get_name(), ",".join(tags),
                 a.get_actor_location(), a.get_actor_scale3d()))

rows.sort(key=lambda r: r[0])
lines = ["总 StaticMeshActor: %d" % len(rows),
         "zmin<->zmax  X  Y  | label | mesh | tags | loc | scale",
         "=" * 120]
for r in rows:
    zmin, zmax, xmin, xmax, ymin, ymax, lbl, smn, tags, loc, sc = r
    lines.append(
        "z[%7.1f,%7.1f] X[%7.0f,%7.0f] Y[%7.0f,%7.0f] | %-26s | %-22s | %-14s | loc(%.0f,%.0f,%.0f) sc(%.2f,%.2f,%.2f)"
        % (zmin, zmax, xmin, xmax, ymin, ymax, lbl[:26], smn[:22], tags[:14],
           loc.x, loc.y, loc.z, sc.x, sc.y, sc.z))

# 单独统计"底部明显离地"的（zmin>15，排除灯/管道等悬挂物由人工判断）
lines.append("")
lines.append("=== 底部 Z > 15（可能悬空，需结合标签判断）===")
for r in rows:
    if r[0] > 15:
        lines.append("  zmin=%.1f  %-28s mesh=%-20s loc(%.0f,%.0f,%.0f)"
                     % (r[0], r[6][:28], r[7][:20],
                        r[9].x, r[9].y, r[9].z))
lines.append("")
lines.append("=== 底部 Z < -15（可能陷地/穿模）===")
for r in rows:
    if r[0] < -15:
        lines.append("  zmin=%.1f  %-28s mesh=%-20s loc(%.0f,%.0f,%.0f)"
                     % (r[0], r[6][:28], r[7][:20],
                        r[9].x, r[9].y, r[9].z))

with open(r"C:\Users\25227\Documents\robot_game\docs\geom_diag.txt", "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("GEOM_DIAG_DONE count=%d" % len(rows))
