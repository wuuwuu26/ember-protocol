# -*- coding: utf-8 -*-
"""清理 Hunyuan3D 白模里的"杂散大平面片"（第一百一十八轮）。

现象：severed_mech_arm 的展示图里出现两个巨大白色矩形平面（带黑斑），
是 3D 重建时留下的浮片，投影贴图后仍保留在 GLB 里。

做法：Blender 打开 GLB，遍历所有 MESH 对象，计算每个"连通块"的
包围盒/面积；把"相对整体尺寸过大、且很薄（一个轴几乎为 0）"的
孤立平面块删掉，其余保留，重新导出为干净的 GLB。

用法：
  blender -b --python clean_stray_planes.py -- <in.glb> <out.glb>
"""
import bpy
import sys
import os
import mathutils
from collections import defaultdict

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC = argv[0]
DST = argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)

meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
print("对象数 %d" % len(meshes))

# 全局包围盒（用于判断"过大"）
gmn = [1e9] * 3
gmx = [-1e9] * 3
for o in meshes:
    for c in o.bound_box:
        w = o.matrix_world @ mathutils.Vector(c)
        for i in range(3):
            gmn[i] = min(gmn[i], w[i])
            gmx[i] = max(gmx[i], w[i])
gsize = [gmx[i] - gmn[i] for i in range(3)]
gmax = max(gsize)
print("全局尺寸 (%.2f, %.2f, %.2f)" % tuple(gsize))

removed = 0
for o in list(meshes):
    me = o.data
    if len(me.polygons) == 0:
        continue
    # 该对象的尺寸
    omn = [1e9] * 3
    omx = [-1e9] * 3
    for c in o.bound_box:
        w = o.matrix_world @ mathutils.Vector(c)
        for i in range(3):
            omn[i] = min(omn[i], w[i])
            omx[i] = max(omx[i], w[i])
    osz = [omx[i] - omn[i] for i in range(3)]
    thick = min(osz)
    span = max(osz)

    # 判定"杂散大平面"：很薄（厚度 < 跨度的 3%）且跨度 >= 全局最大边的 60%
    is_plane = thick < span * 0.03
    is_huge = span >= gmax * 0.60
    # 且面数很少（真正的浮片通常就 2 个三角形 / 一个四边形）
    few_faces = len(me.polygons) <= 8
    if is_plane and is_huge and few_faces:
        print("  删除杂散平面 %s: 尺寸(%.2f,%.2f,%.2f) 面数%d" % (
            o.name, osz[0], osz[1], osz[2], len(me.polygons)))
        bpy.data.objects.remove(o, do_unlink=True)
        removed += 1

print("共删除 %d 个杂散平面" % removed)

# 重新导出（只导出剩下的 mesh）
bpy.ops.object.select_all(action="DESELECT")
for o in bpy.context.scene.objects:
    if o.type == "MESH":
        o.select_set(True)
bpy.ops.export_scene.gltf(filepath=DST, export_format="GLB",
                          use_selection=True, export_apply=True)
print("CLEANED=%s  %.1f MB" % (DST, os.path.getsize(DST) / 1048576.0))
print("CLEAN_STRAY_DONE")
