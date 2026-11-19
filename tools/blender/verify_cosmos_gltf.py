# -*- coding: utf-8 -*-
"""验证下载的 Cosmos glTF 能否被 Blender 正常导入（几何 + 贴图）。"""
import bpy
import os
import json

SLUG = "cs1-pipe"
DIR = r"C:\Users\25227\Documents\robot_game\art_src\cosmos\%s" % SLUG
GLTF = os.path.join(DIR, "model.gltf")
REPORT = r"C:\Users\25227\Documents\robot_game\docs\cosmos_verify.txt"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLTF)

lines = []
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
lines.append("mesh objects: %d" % len(meshes))
total_tris = 0
for o in meshes:
    me = o.data
    me.calc_loop_triangles()
    total_tris += len(me.loop_triangles)
    lines.append("obj %s  verts=%d  tris=%d  mats=%d" %
                 (o.name, len(me.vertices), len(me.loop_triangles), len(me.materials)))
    # 世界包围盒
    mn = [1e9]*3; mx = [-1e9]*3
    for c in o.bound_box:
        w = o.matrix_world @ __import__("mathutils").Vector(c)
        for i in range(3):
            mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
    lines.append("   bbox size=(%.3f, %.3f, %.3f) m" %
                 (mx[0]-mn[0], mx[1]-mn[1], mx[2]-mn[2]))
    for m in me.materials:
        if not m: continue
        imgs = []
        if m.use_nodes:
            for n in m.node_tree.nodes:
                if n.type == "TEX_IMAGE" and n.image:
                    imgs.append("%s(%s, %dx%d)" % (
                        n.image.name, n.image.file_format,
                        n.image.size[0], n.image.size[1]) if n.image.has_data else
                        "%s(未加载)" % n.image.name)
        lines.append("   mat %s  images=%s" % (m.name, imgs))
lines.append("total tris: %d" % total_tris)

with open(REPORT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
print("\n".join(lines))
print("COSMOS_VERIFY_DONE")
