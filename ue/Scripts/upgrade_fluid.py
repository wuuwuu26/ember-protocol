# -*- coding: utf-8 -*-
"""开启/增强落水点的物理流体效果（第一百一十四轮）。

现状：CoolantSpill_0 的 bInflow=true、InflowLocal=(-330,0) 已对准水柱，
但 InflowStrength=1.3 / MaxHeight=5cm 太弱，且三个静态 Splash 装饰片
盖在落点上，把物理涟漪遮住了 → 看起来"假"。

修法：
  1) 隐藏三个静态装饰片（Splash_FoamRing/Disc/SprayCone）——
     落水效果改由真实模拟承担
  2) 增强注水脉冲：强度 1.3 -> 3.2，间隔 0.10 -> 0.06s（更连续）
  3) MaxHeight 5 -> 9cm（涟漪更明显但不尖刺）
  4) InflowRadius 62 -> 45cm（更集中的落点凹陷）
  5) 提高网格密度 GridCells 72 -> 96（涟漪更细腻）

⚠️ 只改 CoolantSpill_0（长方形水渠），4 个毒液池保持死水。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\fluid_upgrade.txt"

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lines = []


def log(s):
    unreal.log("[FluidUpgrade] %s" % s)
    lines.append(str(s))


# 1. 隐藏静态装饰片
HIDE = ("Splash_FoamRing", "Splash_FoamDisc", "Splash_SprayCone")
n_hide = 0
for a in sub.get_all_level_actors():
    if a.get_actor_label() in HIDE and a.get_class().get_name() == "StaticMeshActor":
        c = a.static_mesh_component
        c.set_editor_property("visible", False)
        c.set_editor_property("hidden_in_game", True)
        n_hide += 1
        log("隐藏静态装饰 %s" % a.get_actor_label())
log("共隐藏 %d 个" % n_hide)

# 2. 增强物理注水
n_field = 0
for a in sub.get_all_level_actors():
    if a.get_class().get_name() != "RobotCoolantField":
        continue
    if a.get_actor_label() != "CoolantSpill_0":
        continue
    try:
        a.set_editor_property("InflowStrength", 3.2)
        a.set_editor_property("InflowInterval", 0.06)
        a.set_editor_property("InflowRadius", 45.0)
        a.set_editor_property("MaxHeight", 9.0)
        a.set_editor_property("GridCells", 96)
        log("CoolantSpill_0 物理参数：强度3.2 间隔0.06 半径45 最大起伏9cm 网格96")
        n_field += 1
    except Exception as e:
        log("!! 参数设置失败 %s" % str(e)[:70])

les.save_current_level()
log("已保存关卡")

with open(REPORT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("FLUID_UPGRADE_DONE")
