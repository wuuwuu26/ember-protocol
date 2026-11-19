# -*- coding: utf-8 -*-
import unreal

def L(s): print("[机体材质] %s" % s)

for n in ("SK_Chassis_Light", "SK_Chassis_Medium", "SK_Chassis_Heavy",
          "SK_Enemy_Guard"):
    path = "/Game/RobotGame/Art/Characters/%s" % n
    m = unreal.EditorAssetLibrary.load_asset(path)
    if not m:
        L("  %-20s ❌ 加载失败" % n)
        continue
    try:
        mats = m.get_editor_property("materials")
        names = []
        for i, mi in enumerate(mats):
            try:
                iface = mi.get_editor_property("material_interface")
                names.append("%d:%s" % (i, iface.get_name() if iface else "空"))
            except Exception as e:
                names.append("%d:?%s" % (i, str(e)[:30]))
        L("  %-20s 槽%d  %s" % (n, len(mats), "  ".join(names)))
    except Exception as e:
        L("  %-20s 读取失败: %s" % (n, str(e)[:80]))
        # 兜底：看看有哪些属性
        try:
            L("      可用属性: %s" % [p for p in dir(m) if "mat" in p.lower()][:10])
        except Exception:
            pass
