import bpy, os
p = os.path.abspath("../../assets/out/chassis_medium.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=p)
for ob in bpy.data.objects:
    if ob.type != 'MESH':
        continue
    me = ob.data
    n = len(me.uv_layers)
    print("[FBX] %-28s 顶点=%6d UV层=%d" % (ob.name, len(me.vertices), n))
    if n:
        uv = me.uv_layers[0].data
        us = [d.uv[0] for d in uv]; vs = [d.uv[1] for d in uv]
        print("       u: %.3f ~ %.3f   v: %.3f ~ %.3f" % (min(us), max(us), min(vs), max(vs)))
