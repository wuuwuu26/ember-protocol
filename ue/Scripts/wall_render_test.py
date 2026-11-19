import json
import os
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ENV = "/Game/RobotGame/Art/Environment"
STATE = r"C:\Users\25227\AppData\Local\Temp\opencode\wall_mats_backup.json"

mode = os.environ.get("WALLTEST", "apply")
unreal.EditorLevelLibrary.load_level(LEVEL)

targets = []
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    comps = a.get_components_by_class(unreal.StaticMeshComponent)
    if not comps:
        continue
    m = comps[0].get_editor_property("static_mesh")
    if not m or "wall" not in m.get_name().lower():
        continue
    targets.append((a.get_actor_label(), comps[0]))

if mode == "apply":
    backup = {}
    for lab, smc in targets:
        n = smc.get_num_materials()
        backup[lab] = []
        for i in range(n):
            mi = smc.get_material(i)
            backup[lab].append(mi.get_path_name() if mi else None)
    json.dump(backup, open(STATE, "w", encoding="utf-8"))
    bright = unreal.EditorAssetLibrary.load_asset(ENV + "/M_Core_wall")
    for lab, smc in targets:
        smc.set_material(0, bright)
    unreal.EditorLevelLibrary.save_current_level()
    unreal.log("WALLTEST applied to %d" % len(targets))
else:
    backup = json.load(open(STATE, "r", encoding="utf-8"))
    for lab, smc in targets:
        paths = backup.get(lab, [])
        for i, p in enumerate(paths):
            if not p:
                continue
            mi = unreal.EditorAssetLibrary.load_asset(p.split(".")[0])
            if mi:
                smc.set_material(i, mi)
    unreal.EditorLevelLibrary.save_current_level()
    unreal.log("WALLTEST restored %d" % len(targets))

unreal.log("WALLTEST_DONE")
