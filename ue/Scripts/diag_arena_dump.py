# -*- coding: utf-8 -*-
"""综合诊断：机体材质槽 + 关卡布局（用于找穿模与空地）。"""
import json
import unreal

OUT_JSON = r"C:\Users\25227\Documents\robot_game\docs\arena_dump.json"
lines = []


def log(s):
    unreal.log("[Diag2] " + s)
    lines.append(s)


# ── 1. 机体材质槽（混合模式）──
sk = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Characters/SK_Chassis_Light")
if sk:
    mats = sk.get_editor_property("materials")
    for idx, m in enumerate(mats):
        mi = m.get_editor_property("material_interface")
        path = mi.get_path_name() if mi else None
        blend = "?"
        if path:
            mat = unreal.EditorAssetLibrary.load_asset(path)
            try:
                blend = str(mat.get_editor_property("blend_mode"))
            except Exception as e:
                blend = "err:" + str(e)[:40]
        log(f"slot{idx} {m.get_editor_property('material_slot_name')} -> {path} blend={blend}")

# ── 2. 关卡布局 ──
actors = unreal.EditorLevelLibrary.get_all_level_actors()
log(f"actors={len(actors)}")

dump = []
for a in actors:
    try:
        label = a.get_actor_label()
        cls = a.get_class().get_name()
        loc = a.get_actor_location()
        try:
            origin, extent = a.get_actor_bounds(False)
        except Exception:
            origin, extent = loc, unreal.Vector(0, 0, 0)
        item = {
            "label": label,
            "class": cls,
            "x": round(loc.x, 1),
            "y": round(loc.y, 1),
            "z": round(loc.z, 1),
            "bx": round(origin.x, 1),
            "by": round(origin.y, 1),
            "bz": round(origin.z, 1),
            "ex": round(extent.x, 1),
            "ey": round(extent.y, 1),
            "ez": round(extent.z, 1),
        }
        dump.append(item)
    except Exception:
        pass

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(dump, f, ensure_ascii=False, indent=1)

with open(r"C:\Users\25227\Documents\robot_game\docs\diag2.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\nARENA_DUMP_OK\n")
unreal.log("ARENA_DUMP_OK")
