# -*- coding: utf-8 -*-
"""
在竞技场里建一盏"英雄补光"（HeroFill）。

为什么要有它：
    第三人称视角下，玩家的机体几乎总是背对太阳 —— 镜头看到的那一面
    全在阴影里，只剩一团黑剪影。RobotCharacter.cpp 里本来就写了
    "挂一盏跟随玩家、不投影的冷白点光"，但那是运行时 SpawnActor 出来的，
    **本工程的运行时生成灯完全不参与渲染**（见 arena_pools.py 顶部说明），
    所以这盏灯从第一天起就没有亮过。

做法：
    走和 PoolLight 完全相同的路径 —— 编辑器里建好存进关卡，C++ 只负责
    每帧把它挪到"镜头这一侧"的合适位置（灯是 Movable，移动关卡灯正常）。

参数：
    强度   9000 cd  →  3m 处约 1000 lux，只有月光(1800 lux)的一半多一点，
                      职责是"把暗部抬起来"，不是"再打一盏主光"
    半径   1900 cm  →  只覆盖玩家周围，照不到场地别处
    颜色   (0.82, 0.90, 1.00) 冷白，和暖色光池对冲，别让机体变成橙色
    阴影   关 —— 补光开阴影会和光池的投影打架，且这里不需要方向感
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
LABEL = "HeroFill"
TAG = "HeroFill"

unreal.EditorLevelLibrary.load_level(LEVEL)


def log(m):
    unreal.log("[英雄补光] %s" % m)


actor = None
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == LABEL:
        actor = a
        break

if actor is None:
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PointLight,
        unreal.Vector(0.0, 0.0, 350.0),
        unreal.Rotator(0.0, 0.0, 0.0))
    actor.set_actor_label(LABEL)
    log("新建 %s" % LABEL)
else:
    log("更新 %s" % LABEL)

# Actor.tags 是 UPROPERTY，没有 set_actor_tags 这个 Python 方法
actor.set_editor_property("tags", [TAG])

comp = actor.get_component_by_class(unreal.PointLightComponent)
if comp is None:
    log("❌ 没有 PointLightComponent")
    raise SystemExit(1)

comp.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
comp.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
comp.set_editor_property("intensity", 9000.0)
comp.set_editor_property("attenuation_radius", 1900.0)
comp.set_editor_property("light_color",
                         unreal.Color(r=209, g=230, b=255, a=255))
comp.set_editor_property("cast_shadows", False)
comp.set_editor_property("volumetric_scattering_intensity", 0.0)
comp.set_editor_property("affects_world", True)

unreal.EditorLevelLibrary.save_current_level()
log("已保存关卡")

try:
    with open(r"C:\Users\25227\Documents\robot_game\docs\herofill_result.txt",
              "w") as f:
        loc = actor.get_actor_location()
        f.write("label=%s loc=(%.0f,%.0f,%.0f)\n"
                % (LABEL, loc.x, loc.y, loc.z))
        f.write("HEROFILL_DONE\n")
except Exception as e:
    log("写结果失败: %s" % str(e))
