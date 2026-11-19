# -*- coding: utf-8 -*-
"""把 Niagara 喷泉系统挂到落水点，实际渲染验证（第一百一十五轮）。

用已落盘的 NS_TestB（FountainLightweight 副本）。
落水点：水柱 (120,300)，水面 z≈2~10。水花应从水面向上溅。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
SYS = "/Game/RobotGame/FX/NS_TestB"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\niagara_spawn.txt"

EAL = unreal.EditorAssetLibrary
out = []


def log(s):
    unreal.log("[NiagaraSpawn] %s" % s)
    out.append(str(s))


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(LEVEL)
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    system = EAL.load_asset(SYS)
    if not system:
        log("!! 系统加载失败 %s" % SYS)
        return
    log("系统 = %s (%s)" % (system.get_name(), system.get_class().get_name()))

    # 清理旧的测试 NiagaraActor
    n_old = 0
    for a in list(sub.get_all_level_actors()):
        try:
            tags = [str(t) for t in a.get_editor_property("tags")]
        except Exception:
            continue
        if "WaterSplash" in tags:
            sub.destroy_actor(a)
            n_old += 1
    log("清理旧水花 %d 个" % n_old)

    # 用 NiagaraActor（关卡里持久存在的组件宿主）
    loc = unreal.Vector(120.0, 300.0, 6.0)   # 落水点，略高于水面
    a = sub.spawn_actor_from_class(unreal.NiagaraActor, loc,
                                   unreal.Rotator(0, 0, 0))
    if not a:
        log("!! NiagaraActor 生成失败")
        return
    a.set_actor_label("NS_WaterSplash_Impact")
    a.set_editor_property("tags", ["WaterSplash"])

    comp = a.get_editor_property("niagara_component")
    if comp:
        comp.set_asset(system)
        # 自动激活
        try:
            comp.set_editor_property("auto_activate", True)
        except Exception:
            pass
        log("NiagaraComponent 已挂系统 %s" % system.get_name())
    else:
        log("!! 没拿到 NiagaraComponent")

    les.save_current_level()
    log("已保存关卡")


main()
with open(REPORT, "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("NIAGARA_SPAWN_DONE")
