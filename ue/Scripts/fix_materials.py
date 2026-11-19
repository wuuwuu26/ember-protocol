"""
排查黑屏：把所有网格的材质换成引擎自带材质
================================================
导入的 FBX 材质在缺少贴图时，UE 生成的材质可能是纯黑的 —— 这会让
整个场景看起来全黑，而灯光其实是正常的。这个脚本把材质统一换成
引擎自带的 BasicShapeMaterial（中性灰），用来排除材质因素。

如果换完之后画面能看见东西 → 问题在导入材质，需要重新制作材质。
如果还是全黑 → 问题在灯光或渲染设置。

用法:
    UnrealEditor-Cmd.exe <项目> -unattended -nopause -nosplash \
      -ExecutePythonScript="<本文件>" -log
"""

import unreal

PLACEHOLDER_MAT = "/Engine/BasicShapes/BasicShapeMaterial"
LEVEL_PATH = "/Game/RobotGame/Maps/Persistent/L_TestArena"

# 要处理的网格资产
MESH_ASSETS = [
    "/Game/RobotGame/Art/Characters/SK_Chassis_Light",
    "/Game/RobotGame/Art/Characters/SK_Chassis_Medium",
    "/Game/RobotGame/Art/Characters/SK_Chassis_Heavy",
    "/Game/RobotGame/Art/Characters/SK_Enemy_Patrol",
    "/Game/RobotGame/Art/Environment/SM_Env_Floor",
    "/Game/RobotGame/Art/Props/SM_Prop_Container",
]


def log(m):
    unreal.log("[材质] %s" % m)
    print("[材质] %s" % m)


def load(p):
    try:
        return unreal.EditorAssetLibrary.load_asset(p)
    except Exception:
        return None


def main():
    mat = load(PLACEHOLDER_MAT)
    if not mat:
        log("❌ 找不到引擎占位材质 %s" % PLACEHOLDER_MAT)
        return
    log("占位材质: %s" % mat.get_name())

    # ── 1. 直接改网格资产上的材质槽 ──
    # 这样所有引用该网格的地方都会跟着变，比逐个 Actor 改更彻底。
    fixed = 0
    for path in MESH_ASSETS:
        m = load(path)
        if not m:
            log("  跳过（不存在）: %s" % path.split("/")[-1])
            continue
        try:
            n = m.get_num_materials(0) if hasattr(m, "get_num_materials") else 0
        except Exception:
            n = 0
        if n == 0:
            # 没有材质槽就先建一个
            try:
                m.set_material(0, mat)
                n = 1
            except Exception as e:
                log("  %s 设材质失败: %s" % (path.split("/")[-1], str(e)[:60]))
                continue
        for i in range(n):
            try:
                m.set_material(i, mat)
            except Exception as e:
                log("  %s 槽%d 失败: %s" % (path.split("/")[-1], i, str(e)[:50]))
        unreal.EditorAssetLibrary.save_loaded_asset(m)
        fixed += 1
        log("  ✅ %s（%d 个槽）" % (path.split("/")[-1], n))

    log("共处理 %d 个网格资产" % fixed)

    # ── 2. 关卡里已放置的 Actor 也要改（它们保存了自己的材质覆盖）──
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(LEVEL_PATH)
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = unreal.EditorLevelLibrary.get_all_level_actors()

    touched = 0
    for a in actors:
        if isinstance(a, unreal.StaticMeshActor):
            comp = a.static_mesh_component
            if not comp:
                continue
            try:
                comp.set_material(0, mat)
                touched += 1
            except Exception:
                pass
    log("关卡里 %d 个静态网格 Actor 已换材质" % touched)

    # 重新保存关卡
    try:
        les.save_current_level()
        log("关卡已保存")
    except Exception as e:
        log("保存关卡失败: %s" % str(e)[:60])

    log("完成")


main()
