"""
创建一个最简对照关卡，用于判断黑屏是"我的内容问题"还是"引擎/驱动问题"
================================================================
关卡内容只有：
  - 一个引擎自带立方体（缩放 10 倍，放在原点）
  - 可移动的平行光 + 天光 + 大气
  - PlayerStart

如果这个关卡也全黑 → 问题在引擎/驱动层面，与我们的资产无关
如果这个关卡正常 → 问题在我们的关卡或导入的资产上

用法:
    UnrealEditor-Cmd.exe <项目> -unattended -nopause -nosplash \
      -ExecutePythonScript="<本文件>" -log
"""

import unreal

LEVEL_PATH = "/Game/RobotGame/Maps/_MinTest"


def log(m):
    unreal.log("[最简关卡] %s" % m)
    print("[最简关卡] %s" % m)


def load(p):
    try:
        return unreal.EditorAssetLibrary.load_asset(p)
    except Exception:
        return None


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # 已存在就删掉重建
    if unreal.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
        try:
            unreal.EditorAssetLibrary.delete_asset(LEVEL_PATH)
        except Exception as e:
            log("删除旧关卡失败: %s" % str(e)[:60])

    try:
        les.new_level(LEVEL_PATH)
    except Exception as e:
        log("❌ 新建关卡失败: %s" % str(e)[:80])
        return

    # ── 引擎自带立方体，缩放 10 倍（10 米）──
    cube_mesh = load("/Engine/BasicShapes/Cube.Cube")
    if not cube_mesh:
        log("❌ 引擎立方体加载失败")
        return

    cube = actor_sub.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(500.0, 0.0, 0.0),
        unreal.Rotator(0, 0, 0))
    if cube:
        cube.static_mesh_component.set_static_mesh(cube_mesh)
        cube.set_actor_scale3d(unreal.Vector(10.0, 10.0, 0.2))  # 压扁当地面
        log("✅ 立方体已放置（10m×10m 地面）")

    # ── 光照 ──
    sun = actor_sub.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0, 0, 1000),
        unreal.Rotator(-45, 30, 0))
    if sun:
        for prop in ("light_component", "directional_light_component"):
            try:
                lc = sun.get_editor_property(prop)
            except Exception:
                continue
            if not lc:
                continue
            lc.set_mobility(unreal.ComponentMobility.MOVABLE)
            lc.set_editor_property("intensity", 100000.0)
            log("✅ 平行光 Movable / 100000 lux")
            break

    if hasattr(unreal, "SkyAtmosphere"):
        actor_sub.spawn_actor_from_class(
            unreal.SkyAtmosphere, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
        log("✅ 大气已放置")

    sky = actor_sub.spawn_actor_from_class(
        unreal.SkyLight, unreal.Vector(0, 0, 500))
    if sky:
        for prop in ("light_component", "sky_light_component"):
            try:
                lc = sky.get_editor_property(prop)
            except Exception:
                continue
            if not lc:
                continue
            lc.set_mobility(unreal.ComponentMobility.MOVABLE)
            lc.set_editor_property("intensity", 1.0)
            lc.set_editor_property("real_time_capture", True)
            log("✅ 天光 Movable / 实时捕获")
            break

    # ── 玩家出生点 ──
    actor_sub.spawn_actor_from_class(
        unreal.PlayerStart, unreal.Vector(0.0, 0.0, 150.0), unreal.Rotator(0, 0, 0))
    log("✅ 出生点已放置")

    try:
        les.save_current_level()
        log("✅ 关卡已保存：%s" % LEVEL_PATH)
    except Exception as e:
        log("保存失败: %s" % str(e)[:60])

    log("完成")


main()
