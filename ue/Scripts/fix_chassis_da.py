# -*- coding: utf-8 -*-
"""把三个机体的 DataAsset 指向重导入后的新网格。

背景：reimport_rigged.py 导入的 FBX 文件名是 chassis_light.fbx，
UE 按文件名生成了 chassis_light / chassis_light_Skeleton；而旧的
SK_Chassis_Light 网格还在，骨架却被删了 —— 运行时一用就断言
"SK_Chassis_Light missing skeleton"。

这里不改旧资产，只把 DA_Chassis_* 的 ChassisMesh 软路径指到新网格。
新网格的骨架是完整的。
"""
import unreal

EAL = unreal.EditorAssetLibrary
CHAR_DIR = "/Game/RobotGame/Art/Characters"
DA_DIR = "/Game/RobotGame/Data/Chassis"
PAIRS = [
    ("DA_Chassis_Light", "chassis_light"),
    ("DA_Chassis_Medium", "chassis_medium"),
    ("DA_Chassis_Heavy", "chassis_heavy"),
]


def log(m):
    unreal.log("[机体DA] %s" % m)
    print("[机体DA] %s" % m)


for da_name, mesh_name in PAIRS:
    da = EAL.load_asset(f"{DA_DIR}/{da_name}")
    mesh = EAL.load_asset(f"{CHAR_DIR}/{mesh_name}")
    if not da:
        log("!! 找不到 %s" % da_name)
        continue
    if not mesh:
        log("!! 找不到 %s" % mesh_name)
        continue

    skel = None
    try:
        skel = mesh.get_editor_property("skeleton")
    except Exception as e:
        log("读取 skeleton 失败: %s" % e)
    if not skel:
        log("!! %s 没有骨架，跳过" % mesh_name)
        continue

    before = da.get_editor_property("chassis_mesh")
    log("%s 原 ChassisMesh = %s；新网格骨架 = %s"
        % (da_name, before, skel.get_name()))

    path = f"{CHAR_DIR}/{mesh_name}.{mesh_name}"
    ok = False
    for value in (unreal.SoftObjectPath(path), path, mesh):
        try:
            da.set_editor_property("chassis_mesh", value)
        except Exception as e:
            continue
        now = da.get_editor_property("chassis_mesh")
        now_s = str(now)
        if mesh_name in now_s:
            ok = True
            log("  -> %s" % now_s)
            break

    if not ok:
        log("!! %s 设置 ChassisMesh 失败（最后值=%s）"
            % (da_name, da.get_editor_property("chassis_mesh")))
        continue

    EAL.save_loaded_asset(da)
    log("  %s 已保存" % da_name)

EAL.save_directory(CHAR_DIR, only_if_is_dirty=False, recursive=True)
unreal.log("CHASSIS_DA_OK")
