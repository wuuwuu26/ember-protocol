# -*- coding: utf-8 -*-
"""导入 IdolMech 到 /Game/RobotGame/Art/Props/IdolMech（第一百零三轮）

源文件：art_src/idol/IdolMech.fbx（由 IdolMech.glb 经 Blender 转换）

模型实测（Blender Z-up）：
  尺寸 0.2945 x 0.6178 x 1.0019 米 —— Z 轴向上，本来就是竖着的
  ⚠️ 轴心在几何中心（z ∈ [-0.50, +0.50]），不是脚底：
     放大 9 倍后向下延伸 4.5m，摆进关卡时 actor 的 Z 必须 ≈ +450cm
     才能让脚落在地面，否则半个身子会埋进地里。

导入设置：
  combine_meshes        合并成一个静态网格（源文件只有 1 个网格，保险起见）
  import_materials      True
  import_textures       True（GLB 的贴图已嵌入 FBX）
  generate_lightmap_uv  True（静态网格需要，否则光照贴图会报错）
  auto_generate_collision True（摆件也要挡人）
"""
import unreal

DEST = "/Game/RobotGame/Art/Props/IdolMech"
NAME = "SM_IdolMech"
FBX = r"C:\Users\25227\Documents\robot_game\art_src\idol\IdolMech.fbx"
REPORT = r"C:\Users\25227\Documents\robot_game\docs\idol_import.txt"

lines = []


def log(s):
    unreal.log("[IdolImport] %s" % s)
    lines.append(str(s))


# 目标目录不存在就建
if not unreal.EditorAssetLibrary.does_directory_exist(DEST):
    unreal.EditorAssetLibrary.make_directory(DEST)
    log("创建目录 %s" % DEST)

# 已存在就删（保证幂等）
target = "%s/%s" % (DEST, NAME)
if unreal.EditorAssetLibrary.does_asset_exist(target):
    unreal.EditorAssetLibrary.delete_asset(target)
    log("删除旧资产 %s" % target)

task = unreal.AssetImportTask()
task.filename = FBX
task.destination_path = DEST
task.destination_name = NAME
task.automated = True
task.save = True
task.replace_existing = True

ui = unreal.FbxImportUI()
ui.import_mesh = True
ui.import_materials = True
ui.import_textures = True
ui.import_animations = False
ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
ui.automated_import_should_detect_type = False
# 静态网格导入选项
# ⚠️ 属性名是实测出来的（docs/idol_props.txt），不要猜：
#    transform_vertex_positions_to_u_e_unit_scale 这个名字不存在
sm = ui.static_mesh_import_data
sm.combine_meshes = True
sm.generate_lightmap_u_vs = True
sm.auto_generate_collision = True
# Blender 导出的是米，UE 用厘米：convert_scene_unit 才是那个开关
sm.convert_scene_unit = True
sm.convert_scene = True
sm.force_front_x_axis = False
# 39.8 万三角面：开 Nanite，静态摆件用它最合适
sm.build_nanite = True
# 法线导入方式沿用源文件（不重算，重算会破坏硬表面的锐边）
sm.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
# ⚠️ 第一百零三轮（关键）：这个模型**没有贴图**，颜色全在顶点色里
#    （材质基叫 M_IdolMech_VC，VC = Vertex Color）。
#    导入选项的默认值是 IGNORE —— 忽略顶点色，于是整个模型渲染成纯白。
#    必须改成 REPLACE，把 FBX 里的顶点色写进网格。
sm.vertex_color_import_option = unreal.VertexColorImportOption.REPLACE

task.options = ui
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

imported = task.imported_object_paths
log("imported: %s" % [str(p) for p in imported])

mesh = unreal.EditorAssetLibrary.load_asset(target)
if not mesh:
    log("!! 导入后找不到资产 %s" % target)
else:
    log("资产名 %s  类 %s" % (mesh.get_name(), mesh.get_class().get_name()))
    try:
        bb = mesh.get_bounding_box()
        log("包围盒 size=(%.2f, %.2f, %.2f)  min=(%.2f,%.2f,%.2f)  max=(%.2f,%.2f,%.2f)"
            % (bb.max.x - bb.min.x, bb.max.y - bb.min.y, bb.max.z - bb.min.z,
               bb.min.x, bb.min.y, bb.min.z, bb.max.x, bb.max.y, bb.max.z))
    except Exception as e:
        log("包围盒读取失败: %s" % e)
    try:
        log("材质槽数 %d" % len(mesh.get_editor_property("static_materials")))
        for i, mi in enumerate(mesh.get_editor_property("static_materials")):
            m = mi.get_editor_property("material_interface")
            log("  slot%d -> %s" % (i, m.get_path_name() if m else "None"))
    except Exception as e:
        log("材质槽读取失败: %s" % e)

# 保存
unreal.EditorAssetLibrary.save_asset(target, only_if_is_dirty=False)
log("已保存 %s" % target)

with open(REPORT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
unreal.log("IDOL_IMPORT_DONE")
