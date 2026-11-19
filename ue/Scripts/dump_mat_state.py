# -*- coding: utf-8 -*-
"""打印机体/环境/弹丸材质的贴图绑定，定位“d1”字符贴图从哪来。"""
import unreal

L = "[材质状态]"


def log(s):
    unreal.log("%s %s" % (L, s))


def dump_mat(path):
    m = unreal.load_asset(path)
    if not m:
        log("missing " + path)
        return
    log("MAT %s class=%s" % (path, m.get_class().get_name()))
    try:
        for e in m.get_editor_property("expressions"):
            cn = e.get_class().get_name()
            if "TextureSample" in cn:
                tex = None
                try:
                    tex = e.get_editor_property("texture")
                except Exception:
                    pass
                pn = ""
                try:
                    pn = e.get_editor_property("parameter_name")
                except Exception:
                    pass
                log("  %s param=%s tex=%s" % (
                    cn, pn, tex.get_path_name() if tex else "None"))
    except Exception as e:
        log("  expr fail " + str(e)[:90])
    try:
        for v in m.get_editor_property("texture_parameter_values"):
            info = v.get_editor_property("parameter_info")
            name = info.get_editor_property("name")
            tex = v.get_editor_property("parameter_value")
            log("  INST %s -> %s" % (
                name, tex.get_path_name() if tex else "None"))
    except Exception:
        pass


def dump_mesh(path):
    sm = unreal.load_asset(path)
    if not sm:
        log("mesh missing " + path)
        return
    log("MESH %s class=%s" % (path, sm.get_class().get_name()))
    try:
        for s in sm.get_editor_property("materials"):
            mi = None
            try:
                mi = s.get_editor_property("material_interface")
            except Exception:
                pass
            slot = ""
            try:
                slot = s.get_editor_property("material_slot_name")
            except Exception:
                pass
            log("  SLOT %s -> %s" % (
                slot, mi.get_path_name() if mi else "None"))
            if mi:
                dump_mat(mi.get_path_name())
    except Exception as e:
        log("  mesh fail " + str(e)[:90])


dump_mesh("/Game/RobotGame/Art/Characters/SK_Chassis_Light")
dump_mesh("/Game/RobotGame/Art/Environment/SM_Env_Floor")
dump_mat("/Game/RobotGame/Art/Materials/M_RobotSurface")
dump_mat("/Game/RobotGame/Art/Materials/M_Bolt_Shell")
unreal.log("MATSTATE_OK")
