# -*- coding: utf-8 -*-
"""导出几张关键贴图为 PNG，确认“d1”字符图案来自哪张图。"""
import os
import unreal

L = "[导出贴图]"
OUT = r"C:\Users\25227\Documents\robot_game\docs\tmp"
os.makedirs(OUT, exist_ok=True)


def export(path, name):
    t = unreal.load_asset(path)
    if not t:
        unreal.log("%s missing %s" % (L, path))
        return
    task = unreal.AssetExportTask()
    task.object = t
    task.filename = os.path.join(OUT, name)
    task.exporter = unreal.TextureExporter()
    task.automated = True
    task.replace_identical = True
    task.prompt = False
    try:
        ok = unreal.Exporter.run_asset_export_task(task)
        unreal.log("%s %s -> %s ok=%s" % (L, path, name, ok))
    except Exception as e:
        unreal.log("%s %s fail %s" % (L, name, str(e)[:120]))


export("/Game/RobotGame/Art/Materials/T_MechDetail", "T_MechDetail.png")
export("/Game/RobotGame/Art/Materials/T_MechDetail_N", "T_MechDetail_N.png")
export("/Game/RobotGame/Art/Materials/T_EnvDetail", "T_EnvDetail.png")
export("/Game/RobotGame/Art/Materials/T_BoltMetal", "T_BoltMetal.png")
unreal.log("EXPORTTEX_OK")
