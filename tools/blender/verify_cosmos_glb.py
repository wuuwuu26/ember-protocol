# -*- coding: utf-8 -*-
"""验证打包出的 GLB：结构合法 + Blender 能导入 + 贴图能读到像素。"""
import bpy
import os
import sys
import struct
import json

GLB_DIR = r"C:\Users\25227\Documents\robot_game\art_src\cosmos\glb"
# Blender 会把自身命令行参数（--background、--python <script> 等）也塞进 sys.argv。
# 用 "--" 之后的参数作为 slug；没给就退回默认两个。
if "--" in sys.argv:
    slugs = sys.argv[sys.argv.index("--") + 1:]
else:
    slugs = []
slugs = slugs or ["cs1-pipe", "rps-fire-extinguisher-02"]
lines = []

for slug in slugs:
    path = os.path.join(GLB_DIR, slug + ".glb")
    lines.append("=== %s ===" % slug)
    # 手写校验 GLB 头
    with open(path, "rb") as f:
        head = f.read(20)
    magic, ver, total = struct.unpack("<III", head[:12])
    jlen, jtype = struct.unpack("<II", head[12:20])
    lines.append("  header magic=%s ver=%s total=%d jsonLen=%d" %
                 (hex(magic), ver, total, jlen))
    lines.append("  file size=%d  (total==file: %s)" %
                 (os.path.getsize(path), os.path.getsize(path) == total))

    # Blender 导入
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        bpy.ops.import_scene.gltf(filepath=path)
    except Exception as e:
        lines.append("  !! Blender import FAILED: %s" % e)
        continue
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    lines.append("  meshes=%d" % len(meshes))
    for o in meshes:
        me = o.data
        me.calc_loop_triangles()
        mn = [1e9]*3; mx = [-1e9]*3
        for c in o.bound_box:
            w = o.matrix_world @ __import__("mathutils").Vector(c)
            for i in range(3):
                mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
        lines.append("    %s tris=%d bbox=(%.2f,%.2f,%.2f)m" %
                     (o.name, len(me.loop_triangles),
                      mx[0]-mn[0], mx[1]-mn[1], mx[2]-mn[2]))
        for m in me.materials:
            if not m:
                continue
            ims = []
            for n in m.node_tree.nodes if m.use_nodes else []:
                if n.type == "TEX_IMAGE" and n.image:
                    loaded = n.image.has_data and (n.image.size[0] > 0)
                    ims.append("%s=%dx%d:%s" %
                               (n.image.name, n.image.size[0], n.image.size[1],
                                "LOADED" if loaded else "EMPTY"))
            lines.append("    mat %s -> %s" % (m.name, "; ".join(ims)))

with open(r"C:\Users\25227\Documents\robot_game\docs\cosmos_glb_verify.txt", "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
print("\n".join(lines))
print("COSMOS_GLB_VERIFY_DONE")
