"""在相机中心放一个静止的 SK_Enemy_Patrol 副本（标签 DiagPatrol），排除 AI 移动干扰，只验资产本身。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
EAL = unreal.EditorAssetLibrary
ELL.load_level(LEVEL)

for a in list(ELL.get_all_level_actors()):
    if a.get_actor_label() == "DiagPatrol":
        ELL.destroy_actor(a)

mesh = EAL.load_asset("/Game/RobotGame/Art/Characters/SK_Enemy_Patrol")
act = ELL.spawn_actor_from_class(unreal.SkeletalMeshActor,
                                 unreal.Vector(400.0, -400.0, 100.0),
                                 unreal.Rotator(0.0, 0.0, 0.0))
act.set_actor_label("DiagPatrol")
comp = act.get_component_by_class(unreal.SkeletalMeshComponent)
comp.set_skeletal_mesh(mesh)
ELL.save_current_level()
print("DIAG_STATIC_OK")
