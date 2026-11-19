# -*- coding: utf-8 -*-
"""测试：复制引擎 FountainLightweight 系统到项目，看是否可行。"""
import unreal

EAL = unreal.EditorAssetLibrary
out = []

SRC = "/Niagara/DefaultAssets/Templates/Systems/FountainLightweight.FountainLightweight"
DEST_DIR = "/Game/RobotGame/FX"
DEST = DEST_DIR + "/NS_WaterSplash"

# 检查源
src = EAL.load_asset(SRC)
out.append("源 = %s  类=%s" % (SRC, src.get_class().get_name() if src else "None"))

if src:
    # 系统属性
    for p in ("get_exposed_parameters",):
        pass
    try:
        # 列出系统里的 emitter
        handles = src.get_editor_property("emitter_handles")
        out.append("emitter_handles = %d" % len(handles))
        for h in handles:
            try:
                out.append("  emitter: %s" % h.get_editor_property("id"))
            except Exception:
                pass
    except Exception as e:
        out.append("emitter_handles 读取: %s" % str(e)[:60])

    # 复制资产
    if not EAL.does_directory_exist(DEST_DIR):
        EAL.make_directory(DEST_DIR)
        out.append("建目录 %s" % DEST_DIR)
    if EAL.does_asset_exist(DEST):
        EAL.delete_asset(DEST)
    ok = EAL.duplicate_asset(SRC, DEST)
    out.append("duplicate_asset -> %s" % ok)
    dup = EAL.load_asset(DEST)
    out.append("副本 = %s  类=%s" % (
        DEST, dup.get_class().get_name() if dup else "None"))

with open(r"C:\Users\25227\Documents\robot_game\docs\niagara_dup.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("NIAGARA_DUP_DONE")
