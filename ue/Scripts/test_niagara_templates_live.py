# -*- coding: utf-8 -*-
"""复制多种 Niagara 系统模板并排挂到场景，找出哪个能真正出粒子。

在落水点附近横向排开 4 个不同模板的系统，平视一眼就能看出谁在喷。
"""
import unreal

EAL = unreal.EditorAssetLibrary
DIR = "/Game/RobotGame/FX"
out = []

TEMPLATES = [
    ("NS_T_SimpleExplosion", "/Niagara/DefaultAssets/Templates/Systems/SimpleExplosion.SimpleExplosion"),
    ("NS_T_RadialBurst", "/Niagara/DefaultAssets/Templates/Systems/RadialBurst.RadialBurst"),
    ("NS_T_DirBurst", "/Niagara/DefaultAssets/Templates/Systems/DirectionalBurst.DirectionalBurst"),
    ("NS_T_Minimal", "/Niagara/DefaultAssets/Templates/Systems/MinimalLightweight.MinimalLightweight"),
    ("NS_T_AttrTrails", "/Niagara/DefaultAssets/Templates/Systems/AttributeReaderTrails.AttributeReaderTrails"),
]

for name, src in TEMPLATES:
    p = DIR + "/" + name
    if EAL.does_asset_exist(p):
        EAL.delete_asset(p)
    dup = EAL.duplicate_asset(src, p)
    if dup:
        EAL.save_loaded_asset(dup)
        out.append("%-24s OK (复制保存)" % name)
    else:
        out.append("%-24s FAIL" % name)

# 在场景中沿 Y 排开（远离水渠，避免遮挡），逐个挂 NiagaraActor
LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# 清理旧的测试
for a in list(sub.get_all_level_actors()):
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        continue
    if "NiagaraTest" in tags:
        sub.destroy_actor(a)

for i, (name, _) in enumerate(TEMPLATES):
    sysm = EAL.load_asset(DIR + "/" + name)
    if not sysm:
        continue
    loc = unreal.Vector(-800.0 + i * 220.0, -1100.0, 60.0)
    a = sub.spawn_actor_from_class(unreal.NiagaraActor, loc, unreal.Rotator(0, 0, 0))
    if a:
        a.set_actor_label("NiagaraTest_" + name)
        a.set_editor_property("tags", ["NiagaraTest"])
        comp = a.get_editor_property("niagara_component")
        if comp:
            comp.set_asset(sysm)
            try:
                comp.set_editor_property("auto_activate", True)
            except Exception:
                pass
        out.append("  摆放 %s (%.0f,%.0f)" % (name, loc.x, loc.y))

les.save_current_level()
out.append("已保存")
with open(r"C:\Users\25227\Documents\robot_game\docs\niagara_templates_test.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("NIAGARA_TEMPLATES_TEST_DONE")
