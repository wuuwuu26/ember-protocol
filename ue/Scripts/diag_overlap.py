# -*- coding: utf-8 -*-
"""包围盒两两相交检测（找穿模）。跳过结构件（墙/地面/柱/SkyDome/背景），
只看道具/碎骸/掩体类。输出重叠体积较大的 actor 对。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
ELL.load_level(LEVEL)

SKIP_MESH = ("Sphere", "sm_wall", "SM_Env_Floor", "SM_Env_Pillar",
             "SM_Env_Catwalk", "sm_bg_", "SM_Env_Doorframe",
             "SM_Env_Gantry", "Cube", "Cylinder", "Cone")
SKIP_LABEL = ("SkyDome", "BG_", "POSTER_", "StaticMeshActor", "Pipe_",
              "Inlet_", "Basin_", "Jet_", "Splash_", "Splash",
              "墙", "地面", "柱", "龙门", "天桥")

items = []
for a in ELL.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    lbl = a.get_actor_label()
    comp = a.static_mesh_component
    if not comp:
        continue
    try:
        sm = comp.get_editor_property("static_mesh")
    except Exception:
        continue
    if not sm:
        continue
    mn = sm.get_name()
    if any(k in mn for k in SKIP_MESH) or any(k in lbl for k in SKIP_LABEL):
        continue
    try:
        cen, ext = a.get_actor_bounds(False)
    except Exception:
        continue
    box = (cen.x - ext.x, cen.x + ext.x, cen.y - ext.y, cen.y + ext.y,
           cen.z - ext.z, cen.z + ext.z)
    # 只保留有一定体积的
    if ext.x < 5 or ext.y < 5:
        continue
    tags = [str(t) for t in a.get_editor_property("tags")]
    items.append((lbl, mn, ",".join(tags), box, ext, a.get_actor_location()))

lines = ["参与检测道具数: %d" % len(items), ""]
pairs = []
for i in range(len(items)):
    for j in range(i + 1, len(items)):
        a, b = items[i], items[j]
        ba, bb = a[3], b[3]
        ox = min(ba[1], bb[1]) - max(ba[0], bb[0])
        oy = min(ba[3], bb[3]) - max(ba[2], bb[2])
        oz = min(ba[5], bb[5]) - max(ba[4], bb[4])
        if ox > 8 and oy > 8 and oz > 8:
            vol = ox * oy * oz
            pairs.append((vol, ox, oy, oz, a, b))
pairs.sort(key=lambda p: -p[0])
lines.append("=== 包围盒相交对（重叠体积降序，前 40）===")
for vol, ox, oy, oz, a, b in pairs[:40]:
    lines.append("重叠(%4.0f×%4.0f×%4.0f=%.0f) %s[%s] @%s  ×  %s[%s] @%s"
                 % (ox, oy, oz, vol, a[0][:22], a[2][:10],
                    "%.0f,%.0f,%.0f" % (a[5].x, a[5].y, a[5].z),
                    b[0][:22], b[2][:10],
                    "%.0f,%.0f,%.0f" % (b[5].x, b[5].y, b[5].z)))
lines.append("")
lines.append("=== 涉及 MechWreck 碎骸的相交 ===")
for vol, ox, oy, oz, a, b in pairs:
    if "MechWreck" in a[2] or "MechWreck" in b[2]:
        lines.append("重叠(%3.0f×%3.0f×%3.0f) %s[%s]  ×  %s[%s]"
                     % (ox, oy, oz, a[0][:22], a[2][:12], b[0][:22], b[2][:12]))

with open(r"C:\Users\25227\Documents\robot_game\docs\overlap_diag.txt", "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("OVERLAP_DIAG_DONE items=%d pairs=%d" % (len(items), len(pairs)))
