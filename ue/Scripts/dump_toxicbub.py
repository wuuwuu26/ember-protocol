# -*- coding: utf-8 -*-
"""把 T_Toxic_Bub 导出成 PNG 看看内容（判断是否是有效纹理）。"""
import unreal
import os

EAL = unreal.EditorAssetLibrary
t = EAL.load_asset("/Game/RobotGame/Art/Materials/T_Toxic_Bub")
out = []
if not t:
    out.append("加载失败")
else:
    out.append("name=%s size=%dx%d srgb=%s" % (
        t.get_name(), t.blueprint_get_size_x(), t.blueprint_get_size_y(),
        t.get_editor_property("srgb")))
    # 导出到磁盘
    dst = r"C:\Users\25227\AppData\Local\Temp\opencode\T_Toxic_Bub.png"
    try:
        unreal.ImageWriteBlueprintLibrary  # noqa
    except Exception:
        pass
    # 用 asset export task
    task = unreal.AssetExportTask()
    task.set_editor_property("object", t)
    task.set_editor_property("filename", dst)
    task.set_editor_property("automated", True)
    task.set_editor_property("prompt", False)
    try:
        ok = unreal.Exporter.run_asset_export_task(task)
        out.append("export ok=%s exists=%s size=%s" % (
            ok, os.path.exists(dst),
            os.path.getsize(dst) if os.path.exists(dst) else -1))
    except Exception as e:
        out.append("export err %s" % e)

with open(r"C:\Users\25227\Documents\robot_game\docs\toxicbub.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("TOXICBUB_DONE")
