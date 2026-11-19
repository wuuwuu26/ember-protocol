# -*- coding: utf-8 -*-
"""把 UE 里的 fixed 贴图导出成 png，检查它到底是不是修复版。"""
import unreal

EAL = unreal.EditorAssetLibrary
lines = []
def log(s):
    unreal.log("[WreckTexDiag] %s" % s)
    lines.append(str(s))

paths = [
    "/Game/RobotGame/Art/Props/Gen3D/mech_torso_wreck",
    "/Game/RobotGame/Art/Props/Gen3D/severed_mech_arm",
]
for d in paths:
    for a in EAL.list_assets(d, recursive=True):
        obj = EAL.load_asset(a)
        if obj and "Texture2D" in obj.get_class().get_name():
            name = a.rsplit("/", 1)[-1]
            # 用 export 任务导出贴图
            out = r"C:\Users\25227\Documents\robot_game\docs\ue_tex_dump"
            import os
            os.makedirs(out, exist_ok=True)
            dst = os.path.join(out, name.split(".")[0] + ".png")
            try:
                t = unreal.AssetExportTask()
                t.object = obj
                t.filename = dst
                t.automated = True
                t.exporter = unreal.TextureExporterPNG()
                ok = unreal.Exporter.run_asset_export_task(t)
                log("%s -> %s ok=%s" % (name, dst, ok))
            except Exception as e:
                log("%s export err %s" % (name, str(e)[:80]))

with open(r"C:\Users\25227\Documents\robot_game\docs\wreck_tex_diag.txt", "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("WRECK_TEX_DIAG_DONE")
