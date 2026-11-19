# -*- coding: utf-8 -*-
"""
在竞技场里生成 5 盏"光池"投光灯（PoolLight_0..4）。

为什么用编辑器脚本而不是运行时 SpawnActor：
    2026-10-25 实测，运行中 SpawnActor<ASpotLight> 出来的灯
    强度/可见/注册/影响世界 全是 1、组件位置也对，但画面**一个像素都不亮**
    （开池/关池截图的地板均值都是 0.299）。换成 SpawnActorDeferred
    在注册前设 Movable 也一样。与其继续和运行时生成较劲，
    不如走和关卡里现有 8 盏投光完全相同的路径：**编辑器里建好、存进关卡**，
    C++ 只负责在 BeginPlay 按统一参数把它们调成想要的样子。

参数（与 RobotCharacter.cpp / TuneArenaLights 保持一致）：
    位置   (±1100, ±1100, 620) + (0, 0, 620)
       620 是关键：天桥甲板在 z=700，灯必须挂在**甲板下面**，
       否则光线全被甲板挡住（第一版放在 750，等于白装）。
    强度   60000 cd  →  地面照度 ≈ 60000 / 6.2² ≈ 1560 lux
    锥角   内 12° / 外 34°  →  地面光斑半径 ≈ 4.2m
    颜色   (1.00, 0.72, 0.46) 暖白，和冷蓝月光形成色温对冲
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"

SPOTS = [
    (0.0, 0.0),
    (-1100.0, -1100.0),
    (1100.0, -1100.0),
    (-1100.0, 1100.0),
    (1100.0, 1100.0),
]
Z = 620.0


def log(m):
    unreal.log("[光池] %s" % m)


unreal.EditorLevelLibrary.load_level(LEVEL)

existing = {}
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    label = a.get_actor_label()
    if label.startswith("PoolLight"):
        existing[label] = a

for i, (x, y) in enumerate(SPOTS):
    label = "PoolLight_%d" % i
    actor = existing.get(label)
    if actor is None:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.SpotLight,
            unreal.Vector(x, y, Z),
            unreal.Rotator(0.0, -90.0, 0.0))
        actor.set_actor_label(label)
        log("新建 %s" % label)
    else:
        actor.set_actor_location(unreal.Vector(x, y, Z), False, False)
        log("更新 %s" % label)

    comp = actor.get_component_by_class(unreal.SpotLightComponent)
    if comp is None:
        log("❌ %s 没有 SpotLightComponent" % label)
        continue

    comp.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    comp.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
    comp.set_editor_property("intensity", 60000.0)
    comp.set_editor_property("attenuation_radius", 2600.0)
    comp.set_editor_property("light_color",
                             unreal.Color(r=255, g=184, b=117, a=255))
    comp.set_editor_property("inner_cone_angle", 12.0)
    comp.set_editor_property("outer_cone_angle", 34.0)
    comp.set_editor_property("cast_shadows", True)
    comp.set_editor_property("volumetric_scattering_intensity", 0.45)
    comp.set_editor_property("affects_world", True)

unreal.EditorLevelLibrary.save_current_level()
log("已保存关卡：%d 盏光池" % len(SPOTS))

# 落盘一份结果，避免依赖日志编码（中文日志在 PowerShell 里会乱码）
try:
    with open(r"C:\Users\25227\Documents\robot_game\docs\pools_result.txt", "w") as f:
        f.write("spots=%d\n" % len(SPOTS))
        for a in unreal.EditorLevelLibrary.get_all_level_actors():
            label = a.get_actor_label()
            if label.startswith("PoolLight"):
                loc = a.get_actor_location()
                f.write("%s loc=(%.0f,%.0f,%.0f)\n" % (label, loc.x, loc.y, loc.z))
        f.write("POOLS_DONE\n")
except Exception as e:
    log("写结果失败: %s" % str(e))

