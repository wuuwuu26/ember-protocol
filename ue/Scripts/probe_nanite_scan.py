# -*- coding: utf-8 -*-
"""全关卡 + 全项目扫一遍：到底哪些 StaticMesh 开了 Nanite（找 SM6 警告来源）。"""
import unreal

EAL = unreal.EditorAssetLibrary
out = []

all_paths = EAL.list_assets("/Game/RobotGame", recursive=True, include_folder=False)
out.append("项目 /Game/RobotGame 资产总数 %d" % len(all_paths))

on = []
sm_count = 0
for p in all_paths:
    a = EAL.load_asset(p)
    if not a or a.get_class().get_name() != "StaticMesh":
        continue
    sm_count += 1
    try:
        ns = a.get_editor_property("nanite_settings")
        if ns.get_editor_property("enabled"):
            on.append(p)
    except Exception:
        pass

out.append("StaticMesh 共 %d 个，其中开 Nanite 的 %d 个：" % (sm_count, len(on)))
for p in on:
    out.append("  " + p)

# 项目 RHI / SM6 设置
out.append("")
out.append("== 渲染设置（只读）==")
try:
    r = unreal.get_default_object(unreal.RendererSettings)
    for prop in ("default_feature_level", "mobile_hdr"):
        try:
            out.append("  %s = %s" % (prop, r.get_editor_property(prop)))
        except Exception:
            pass
except Exception:
    pass

with open(r"C:\Users\25227\Documents\robot_game\docs\nanite_scan.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("NANITE_SCAN_DONE")
