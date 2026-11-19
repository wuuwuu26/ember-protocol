"""
在编辑器里重新编译材质与着色器，并报告状态
================================================================
在编辑器 Output Log 的 Cmd 输入框执行：
    py exec(open(r'C:/Users/25227/Documents/robot_game/ue/Scripts/editor_recompile.py').read())

这是唯一还没验证过的环节：材质/着色器在 GPU 上是否真的编译成功。
"""

import unreal


def log(m):
    unreal.log("[重编译] %s" % m)
    print("[重编译] %s" % m)


def main():
    log("=" * 50)

    # ── 1. 重新编译所有用到的材质 ──
    mats = [
        "/Engine/BasicShapes/BasicShapeMaterial",
        "/Game/RobotGame/M_EmissiveTest",
    ]
    for p in mats:
        m = unreal.EditorAssetLibrary.load_asset(p)
        if not m:
            log("%s: 不存在，跳过" % p.split("/")[-1])
            continue
        try:
            unreal.MaterialEditingLibrary.recompile_material(m)
            log("%s: ✅ 已重新编译" % p.split("/")[-1])
        except Exception as e:
            log("%s: 编译失败 %s" % (p.split("/")[-1], str(e)[:60]))

    # ── 2. 把受光材质重新应用到网格（触发着色器重编译）──
    lit = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/BasicShapeMaterial")
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    n = 0
    for a in actors:
        if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component:
            try:
                a.static_mesh_component.set_material(0, lit)
                n += 1
            except Exception:
                pass
    log("重新应用材质到 %d 个 Actor" % n)

    # ── 3. 报告当前 CVar ──
    names = ["r.Nanite", "r.ForwardShading", "r.Shadow.Virtual.Enable",
             "r.AllowStaticLighting", "r.AntiAliasingMethod",
             "r.ScreenPercentage", "r.DefaultFeature.AutoExposure",
             "r.MaterialQualityLevel"]
    for nm in names:
        try:
            v = unreal.SystemLibrary.get_console_variable_value(nm)
            log("CVar %-32s = %s" % (nm, v))
        except Exception:
            log("CVar %-32s = 读取失败" % nm)

    # ── 4. 报告引擎的着色器编译状态 ──
    try:
        # 有些版本有这个方法
        ok = unreal.SystemLibrary.get_console_variable_value("r.ShaderDevelopmentMode")
        log("着色器开发模式 = %s" % ok)
    except Exception:
        pass

    # ── 5. 标记关卡脏并保存（让改动生效）──
    try:
        les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        les.save_current_level()
        log("关卡已保存")
    except Exception as e:
        log("保存失败: %s" % str(e)[:60])

    log("=" * 50)
    log("完成。请看一眼编辑器视口，然后按 Play（PIE）试试")


main()
