"""
余火协议 · 工程初始化脚本
================================================
在 UE 编辑器里跑，自动完成：
  1. 建立 Content 目录结构
  2. 批量导入 assets/out 下的全部 FBX
  3. 创建默认关卡 L_Persistent

用法（任选其一）:

  A. 编辑器菜单：工具 → 执行 Python 脚本 → 选择本文件
  B. 编辑器 Python 控制台：
       exec(open(r"C:/Users/25227/Documents/robot_game/ue/Scripts/setup_project.py").read())
  C. 命令行（需先关闭已打开的编辑器）：
       UnrealEditor-Cmd.exe <项目.uproject> -ExecutePythonScript="<本文件路径>"

前置条件：插件 PythonScriptPlugin 已启用（已在 RobotGame.uproject 中声明）。

导入设置说明:
  · import_uniform_scale = 1.0
    FBX 的尺寸已通过往返测试验证（机体 2.59 m），不要改这个值。
  · 带骨架的资产（chassis_* / enemy_*）导入为骨骼网格体，其余为静态网格体。
  · 不导入动画与贴图（目前资产里没有）。
"""

import os
import unreal

# ─────────────────────────────────────────────
# 配置
# ─────────────────────────────────────────────

PROJECT_DIR = r"C:\Users\25227\Documents\robot_game"
FBX_DIR = os.path.join(PROJECT_DIR, "assets", "out")

# 有骨架的资产前缀 → 导入为骨骼网格体
SKELETAL_PREFIXES = ("chassis_", "enemy_")

# 资产前缀 → 目标 Content 路径
DEST_MAP = {
    "chassis_":  "/Game/RobotGame/Art/Characters",
    "enemy_":    "/Game/RobotGame/Art/Characters",
    "module_":   "/Game/RobotGame/Art/Modules",
    "prop_":     "/Game/RobotGame/Art/Props",
    "env_":      "/Game/RobotGame/Art/Environment",
    "landmark_": "/Game/RobotGame/Art/Environment",
}

# 需要预先建立的目录
FOLDERS = [
    "/Game/RobotGame/Art/Characters",
    "/Game/RobotGame/Art/Modules",
    "/Game/RobotGame/Art/Environment",
    "/Game/RobotGame/Art/Props",
    "/Game/RobotGame/Art/VFX",
    "/Game/RobotGame/Art/Materials",
    "/Game/RobotGame/Audio",
    "/Game/RobotGame/Blueprints",
    "/Game/RobotGame/Data/Chassis",
    "/Game/RobotGame/Data/Modules",
    "/Game/RobotGame/Data/Enemies",
    "/Game/RobotGame/Data/Economy",
    "/Game/RobotGame/Maps/Persistent",
    "/Game/RobotGame/Maps/Regions",
    "/Game/RobotGame/UI",
    "/Game/RobotGame/Cinematics",
]

DEFAULT_LEVEL = "/Game/RobotGame/Maps/Persistent/L_Persistent"


# ─────────────────────────────────────────────
# 工具
# ─────────────────────────────────────────────

def log(msg):
    unreal.log("[余火协议] %s" % msg)
    print("[余火协议] %s" % msg)


def warn(msg):
    unreal.log_warning("[余火协议] %s" % msg)
    print("[余火协议][警告] %s" % msg)


def get_asset_subsystem():
    try:
        return unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
    except Exception:
        return None


def make_directories():
    log("建立目录结构...")
    sub = get_asset_subsystem()
    ok = 0
    for path in FOLDERS:
        try:
            if sub:
                sub.make_directory(path)
            else:
                unreal.EditorAssetLibrary.make_directory(path)
            ok += 1
        except Exception as e:
            warn("建立目录失败 %s: %s" % (path, e))
    log("目录就绪：%d/%d" % (ok, len(FOLDERS)))


def dest_for(filename):
    base = os.path.basename(filename).lower()
    for prefix, dest in DEST_MAP.items():
        if base.startswith(prefix):
            return dest
    return "/Game/RobotGame/Art/Props"


def is_skeletal(filename):
    base = os.path.basename(filename).lower()
    return any(base.startswith(p) for p in SKELETAL_PREFIXES)


def _try_set(obj, attr, value):
    """设置属性，失败则忽略。

    FBX 导入选项在不同 UE 版本间会增删（实测 5.8 就没有
    `automated_import_should_detect_errors`）。一个属性不存在
    不该让整批 51 个资产全部导入失败，所以逐个容错。
    """
    try:
        setattr(obj, attr, value)
        return True
    except Exception as e:
        warn("  跳过不支持的导入选项 %s: %s" % (attr, e))
        return False


def build_import_ui(skeletal):
    """构造 FBX 导入选项。

    单位缩放必须是 1.0 —— FBX 里已经是厘米（已通过往返测试验证，
    机体高度 2.59 米）。改这个值会让全部资产尺寸出错。
    """
    ui = unreal.FbxImportUI()
    _try_set(ui, "import_mesh", True)
    _try_set(ui, "import_materials", True)
    _try_set(ui, "import_textures", False)
    _try_set(ui, "import_animations", False)

    if skeletal:
        _try_set(ui, "mesh_type_to_import",
                 unreal.FBXImportType.FBXIT_SKELETAL_MESH)
        _try_set(ui, "import_as_skeletal", True)
        data = getattr(ui, "skeletal_mesh_import_data", None)
        if data:
            _try_set(data, "import_uniform_scale", 1.0)
            _try_set(data, "convert_scene", True)
            _try_set(data, "import_content_type",
                     unreal.FBXImportContentType.FBXICT_ALL)
    else:
        _try_set(ui, "mesh_type_to_import",
                 unreal.FBXImportType.FBXIT_STATIC_MESH)
        _try_set(ui, "import_as_skeletal", False)
        data = getattr(ui, "static_mesh_import_data", None)
        if data:
            _try_set(data, "import_uniform_scale", 1.0)
            _try_set(data, "convert_scene", True)
            _try_set(data, "generate_lightmap_u_vs", True)
            _try_set(data, "auto_generate_collision", True)

    return ui


def import_all():
    if not os.path.isdir(FBX_DIR):
        warn("找不到 FBX 目录：%s" % FBX_DIR)
        return 0, 0

    files = sorted(f for f in os.listdir(FBX_DIR) if f.lower().endswith(".fbx"))
    if not files:
        warn("FBX 目录为空：%s" % FBX_DIR)
        return 0, 0

    log("待导入 %d 个 FBX..." % len(files))
    tools = unreal.AssetToolsHelpers.get_asset_tools()

    tasks = []
    skipped = 0
    for f in files:
        full = os.path.join(FBX_DIR, f)
        skeletal = is_skeletal(f)
        try:
            options = build_import_ui(skeletal)
        except Exception as e:
            warn("  构造导入选项失败，跳过 %s: %s" % (f, e))
            skipped += 1
            continue
        task = unreal.AssetImportTask()
        task.filename = full
        task.destination_path = dest_for(f)
        task.destination_name = os.path.splitext(f)[0]
        task.automated = True
        task.save = True
        task.replace_existing = True
        task.options = options
        tasks.append(task)

    if skipped:
        warn("有 %d 个资产因导入选项构造失败被跳过" % skipped)

    ok, fail = 0, 0
    # 逐个导入而不是一次传整个数组 —— 单个失败不会中断整批，
    # 而且能精确定位是哪个资产出问题。
    for i, task in enumerate(tasks):
        name = os.path.basename(task.filename)
        try:
            tools.import_asset_tasks([task])
            paths = task.imported_object_paths
            if paths:
                ok += 1
                log("  [%2d/%d] %-34s -> %s" % (i + 1, len(tasks), name, paths[0]))
            else:
                fail += 1
                warn("  [%2d/%d] %-34s 无导入结果" % (i + 1, len(tasks), name))
        except Exception as e:
            fail += 1
            warn("  [%2d/%d] %-34s 失败: %s" % (i + 1, len(tasks), name, e))

    return ok, fail


def create_default_level():
    if unreal.EditorAssetLibrary.does_asset_exist(DEFAULT_LEVEL):
        log("默认关卡已存在，跳过：%s" % DEFAULT_LEVEL)
        return True
    try:
        sub = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        if sub:
            sub.new_level(DEFAULT_LEVEL)
            sub.save_current_level()
            log("已创建默认关卡：%s" % DEFAULT_LEVEL)
            return True
    except Exception as e:
        warn("创建关卡失败：%s" % e)
    return False


# ─────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────

def main():
    log("=" * 56)
    log("工程初始化开始")
    log("=" * 56)

    make_directories()
    ok, fail = import_all()
    create_default_level()

    log("=" * 56)
    log("完成：成功 %d  失败 %d" % (ok, fail))
    if fail:
        warn("有 %d 个资产导入失败，请检查上面的输出" % fail)
    log("下一步：打开 Content/RobotGame/Art/Characters/ 查看 chassis_medium，")
    log("       确认朝向是否为 +X 朝前（尺寸应为 2.59 米，Uniform Scale 保持 1.0）")


# 无条件执行。无论是 -ExecutePythonScript 还是编辑器控制台 exec()，
# 都用同一套逻辑，不做 __name__ 判断 —— 那个判断在不同执行路径下行为不一致。
main()
