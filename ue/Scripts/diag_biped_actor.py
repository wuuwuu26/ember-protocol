"""在园丁出生点放一个静止的 SK_Enemy_Gardener 副本（DiagBiped），用于拍摄双足步态。

用 ARobotEnemy 基类实例不行（它需要 AI），这里直接用 SkeletalMeshActor + 程序化步态驱动会更复杂；
先放静态副本确认模型，再考虑驱动。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
EAL = unreal.EditorAssetLibrary
ELL.load_level(LEVEL)

for a in list(ELL.get_all_level_actors()):
    if a.get_actor_label().startswith("DiagBiped"):
        ELL.destroy_actor(a)

mesh = EAL.load_asset("/Game/RobotGame/Art/Characters/SK_Enemy_Gardener")
act = ELL.spawn_actor_from_class(unreal.SkeletalMeshActor,
                                 unreal.Vector(1550.0, -100.0, 140.0),
                                 unreal.Rotator(0.0, 90.0, 0.0))
act.set_actor_label("DiagBiped_Gardener")
comp = act.get_component_by_class(unreal.SkeletalMeshComponent)
comp.set_skeletal_mesh(mesh)
unreal.log("[diag] 园丁静态副本已放置 (1550,-100,140)")
ELL.save_current_level()
print("DIAG_BIPED_OK")
