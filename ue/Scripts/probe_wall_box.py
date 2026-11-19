import unreal
import math

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)

out = []
rows = []
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    comps = a.get_components_by_class(unreal.StaticMeshComponent)
    if not comps:
        continue
    m = comps[0].get_editor_property("static_mesh")
    if not m or m.get_name().lower() != "sm_wall_segment":
        continue
    loc = a.get_actor_location()
    rot = a.get_actor_rotation()
    sc = a.get_actor_scale3d()
    b = m.get_bounds()
    # 网格局部盒 8 角 -> 世界
    ex, ey, ez = b.box_extent.x * sc.x, b.box_extent.y * sc.y, b.box_extent.z * sc.z
    ox, oy, oz = b.origin.x * sc.x, b.origin.y * sc.y, b.origin.z * sc.z
    yaw = math.radians(rot.yaw)
    cy, sy = math.cos(yaw), math.sin(yaw)
    xs, ys, zs = [], [], []
    for dx in (-1, 1):
        for dy in (-1, 1):
            for dz in (-1, 1):
                lx = ox + dx * ex
                ly = oy + dy * ey
                lz = oz + dz * ez
                wx = loc.x + lx * cy - ly * sy
                wy = loc.y + lx * sy + ly * cy
                wz = loc.z + lz
                xs.append(wx); ys.append(wy); zs.append(wz)
    rows.append((loc.x, loc.y, rot.yaw,
                 min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))

rows.sort(key=lambda r: (r[0], r[1]))
out.append("wall segments=%d" % len(rows))
out.append("locX    locY   yaw   |  worldX范围        worldY范围        z范围")
for r in rows:
    out.append("%7.1f %7.1f %5.1f | %8.1f..%8.1f %8.1f..%8.1f %6.1f..%6.1f" % r)

open(r"C:\Users\25227\AppData\Local\Temp\opencode\wallbox.txt", "w",
     encoding="utf-8").write("\n".join(out))
unreal.log("WALLBOX_OK")
