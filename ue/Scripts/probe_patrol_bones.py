"""列出 SK_Enemy_Patrol 的骨骼名，判断是否有 leg 骨（源设计巡逻机无腿）。"""
import unreal

EAL = unreal.EditorAssetLibrary
m = EAL.load_asset("/Game/RobotGame/Art/Characters/SK_Enemy_Patrol")
skel = m.get_editor_property("skeleton")
names = []
try:
    names = [str(n) for n in skel.get_editor_property("bone_tree")] if False else []
except Exception:
    pass
try:
    refs = m.get_editor_property("bone_names") if False else None
except Exception:
    pass
for b in ("root", "core", "torso", "leg_L", "leg_R", "arm_L", "arm_R"):
    try:
        idx = unreal.EditorSkeletonLibrary.get_bone_index(skel, b) if hasattr(unreal, "EditorSkeletonLibrary") else -1
        print("[pb] %-6s index=%s" % (b, idx))
    except Exception as e:
        print("[pb] %-6s err %s" % (b, e))
print("PATROL_BONES_OK")
