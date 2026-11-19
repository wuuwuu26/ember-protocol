"""
把自发光测试材质换回普通的受光材质
================================================================
自发光测试已经完成（结论：几何体渲染正常，问题在光照）。
现在换回受光材质，用于验证光照是否修好。

用法:
    UnrealEditor-Cmd.exe <项目> -unattended -nopause -nosplash \
      -ExecutePythonScript="<本文件>" -log
"""

import unreal

LIT_MAT = "/Engine/BasicShapes/BasicShapeMaterial"
LEVEL_PATH = "/Game/RobotGame/Maps/Persistent/L_TestArena"

MESH_ASSETS = [
    "/Game/RobotGame/Art/Environment/SM_Env_Floor",
    "/Game/RobotGame/Art/Props/SM_Prop_Container",
]


def log(m):
    unreal.log("[还原材质] %s" % m)
    print("[还原材质] %s" % m)


def main():
    mat = unreal.EditorAssetLibrary.load_asset(LIT_MAT)
    if not mat:
        log("❌ 找不到 %s" % LIT_MAT)
        return
    log("受光材质: %s" % mat.get_name())

    for p in MESH_ASSETS:
        m = unreal.EditorAssetLibrary.load_asset(p)
        if not m:
            continue
        try:
            m.set_material(0, mat)
            unreal.EditorAssetLibrary.save_loaded_asset(m)
            log("  %s 已还原" % p.split("/")[-1])
        except Exception as e:
            log("  %s 失败: %s" % (p.split("/")[-1], str(e)[:50]))

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(LEVEL_PATH)
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    n = 0
    for a in actors:
        if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component:
            try:
                a.static_mesh_component.set_material(0, mat)
                n += 1
            except Exception:
                pass
    log("关卡里 %d 个 Actor 已还原" % n)

    try:
        les.save_current_level()
        log("关卡已保存")
    except Exception as e:
        log("保存失败: %s" % str(e)[:60])

    log("完成")


main()
