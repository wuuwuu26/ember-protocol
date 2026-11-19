# -*- coding: utf-8 -*-
"""决定性测试：把 RadialBurst 系统放到玩家出生点正前方，正常游戏相机拍。"""
import unreal

EAL = unreal.EditorAssetLibrary
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# 清掉旧的测试排
for a in list(sub.get_all_level_actors()):
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        continue
    if "NiagaraTest" in tags or "WaterSplash" in tags:
        sub.destroy_actor(a)

# 玩家出生 (-200,0,130) 朝 +X，放在正前方几个位置
PLACES = [
    ("NS_T_RadialBurst", -50, 0, 100),
    ("NS_T_SimpleExplosion", 100, -150, 100),
    ("NS_T_DirBurst", 100, 150, 100),
    ("NS_T_Minimal", 250, 0, 100),
]
out = []
for name, x, y, z in PLACES:
    sysm = EAL.load_asset("/Game/RobotGame/FX/" + name)
    if not sysm:
        out.append("%s 缺失" % name)
        continue
    a = sub.spawn_actor_from_class(unreal.NiagaraActor,
        unreal.Vector(float(x), float(y), float(z)), unreal.Rotator(0, 0, 0))
    if a:
        a.set_actor_label("NSNear_" + name)
        a.set_editor_property("tags", ["NiagaraTest"])
        c = a.get_editor_property("niagara_component")
        if c:
            c.set_asset(sysm)
            try:
                c.set_editor_property("auto_activate", True)
            except Exception:
                pass
        out.append("放 %s (%.0f,%.0f,%.0f)" % (name, x, y, z))

les.save_current_level()
out.append("已保存")
with open(r"C:\Users\25227\Documents\robot_game\docs\niagara_near.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("NIAGARA_NEAR_DONE")
