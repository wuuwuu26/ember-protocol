# -*- coding: utf-8 -*-
import unreal
L = "[蓝图网格]"
cls = unreal.load_class(None, "/Game/RobotGame/Blueprints/BP_RobotCharacter.BP_RobotCharacter_C")
if not cls:
    unreal.log("%s ❌ 找不到蓝图类" % L)
else:
    cdo = unreal.get_default_object(cls)
    for pn in ("Mesh", "mesh"):
        try:
            comp = cdo.get_editor_property(pn)
        except Exception:
            comp = None
        if comp:
            unreal.log("%s 组件属性名=%s" % (L, pn))
            break
    else:
        comp = None
    if comp:
        for p in ("skeletal_mesh_asset", "skeletal_mesh"):
            try:
                m = comp.get_editor_property(p)
                if m:
                    unreal.log("%s 网格 = %s" % (L, m.get_path_name()))
                    break
            except Exception as e:
                unreal.log("%s   %s: %s" % (L, p, str(e)[:50]))
        try:
            ov = comp.get_editor_property("override_materials")
            unreal.log("%s OverrideMaterials = %d 个: %s"
                       % (L, len(ov), [str(x) for x in ov][:10]))
        except Exception as e:
            unreal.log("%s override 读取失败 %s" % (L, str(e)[:50]))
        try:
            n = comp.get_num_materials()
            for i in range(n):
                mm = comp.get_material(i)
                unreal.log("%s   槽%d → %s" % (L, i, mm.get_path_name() if mm else "空"))
        except Exception as e:
            unreal.log("%s 材质读取失败 %s" % (L, str(e)[:50]))
