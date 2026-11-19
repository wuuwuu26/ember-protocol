"""
直接在编辑器里修复：把所有静态网格体改为 Movable 并构建光照
================================================================
编辑器红字「光照需要重建（52 未构建对象）」指出：
脚本生成的 StaticMeshActor 组件 Mobility 是 Static，而关卡从未烘焙过光照
→ Static 网格体拿不到光照 → 渲染成纯黑。

运行时改 Mobility 的效果不稳定，这里直接在编辑器里改并保存。

同时执行一次 Build Lighting，让所有 Static 网格体拿到光照。

用法:
    UnrealEditor-Cmd.exe <项目> -unattended -nopause -nosplash \
      -ExecutePythonScript="<本文件>" -log
"""

import unreal

LEVEL_PATH = "/Game/RobotGame/Maps/Persistent/L_TestArena"


def log(m):
    unreal.log("[修复] %s" % m)
    print("[修复] %s" % m)


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(LEVEL_PATH)
    log("关卡已加载")

    actors = unreal.EditorLevelLibrary.get_all_level_actors()

    # ── 1. 静态网格体 → Movable ──
    changed = 0
    for a in actors:
        if not isinstance(a, unreal.StaticMeshActor):
            continue
        comp = a.static_mesh_component
        if not comp:
            continue
        try:
            comp.set_mobility(unreal.ComponentMobility.MOVABLE)
            changed += 1
        except Exception as e:
            log("  设 Mobility 失败: %s" % str(e)[:60])
    log("静态网格体改为 Movable: %d 个" % changed)

    # ── 2. 灯光也确认一遍 ──
    for a in actors:
        cn = a.get_class().get_name()
        if "DirectionalLight" in cn or "SkyLight" in cn:
            for prop in ("light_component", "directional_light_component",
                         "sky_light_component"):
                try:
                    lc = a.get_editor_property(prop)
                except Exception:
                    continue
                if not lc:
                    continue
                try:
                    lc.set_mobility(unreal.ComponentMobility.MOVABLE)
                    log("  %s → Movable" % cn)
                except Exception:
                    pass
                break

    # ── 3. 标记关卡为已修改并保存 ──
    try:
        les.save_current_level()
        log("关卡已保存")
    except Exception as e:
        log("保存失败: %s" % str(e)[:70])

    # ── 4. 构建光照 ──
    # 即便都改成 Movable 了，构建一次能让引擎的"未构建"标记清掉。
    try:
        unreal.EditorLevelLibrary.build_light_map()
        log("已触发 Build Lighting")
    except Exception as e:
        log("Build Lighting 失败: %s" % str(e)[:70])

    log("完成")


main()
