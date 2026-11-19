# -*- coding: utf-8 -*-
"""把 UE 里的 SK_Chassis_Light 导出成 FBX，检查肩甲顶点是否还在。"""
import unreal

SRC = "/Game/RobotGame/Art/Characters/SK_Chassis_Light"
OUT = r"C:\Users\25227\Documents\robot_game\docs\tmp\SK_Chassis_Light_ue.fbx"


def log(s):
    unreal.log("[导出机体] %s" % s)


sk = unreal.load_asset(SRC)
if not sk:
    log("找不到 " + SRC)
else:
    log("asset=%s class=%s" % (sk.get_name(), sk.get_class().get_name()))
    try:
        for n in dir(sk):
            low = n.lower()
            if any(k in low for k in ("vert", "section", "lod", "bound", "bone")):
                log("api " + n)
    except Exception as e:
        log("api fail " + str(e)[:100])

    ok = False
    try:
        ok = unreal.EditorAssetLibrary.export_asset(SRC, OUT)
        log("export_asset -> %s" % ok)
    except Exception as e:
        log("export_asset fail " + str(e)[:200])

    if not ok:
        try:
            task = unreal.AssetExportTask()
            task.set_editor_property("object", sk)
            task.set_editor_property("filename", OUT)
            task.set_editor_property("automated", True)
            task.set_editor_property("exporter", unreal.SkeletalMeshExporterFBX())
            ok = unreal.Exporter.run_asset_export_task(task)
            log("run_task -> %s" % ok)
        except Exception as e:
            log("run_task fail " + str(e)[:200])

unreal.log("CHASSISEXPORT_OK")
