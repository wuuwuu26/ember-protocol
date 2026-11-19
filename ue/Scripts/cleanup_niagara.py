# -*- coding: utf-8 -*-
"""清理 Niagara 探测过程的所有测试残留，恢复场景。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
DIR = "/Game/RobotGame/FX"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary
out = []

# 删测试 actor
n = 0
for a in list(sub.get_all_level_actors()):
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        continue
    if "NiagaraTest" in tags or "WaterSplash" in tags:
        sub.destroy_actor(a)
        n += 1
out.append("删除测试 actor %d 个" % n)

# 删测试系统资产
for name in ("NS_TestA", "NS_TestB", "NS_TestC", "NS_WaterSplash",
             "NS_T_SimpleExplosion", "NS_T_RadialBurst", "NS_T_DirBurst",
             "NS_T_Minimal", "NS_T_AttrTrails"):
    p = DIR + "/" + name
    if EAL.does_asset_exist(p):
        EAL.delete_asset(p)
        out.append("删除资产 %s" % name)

les.save_current_level()
out.append("已保存关卡")
with open(r"C:\Users\25227\Documents\robot_game\docs\niagara_cleanup.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("NIAGARA_CLEANUP_DONE")
