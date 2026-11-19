# -*- coding: utf-8 -*-
"""探查扩建要用的第二批资产：门框、龙门架、高台、楼梯、货箱类道具。"""
import unreal

OUT = r"C:\Users\25227\Documents\robot_game\docs\ext_assets2.txt"
FOLDERS = ["/Game/RobotGame/Art/Environment", "/Game/RobotGame/Art/Props"]

lines = []


def log(s):
    lines.append(str(s))


for folder in FOLDERS:
    try:
        all_assets = unreal.EditorAssetLibrary.list_assets(folder, recursive=False)
    except Exception as e:
        log("list fail %s" % e)
        continue
    log("== %s ==" % folder)
    for p in sorted(all_assets):
        name = p.split("/")[-1]
        low = name.lower()
        if "lod1" in low or "lod2" in low or low.startswith("m_"):
            continue
        a = unreal.EditorAssetLibrary.load_asset(p)
        if not a:
            continue
        try:
            bb = a.get_bounding_box()
            mn, mx = bb.min, bb.max
            log("%-26s size=(%.0f, %.0f, %.0f) minZ=%.0f  class=%s"
                % (name, mx.x - mn.x, mx.y - mn.y, mx.z - mn.z, mn.z,
                   a.get_class().get_name()))
        except Exception as e:
            log("%-26s (no bbox) %s" % (name, a.get_class().get_name()))
    log("")

with open(OUT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("EXT_ASSETS2_DONE")
