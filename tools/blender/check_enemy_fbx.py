"""统计敌人 FBX 导入 Blender 后的网格对象数与三角面数，定位丢件环节。"""
import bpy
import sys
import os

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
path = argv[0] if argv else ""

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=path)

total_tris = 0
meshes = []
for ob in bpy.context.scene.objects:
    if ob.type != 'MESH':
        continue
    me = ob.data
    me.calc_loop_triangles()
    tris = len(me.loop_triangles)
    total_tris += tris
    meshes.append((ob.name, tris, len(ob.material_slots), len(me.vertices)))

print("FBX_PATH", os.path.basename(path))
print("FBX_MESH_OBJECTS", len(meshes))
print("FBX_TOTAL_TRIS", total_tris)
for name, t, m, v in sorted(meshes, key=lambda x: -x[1])[:12]:
    print("FBX_OBJ %-28s tris=%6d mats=%d verts=%d" % (name, t, m, v))
print("FBX_CHECK_DONE")
