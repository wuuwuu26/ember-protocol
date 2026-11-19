# -*- coding: utf-8 -*-
"""盘点 tools/blender 下所有脚本，列出可能受 Blender 5.3 API 变动影响的用法。

只读分析，不改文件。输出：
  - 每个脚本用到的 bpy 模块/API
  - 已知在 5.x 里变动/废弃的 API（use_nodes、BLENDER_EEVEE_NEXT、
    eevee 引擎名、gltf 导入参数、mathutils 等）
"""
import os
import re

ROOT = r"C:\Users\25227\Documents\robot_game\tools\blender"
OUT = r"C:\Users\25227\Documents\robot_game\docs\blender_scripts_audit.txt"

# 5.2 -> 5.3 需要重点关注的 API
WATCH = [
    "BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "BLENDER_WORKBENCH", "CYCLES",
    "use_nodes", "import_scene.gltf", "export_scene.gltf",
    "bpy.ops.object.bake", "smart_project", "get_ref_skeleton",
    "get_reference_skeleton", "calc_loop_triangles", "loop_triangles",
    "to_track_quat", "bound_box", "material_slot", "node_tree",
    "hide_render", "shade_smooth", "shade_flat", "Quaternion",
    "bpy.context.preferences.addons", "cycles.preferences",
    "scene.render.engine", "view_settings", "look",
]

lines = []
files = sorted(f for f in os.listdir(ROOT) if f.endswith(".py"))
lines.append("tools/blender 脚本共 %d 个" % len(files))
lines.append("")

all_hits = {}
for f in files:
    p = os.path.join(ROOT, f)
    try:
        s = open(p, encoding="utf-8", errors="replace").read()
    except Exception as e:
        lines.append("%-46s 读取失败 %s" % (f, e))
        continue
    hits = [w for w in WATCH if w in s]
    # 额外：统计 bpy.ops 调用
    ops = sorted(set(re.findall(r"bpy\.ops\.([a-z_]+\.[a-z_]+)", s)))
    all_hits[f] = (hits, ops, len(s.splitlines()))
    lines.append("%-46s %3d 行  watch=%s" % (f, len(s.splitlines()),
                                              ",".join(hits) if hits else "-"))
    if ops:
        lines.append("      bpy.ops: %s" % ", ".join(ops[:8]))

lines.append("")
lines.append("=== 需重点在 5.3 验证的 API 汇总 ===")
for w in WATCH:
    n = sum(1 for f in all_hits if w in all_hits[f][0])
    if n:
        lines.append("  %-32s 出现在 %d 个脚本" % (w, n))

with open(OUT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
print("\n".join(lines[:5]))
print("... audit written")
