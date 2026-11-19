import unreal

def L(s):
    print("[敌人] %s" % s)

L("========== 敌人骨骼网格的材质槽 ==========")
for n in ("Guard", "Patrol", "Hauler", "Gardener", "Colossus"):
    p = "/Game/RobotGame/Art/Characters/SK_Enemy_%s" % n
    m = unreal.EditorAssetLibrary.load_asset(p)
    if not m:
        L("  %s 加载失败" % n)
        continue
    L("  --- SK_Enemy_%s ---" % n)
    try:
        b = m.get_bounds()
        L("    包围盒: 中心%s 半径%.0f 尺寸%s" % (b.origin, b.sphere_radius, b.box_extent))
    except Exception as e:
        L("    包围盒失败: %s" % str(e)[:60])
    try:
        skel = m.get_editor_property("skeleton")
        L("    骨架: %s" % (skel.get_name() if skel else "无"))
    except Exception as e:
        L("    骨架读取失败: %s" % str(e)[:60])
    try:
        mats = m.get_editor_property("materials")
        L("    材质槽数: %d" % len(mats))
        for i, mi in enumerate(mats):
            try:
                name = mi.get_editor_property("material_interface").get_name()
            except Exception:
                name = "?"
            L("      [%d] %s" % (i, name))
    except Exception as e:
        L("    材质槽读取失败: %s" % str(e)[:80])

L("========== 玩家机体（对照）==========")
for n in ("Light", "Medium", "Heavy"):
    p = "/Game/RobotGame/Art/Characters/SK_Chassis_%s" % n
    m = unreal.EditorAssetLibrary.load_asset(p)
    if not m:
        continue
    try:
        mats = m.get_editor_property("materials")
        names = []
        for mi in mats:
            try:
                names.append(mi.get_editor_property("material_interface").get_name())
            except Exception:
                names.append("?")
        L("  SK_Chassis_%s: 槽%d %s" % (n, len(mats), names))
    except Exception as e:
        L("  SK_Chassis_%s 失败: %s" % (n, str(e)[:60]))

L("========== 角色数据资产（玩家怎么拿到网格）==========")
for p in ("/Game/RobotGame/Data/Chassis/DA_Chassis_Light",
          "/Game/RobotGame/Data/Chassis/DA_Chassis_Medium",
          "/Game/RobotGame/Data/Chassis/DA_Chassis_Heavy"):
    d = unreal.EditorAssetLibrary.load_asset(p)
    if not d:
        L("  %s 不存在" % p.split("/")[-1])
        continue
    try:
        mesh = d.get_editor_property("chassis_mesh")
        L("  %s: chassis_mesh=%s" % (p.split("/")[-1],
                                     mesh.get_name() if mesh else "无"))
    except Exception as e:
        L("  %s 读取失败: %s" % (p.split("/")[-1], str(e)[:80]))
