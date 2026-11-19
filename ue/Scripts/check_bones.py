import unreal

path = "/Game/RobotGame/Art/Characters/SK_Enemy_Weather"
m = unreal.EditorAssetLibrary.load_asset(path)
out = []
if not m:
    out.append("MISSING")
else:
    sk = m.get_editor_property("skeleton")
    skel = unreal.EditorAssetLibrary.load_asset(
        "/Game/RobotGame/Art/Characters/SK_Enemy_Weather_Skeleton")
    ref = skel.get_editor_property("reference_skeleton")
    n = ref.get_num()
    out.append("bones=%d" % n)
    names = []
    for i in range(n):
        try:
            names.append(str(ref.get_editor_property("bone_names")[i]))
        except Exception:
            names.append("?")
    out.append("names=" + ",".join(names))
    # 用 get_bone_tree / local transforms
    try:
        bt = ref.get_editor_property("bone_tree")
    except Exception as e:
        bt = None
    try:
        poses = ref.get_editor_property("ref_bone_pose")
        for i, nm in enumerate(names):
            if nm.startswith(("thigh", "shin", "foot")):
                p = poses[i]
                t = p.translation
                out.append("%-10s local=(%.2f, %.2f, %.2f)" % (nm, t.x, t.y, t.z))
    except Exception as e:
        out.append("pose_err %s" % e)

open(r"C:\Users\25227\AppData\Local\Temp\opencode\uebones.txt", "w",
     encoding="utf-8").write("\n".join(out))
unreal.log("UEBONES_OK")
