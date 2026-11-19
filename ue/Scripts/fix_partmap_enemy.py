"""修 DA_PartMap_Enemy：敌人骨架已改成 thigh_/shin_/foot_ 分节命名，
腿规则的旧前缀 leg_L / leg_R 匹配不上任何骨骼 → 断腿时部件不会消失。
改成覆盖三个前缀（同时保留 leg_ 兼容旧资产）。"""
import unreal

PATH = "/Game/RobotGame/Data/Enemies/DA_PartMap_Enemy"
EAL = unreal.EditorAssetLibrary
pm = EAL.load_asset(PATH)
rules = pm.get_editor_property("rules")

UPDATED = {
    "leg_L": ["thigh_L", "shin_L", "foot_L", "thigh_BL", "shin_BL", "foot_BL", "leg_L"],
    "leg_R": ["thigh_R", "shin_R", "foot_R", "thigh_BR", "shin_BR", "foot_BR", "leg_R"],
}

for r in rules:
    prefixes = [str(p) for p in r.get_editor_property("bone_prefixes")]
    key = prefixes[0] if prefixes else ""
    if key in UPDATED:
        new = [unreal.Name(p) for p in UPDATED[key]]
        r.set_editor_property("bone_prefixes", new)
        unreal.log("[pm] %s -> %s" % (key, [str(x) for x in new]))

pm.set_editor_property("rules", rules)
EAL.save_loaded_asset(pm)
print("PARTMAP_FIX_OK")
