# -*- coding: utf-8 -*-
"""列出所有 MechWreck / 碎骸相关 actor 的当前位置、缩放、bbox 底 Z，
检查是否有重复残留 / 悬空。"""
import unreal
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
ELL.load_level(LEVEL)
lines = []
def log(s):
    unreal.log("[WreckList] %s" % s)
    lines.append(str(s))

cnt = 0
for a in ELL.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        tags = []
    comp = a.static_mesh_component
    sm = None
    if comp:
        try:
            sm = comp.get_editor_property("static_mesh")
        except Exception:
            pass
    mn = sm.get_name() if sm else "?"
    # 碎骸判定：tag 含 MechWreck 或 mesh 名含 wreck/debris/armor/head
    isw = ("MechWreck" in tags or
           any(k in mn.lower() for k in ("wreck", "severed", "armor_debris",
                                          "mech_head", "mech_torso")))
    if not isw:
        continue
    cnt += 1
    loc = a.get_actor_location()
    sc = a.get_actor_scale3d()
    try:
        cen, ext = a.get_actor_bounds(False)
        zmin = cen.z - ext.z
    except Exception:
        zmin = -999
    log("%-24s mesh=%-26s loc=(%.0f,%.0f,%.0f) sc=%.2f zmin=%.1f tags=%s"
        % (a.get_actor_label()[:24], mn[:26], loc.x, loc.y, loc.z,
           sc.x, zmin, ",".join(tags)))
log("碎骸类 actor 总数: %d" % cnt)
with open(r"C:\Users\25227\Documents\robot_game\docs\wreck_list.txt", "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("WRECK_LIST_DONE")
