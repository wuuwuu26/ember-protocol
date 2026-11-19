# -*- coding: utf-8 -*-
import unreal

def L(s): print("[环境材质] %s" % s)

def dump(path, label):
    m = unreal.EditorAssetLibrary.load_asset(path)
    if not m:
        L("  %-26s ❌ 加载失败" % label); return
    got = False
    for prop in ("static_materials", "materials"):
        try:
            arr = m.get_editor_property(prop)
        except Exception:
            continue
        try:
            n = len(arr)
        except Exception:
            continue
        names = []
        for i in range(n):
            try:
                mi = arr[i].get_editor_property("material_interface")
                names.append("%d:%s" % (i, mi.get_name() if mi else "空"))
            except Exception:
                names.append("%d:?" % i)
        L("  %-26s [%s] 槽%d  %s" % (label, prop, n, "  ".join(names)))
        got = True
        break
    if not got:
        L("  %-26s 无法读取材质属性" % label)

ENV = "/Game/RobotGame/Art/Environment"
for n in ("SM_Env_Floor", "SM_Env_Wall", "SM_Env_Pillar", "SM_Env_Catwalk",
          "SM_Env_Platform", "SM_Env_Gantry", "SM_Env_Doorframe",
          "SM_Env_Piperun"):
    dump("%s/%s" % (ENV, n), n)

PROPS = "/Game/RobotGame/Art/Props"
for n in ("SM_Prop_Container", "SM_Prop_Shelf", "SM_Prop_Beacon"):
    dump("%s/%s" % (PROPS, n), n)
