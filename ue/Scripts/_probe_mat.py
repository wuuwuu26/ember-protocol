import unreal
def L(s): print("[材质] %s" % s)
ENV = "/Game/RobotGame/Art/Environment"
for n in ("SM_Landmark_Lighthouse", "SM_Env_Platform", "SM_Env_Gantry",
          "SM_Env_Doorframe", "SM_Env_Wall", "SM_Env_Catwalk", "SM_Env_Floor"):
    m = unreal.EditorAssetLibrary.load_asset("%s/%s" % (ENV, n))
    if not m:
        L("  %-26s ❌ 不存在" % n); continue
    try:
        mats = m.get_editor_property("materials")
        names = []
        for mi in mats:
            try:
                mi_ = mi.get_editor_property("material_interface")
                names.append(mi_.get_name() if mi_ else "空")
            except Exception:
                names.append("?")
        L("  %-26s 槽%d: %s" % (n, len(mats), names))
    except Exception as e:
        L("  %-26s 读取失败 %s" % (n, str(e)[:60]))
