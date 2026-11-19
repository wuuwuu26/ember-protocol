# -*- coding: utf-8 -*-
"""用 Blender Decimate 修改器减面（替代 trimesh simplify，避免退化三角形）。

trimesh 的 simplify_quadric_decimation 对 mech_torso_wreck 产生了
"点云"（退化三角形），Blender Decimate 更稳健。

用法：
  blender -b --python decimate_blender.py -- <in.glb> <out.glb> <目标面数>
"""
import bpy
import sys
import os

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SRC, DST = argv[0], argv[1]
TARGET = int(argv[2]) if len(argv) > 2 else 50000

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)

objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
# 合并多对象
if len(objs) > 1:
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
else:
    obj = objs[0]

before = len(obj.data.polygons)
ratio = min(1.0, TARGET / max(before, 1))
mod = obj.modifiers.new("Decimate", "DECIMATE")
mod.ratio = ratio
mod.use_collapse_triangulate = True
bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.modifier_apply(modifier=mod.name)
after = len(obj.data.polygons)
print("DECIMATE %d -> %d (ratio %.4f)" % (before, after, ratio), flush=True)

# 导出
bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=DST, export_format="GLB",
                          use_selection=True, export_apply=True)
print("SAVED %s %.1f MB" % (DST, os.path.getsize(DST)/1048576.0), flush=True)
print("DECIMATE_DONE", flush=True)
