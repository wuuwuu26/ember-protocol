"""
创建一个自发光材质并应用到所有网格体
================================================================
自发光（Emissive）材质不参与任何光照计算，直接输出颜色。
这是排查黑屏的终极测试：

  自发光材质能看见  → 几何体渲染管线正常，问题在光照/材质计算
  自发光材质也看不见 → 几何体根本没进渲染管线

用法:
    UnrealEditor-Cmd.exe <项目> -unattended -nopause -nosplash \
      -ExecutePythonScript="<本文件>" -log
"""

import unreal

MAT_PATH = "/Game/RobotGame/M_EmissiveTest"
LEVEL_PATH = "/Game/RobotGame/Maps/Persistent/L_TestArena"

MESH_ASSETS = [
    "/Game/RobotGame/Art/Environment/SM_Env_Floor",
    "/Game/RobotGame/Art/Props/SM_Prop_Container",
]


def log(m):
    unreal.log("[自发光] %s" % m)
    print("[自发光] %s" % m)


def make_material():
    """创建自发光材质。"""
    at = unreal.AssetToolsHelpers.get_asset_tools()

    # 已存在就先删掉
    if unreal.EditorAssetLibrary.does_asset_exist(MAT_PATH):
        try:
            unreal.EditorAssetLibrary.delete_asset(MAT_PATH)
        except Exception:
            pass

    mat = at.create_asset("M_EmissiveTest", "/Game/RobotGame",
                          unreal.Material, unreal.MaterialFactoryNew())
    if not mat:
        log("❌ 材质创建失败")
        return None
    log("材质已创建: %s" % mat.get_name())

    # 关键：自发光 + Unlit 着色模型，完全绕开光照
    try:
        mat.set_editor_property("shading_model",
                                unreal.MaterialShadingModel.MSM_UNLIT)
        log("  着色模型 = Unlit")
    except Exception as e:
        log("  设 Unlit 失败: %s" % str(e)[:60])

    # 创建一个亮的自发光颜色节点（用 Vector Parameter 也行，这里用常量）
    try:
        emis = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionConstant3Vector, -300, 0)
        # 亮青色，一眼能认出来
        emis.set_editor_property("constant", unreal.LinearColor(0.0, 1.0, 1.0, 1.0))
        unreal.MaterialEditingLibrary.connect_material_property(
            emis, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        log("  已连接自发光颜色（青色）")
    except Exception as e:
        log("  ❌ 连接自发光失败: %s" % str(e)[:80])
        return mat

    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
        log("  材质已编译")
    except Exception as e:
        log("  编译失败: %s" % str(e)[:60])

    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def main():
    mat = make_material()
    if not mat:
        return

    # 应用到网格资产
    for p in MESH_ASSETS:
        m = unreal.EditorAssetLibrary.load_asset(p)
        if not m:
            continue
        try:
            m.set_material(0, mat)
            unreal.EditorAssetLibrary.save_loaded_asset(m)
            log("  %s 已应用自发光材质" % p.split("/")[-1])
        except Exception as e:
            log("  %s 应用失败: %s" % (p.split("/")[-1], str(e)[:50]))

    # 应用到关卡里的 Actor
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
    log("关卡里 %d 个 Actor 已应用" % n)

    try:
        les.save_current_level()
        log("关卡已保存")
    except Exception as e:
        log("保存失败: %s" % str(e)[:60])

    log("完成")


main()
