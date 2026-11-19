# -*- coding: utf-8 -*-
"""检查 UE 机体网格：LOD 屏幕尺寸、材质槽、肩部骨骼、数据资产指向。"""
import unreal

L = "[机体检查]"


def log(s):
    unreal.log("%s %s" % (L, s))


def dump_mesh(path):
    m = unreal.load_asset(path)
    if not m:
        log("missing " + path)
        return
    log("ASSET %s class=%s" % (path, m.get_class().get_name()))
    try:
        for i, li in enumerate(m.get_editor_property("lod_info")):
            log("  LOD%d screen=%.4f" % (
                i, li.get_editor_property("screen_size")))
    except Exception as e:
        log("  lod fail " + str(e)[:100])
    try:
        for s in m.get_editor_property("materials"):
            log("  MAT %s" % s.get_editor_property("material_slot_name"))
    except Exception as e:
        log("  mats fail " + str(e)[:100])
    try:
        sk = m.get_editor_property("skeleton")
        log("  SKEL %s" % sk.get_path_name())
        bt = sk.get_editor_property("bone_tree")
        log("  BONETREE %d" % len(bt))
        for b in bt:
            n = str(b.get_editor_property("name"))
            if any(k in n.lower() for k in
                   ("shoulder", "clavicle", "upperarm", "arm")):
                log("    BONE " + n)
    except Exception as e:
        log("  skel fail " + str(e)[:120])
    try:
        ref = m.get_ref_skeleton()
        log("  REFBONES %d" % ref.get_num())
        for i in range(ref.get_num()):
            n = str(ref.get_bone_name(i))
            if any(k in n.lower() for k in
                   ("shoulder", "clavicle", "upperarm", "arm")):
                log("    REF " + n)
    except Exception as e:
        log("  ref fail " + str(e)[:100])


dump_mesh("/Game/RobotGame/Art/Characters/chassis_light")
dump_mesh("/Game/RobotGame/Art/Characters/chassis_light_LOD1")

for p in ("/Game/RobotGame/Data/Chassis/DA_Chassis_Light",
          "/Game/RobotGame/Data/Chassis/DA_Chassis_Medium"):
    da = unreal.load_asset(p)
    if not da:
        log("DA missing " + p)
        continue
    log("DA %s" % p)
    for prop in ("chassis_mesh", "ChassisMesh"):
        try:
            log("  %s = %s" % (prop, da.get_editor_property(prop)))
        except Exception:
            pass
unreal.log("CHASSISCHECK_OK")
