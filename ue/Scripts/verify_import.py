"""
余火协议 · 导入结果验证
================================================
在 UE 内部读取导入后的资产，量出真实包围盒，验证尺寸与坐标轴映射。

用法（编辑器已关闭时）:
    UnrealEditor-Cmd.exe <项目> -unattended -nopause -nosplash \
      -ExecutePythonScript="<本文件>" -log

或者编辑器菜单：工具 → 执行 Python 脚本

为什么要在 UE 里量：Blender 侧的往返测试只能证明 FBX 文件自洽，
证明不了 UE 导入后的结果。只有从 UE 的资产里读出包围盒才是终局验证。

预期值（来自 Blender 实测）:
    chassis_light   宽 1.436  深 1.076  高 2.620  (米)
    chassis_medium  宽 1.670  深 1.142  高 2.590  (米)
    chassis_heavy   宽 1.978  深 1.441  高 2.480  (米)

坐标轴映射预期（Blender Z-up/-Y 前  →  UE Z-up/+X 前）:
    Blender X(宽) → UE Y
    Blender Y(深) → UE X
    Blender Z(高) → UE Z
"""

import unreal

CHAR_DIR = "/Game/RobotGame/Art/Characters"
MODULE_DIR = "/Game/RobotGame/Art/Modules"
ENV_DIR = "/Game/RobotGame/Art/Environment"

# (资产名, 期望 X 前后, 期望 Y 左右, 期望 Z 高) —— 单位米
#
# 修正朝向之后，坐标轴映射为：
#   Blender X(左右宽) → UE Y(左右)     Blender Y(前后深) → UE X(前后)
#   Blender Z(高)     → UE Z(高)
# 即 UE 的 X 是机体的前后深度，Y 是左右宽度 —— 符合 UE「+X 朝前」的约定。
CHASSIS = [
    ("SK_Chassis_Light", 1.076, 1.436, 2.620),
    ("SK_Chassis_Medium", 1.142, 1.670, 2.590),
    ("SK_Chassis_Heavy", 1.441, 1.978, 2.480),
]

# 朝向检查：这些资产的几何重心明显偏向机体正面，
# 若正面正确落在 UE +X，origin.x 应为较大的正值。
ORIENT_SAMPLES = [
    ("/Game/RobotGame/Art/Modules/SM_Module_ArmCannon", "炮管朝前", 0.19),
    ("/Game/RobotGame/Art/Modules/SM_Module_ArmMining", "钻头朝前", 0.15),
]


def log(msg):
    unreal.log("[验证] %s" % msg)
    print("[验证] %s" % msg)


def load(path):
    try:
        return unreal.EditorAssetLibrary.load_asset(path)
    except Exception as e:
        log("  加载失败 %s: %s" % (path, e))
        return None


def bounds_m(asset):
    """返回包围盒全尺寸（米）。box_extent 是半尺寸，要乘 2。"""
    b = asset.get_bounds()
    e = b.box_extent
    return (e.x * 2.0 / 100.0, e.y * 2.0 / 100.0, e.z * 2.0 / 100.0)


def check_chassis():
    log("=" * 62)
    log("玩家机体（骨骼网格体）")
    log("=" * 62)
    log("%-22s %8s %8s %8s   %s" % ("资产", "X 宽", "Y 深", "Z 高", "判定"))
    log("-" * 62)

    all_ok = True
    for name, ew, ed, eh in CHASSIS:
        a = load("%s/%s" % (CHAR_DIR, name))
        if not a:
            all_ok = False
            continue
        x, y, z = bounds_m(a)
        # 允许 3% 误差（倒角与浮点累积）
        ok = (abs(x - ew) < ew * 0.03
              and abs(y - ed) < ed * 0.03
              and abs(z - eh) < eh * 0.03)
        all_ok = all_ok and ok
        log("%-22s %8.3f %8.3f %8.3f   %s" % (name, x, y, z, "OK" if ok else "FAIL"))
        log("%-22s %8.3f %8.3f %8.3f   (期望)" % ("", ew, ed, eh))

        # 骨骼与 LOD
        try:
            skel = a.skeleton
            log("    骨架: %s   LOD: %d 级   材质槽: %d"
                % (skel.get_name() if skel else "无",
                   a.get_lod_num(),
                   len(a.get_editor_property("materials"))))
        except Exception as e:
            log("    读取骨架/LOD 信息失败: %s" % e)
    return all_ok


def spot_check():
    """抽查几个静态网格体，确认尺寸与预期一致。"""
    log("")
    log("=" * 62)
    log("静态网格体抽查")
    log("=" * 62)
    samples = [
        (MODULE_DIR, "SM_Module_HeadScout", 0.375, 0.375, 0.633),
        (MODULE_DIR, "SM_Module_ThrusterQuad", 0.540, 0.955, 1.009),
        (ENV_DIR, "SM_Landmark_Lighthouse", 16.540, 20.800, 21.000),
    ]
    for d, name, ew, ed, eh in samples:
        a = load("%s/%s" % (d, name))
        if not a:
            log("  %-28s 未找到" % name)
            continue
        x, y, z = bounds_m(a)
        log("  %-28s X %6.3f  Y %6.3f  Z %6.3f  m" % (name, x, y, z))
        log("  %-28s X %6.3f  Y %6.3f  Z %6.3f  (期望)" % ("", ew, ed, eh))


def count_assets():
    for d, label in ((CHAR_DIR, "Characters"),
                     (MODULE_DIR, "Modules"),
                     (ENV_DIR, "Environment")):
        try:
            paths = unreal.EditorAssetLibrary.list_assets(d, recursive=False)
            sk = sum(1 for p in paths if "SK_" in p)
            sm = sum(1 for p in paths if "SM_" in p)
            log("%-12s 骨骼网格体 %2d   静态网格体 %3d   合计 %3d"
                % (label, sk, sm, len(paths)))
        except Exception as e:
            log("%-12s 列举失败: %s" % (label, e))


def check_orientation():
    """检查机体正面是否落在 UE +X。

    原理：炮管 / 钻头这类部件明显朝机体正面伸出，会让包围盒中心偏向正面。
    若正面正确落在 +X，这些资产的 bounds.origin.x 应为较大的正值。
    """
    log("")
    log("=" * 62)
    log("朝向检查（正面应落在 +X）")
    log("=" * 62)
    all_ok = True
    for path, note, expect_x in ORIENT_SAMPLES:
        a = load(path)
        if not a:
            all_ok = False
            continue
        b = a.get_bounds()
        x, y, z = b.origin.x / 100.0, b.origin.y / 100.0, b.origin.z / 100.0
        ok = x > expect_x * 0.6 and abs(y) < abs(x) * 0.5
        all_ok = all_ok and ok
        log("  %-24s origin=(%6.3f, %6.3f, %6.3f)  %s  %s"
            % (path.split("/")[-1], x, y, z, "OK" if ok else "FAIL", note))
    log("  判读：origin.x 明显为正且大于 |origin.y| → 正面在 +X ✅")
    return all_ok


def main():
    log("=" * 62)
    log("导入结果验证")
    log("=" * 62)

    ok_size = check_chassis()
    ok_orient = check_orientation()
    spot_check()

    log("")
    log("=" * 62)
    log("资产统计")
    log("=" * 62)
    count_assets()

    log("")
    log("=" * 62)
    if ok_size and ok_orient:
        log("结论：尺寸与朝向全部正确 ✅")
        log("机体高度 2.59 米符合设计，正面落在 UE +X，符合 UE 约定。")
    elif not ok_size:
        log("结论：尺寸不符 ❌ —— 检查 FBX 导入的 Uniform Scale 是否为 1.0")
    else:
        log("结论：尺寸正确但朝向不符 ❌ —— 检查 export_fbx 的 Z 轴旋转")
    log("=" * 62)


main()
