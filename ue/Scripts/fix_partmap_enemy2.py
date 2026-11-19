"""修 DA_PartMap_Enemy 的腿规则前缀（第二版：改完立刻读回校验）。

敌人骨架已改为 thigh_/shin_/foot_ 分节命名，旧前缀 leg_L/leg_R 匹配不上，
断腿时部件不会消失。这里改成覆盖三段骨 + 四足 BL/BR，并保留 leg_ 兼容。
"""
import unreal

PATH = "/Game/RobotGame/Data/Enemies/DA_PartMap_Enemy"
EAL = unreal.EditorAssetLibrary

WANT = {
    "leg_L": ["thigh_L", "shin_L", "foot_L", "thigh_BL", "shin_BL", "foot_BL", "leg_L"],
    "leg_R": ["thigh_R", "shin_R", "foot_R", "thigh_BR", "shin_BR", "foot_BR", "leg_R"],
}

pm = EAL.load_asset(PATH)
rules = pm.get_editor_property("rules")
print("[fix] 改前规则数=%d" % len(rules))

for i, r in enumerate(rules):
    prefixes = [str(p) for p in r.get_editor_property("bone_prefixes")]
    key = prefixes[0] if prefixes else ""
    if key in WANT:
        rules[i].set_editor_property(
            "bone_prefixes", [unreal.Name(p) for p in WANT[key]])

pm.set_editor_property("rules", rules)
EAL.save_loaded_asset(pm)
EAL.save_asset(PATH, only_if_is_dirty=False)

# 读回校验
pm2 = EAL.load_asset(PATH)
ok = 0
for r in pm2.get_editor_property("rules"):
    prefixes = [str(p) for p in r.get_editor_property("bone_prefixes")]
    print("[fix] 读回: %s" % prefixes)
    if "thigh_L" in prefixes or "thigh_R" in prefixes:
        ok += 1
print("PARTMAP_FIX2_OK verified=%d" % ok)
