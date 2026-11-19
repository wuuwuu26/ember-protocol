import json
import os
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
STATE = r"C:\Users\25227\AppData\Local\Temp\opencode\wall_mats_backup.json"
unreal.EditorLevelLibrary.load_level(LEVEL)

backup = {}
if os.path.exists(STATE):
    backup = json.load(open(STATE, "r", encoding="utf-8"))

fixed = 0
restored = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    comps = a.get_components_by_class(unreal.StaticMeshComponent)
    if not comps:
        continue
    m = comps[0].get_editor_property("static_mesh")
    if not m or "wall" not in m.get_name().lower():
        continue
    smc = comps[0]

    # 1) 恢复材质
    paths = backup.get(a.get_actor_label(), [])
    for i, p in enumerate(paths):
        if not p:
            continue
        mi = unreal.EditorAssetLibrary.load_asset(p.split(".")[0])
        if mi:
            smc.set_material(i, mi)
            restored += 1

    # 2) 把组件 Pitch 归零（原来 90° → 墙躺平埋进地板）
    rot = smc.get_editor_property("relative_rotation")
    if abs(rot.pitch) > 0.5:
        smc.set_editor_property(
            "relative_rotation",
            unreal.Rotator(pitch=0.0, yaw=rot.yaw, roll=rot.roll))
        fixed += 1

unreal.EditorLevelLibrary.save_current_level()
unreal.log("WALLFIX pitch_fixed=%d materials_restored=%d" % (fixed, restored))
unreal.log("WALLFIX_DONE")
