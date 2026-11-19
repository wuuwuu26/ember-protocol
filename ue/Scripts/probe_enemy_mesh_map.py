"""查 BP_Enemy 实际使用的骨骼网格：遍历关卡中所有 BP_Enemy 类 actor，打印其 SkeletalMeshComponent 的网格路径。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
ELL.load_level(LEVEL)

for a in ELL.get_all_level_actors():
    cls = a.get_class().get_name()
    if "BP_Enemy" not in cls:
        continue
    lbl = a.get_actor_label()
    comps = a.get_components_by_class(unreal.SkeletalMeshComponent)
    for c in comps:
        m = c.get_editor_property("skeletal_mesh")
        print("[map] %-12s comp=%-24s mesh=%s" % (lbl, c.get_name(), m.get_path_name() if m else "None"))
print("ENEMY_MESH_MAP_OK")
