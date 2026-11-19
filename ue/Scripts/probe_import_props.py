# -*- coding: utf-8 -*-
"""列 FbxStaticMeshImportData 的可用属性，避免猜名字。"""
import unreal

ui = unreal.FbxImportUI()
d = ui.static_mesh_import_data
names = []
for n in dir(d):
    if n.startswith("_"):
        continue
    try:
        v = getattr(d, n)
    except Exception:
        continue
    if callable(v):
        continue
    names.append("%-46s = %s" % (n, v))

out = ["FbxStaticMeshImportData 可用属性（%d 个）:" % len(names), ""] + names
with open(r"C:\Users\25227\Documents\robot_game\docs\idol_props.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("IDOL_PROPS_DONE")
