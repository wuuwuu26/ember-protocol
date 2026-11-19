# -*- coding: utf-8 -*-
import unreal
L = "[穹顶]"
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() != "StaticMeshActor":
        continue
    lbl = a.get_actor_label()
    if "Sky" not in lbl and "Dome" not in lbl:
        continue
    smc = a.static_mesh_component
    sc = a.get_actor_scale3d()
    loc = a.get_actor_location()
    def g(n, d=None):
        try:
            return smc.get_editor_property(n)
        except Exception:
            return d
    unreal.log("%s %-10s 位置=(%.0f,%.0f,%.0f) 缩放=(%.0f,%.0f,%.0f)"
               % (L, lbl, loc.x, loc.y, loc.z, sc.x, sc.y, sc.z))
    unreal.log("%s   投射阴影=%s 阴影模式=%s 双面=%s 影响光照=%s"
               % (L, g("cast_shadow"), g("shadow_cache_invalidation"),
                  g("double_sided"), g("affect_dynamic_indirect_lighting")))
    unreal.log("%s   材质=%s" % (L, g("override_materials")))
