"""检查 IdolMech.glb 的尺寸、朝向、材质与面数，并导出 FBX 供 UE 导入。

为什么要过 Blender：
  1. UE 的 glTF 导入需要额外插件，而 FBX 是这条流水线（robotlib.py）一直在用的格式；
  2. 先在 Blender 里量清楚真实尺寸，才能在 UE 里准确放大到 8~10 倍；
  3. Blender 导出时可以一次性把朝向（Z-up → UE 的 Z-up）和单位（米）定死。
"""
import bpy
import os
import sys

GLB = r"C:\Users\25227\Documents\robot_game\art_src\idol\IdolMech.glb"
FBX = r"C:\Users\25227\Documents\robot_game\art_src\idol\IdolMech.fbx"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\idol_probe.txt"

lines = []


def log(s):
    lines.append(str(s))
    print(s)


# 清空场景
bpy.ops.wm.read_factory_settings(use_empty=True)

bpy.ops.import_scene.gltf(filepath=GLB)

objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
log("mesh objects: %d" % len(objs))

total_tris = 0
all_min = [1e9, 1e9, 1e9]
all_max = [-1e9, -1e9, -1e9]

for o in objs:
    me = o.data
    log("")
    log("object: %s" % o.name)
    log("  verts=%d  polys=%d  materials=%d"
        % (len(me.vertices), len(me.polygons), len(me.materials)))
    # 三角化后的面数（UE 里按三角面算）
    me.calc_loop_triangles()
    tris = len(me.loop_triangles)
    total_tris += tris
    log("  tris=%d" % tris)
    log("  scale=(%.4f,%.4f,%.4f)  rot=(%.2f,%.2f,%.2f)"
        % (o.scale.x, o.scale.y, o.scale.z,
           o.rotation_euler.x, o.rotation_euler.y, o.rotation_euler.z))
    for i, m in enumerate(me.materials):
        if m:
            log("  mat[%d] = %s" % (i, m.name))

    # 世界坐标包围盒
    for corner in o.bound_box:
        wc = o.matrix_world @ __import__("mathutils").Vector(corner)
        for i in range(3):
            all_min[i] = min(all_min[i], wc[i])
            all_max[i] = max(all_max[i], wc[i])

size = [all_max[i] - all_min[i] for i in range(3)]
log("")
log("== bounding box (Blender Z-up, 单位=米) ==")
log("  min = (%.4f, %.4f, %.4f)" % tuple(all_min))
log("  max = (%.4f, %.4f, %.4f)" % tuple(all_max))
log("  size = (%.4f, %.4f, %.4f)" % tuple(size))
log("  最大边长 = %.4f" % max(size))
log("  total tris = %d" % total_tris)

# 判断哪一轴是"高度"：一般竖直方向的边长最小或最大都可能，
# 但机甲摆件通常是"高 > 宽"，所以取三个轴里最长的那个作为高度参考。
axes = ["X", "Y", "Z"]
tallest = axes[size.index(max(size))]
log("  最长的轴 = %s（若为 Z 说明 Blender 里已经竖着）" % tallest)

# 导出 FBX
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.fbx(
    filepath=FBX,
    use_selection=True,
    object_types={"MESH"},
    apply_scale_options="FBX_SCALE_NONE",
    axis_forward="-Y",
    axis_up="Z",
    bake_space_transform=False,
    use_mesh_modifiers=True,
    mesh_smooth_type="EDGE",
    path_mode="COPY",
    embed_textures=True,
)
log("")
log("FBX exported: %s (%d bytes)"
    % (FBX, os.path.getsize(FBX) if os.path.exists(FBX) else -1))

with open(REPORT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
print("IDOL_PROBE_DONE")
