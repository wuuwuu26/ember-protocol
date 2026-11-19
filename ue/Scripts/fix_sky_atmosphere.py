# -*- coding: utf-8 -*-
"""删除遮挡天空穹顶的 SkyAtmosphere，并重捕获天光。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
unreal.EditorLevelLibrary.load_level(LEVEL)


def g(o, a, d=None):
    try:
        return o.get_editor_property(a)
    except Exception:
        return d

count = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() == "SkyAtmosphere":
        unreal.log("[天空修复] 删除 %s" % a.get_actor_label())
        unreal.EditorLevelLibrary.destroy_actor(a)
        count += 1
unreal.log("[天空修复] 删除大气 Actor %d 个" % count)

for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == "SkyDome":
        c = a.static_mesh_component
        unreal.log("[天空修复] SkyDome mesh=%s mat=%s visible=%s hidden=%s" % (
            c.static_mesh.get_name() if c.static_mesh else "None",
            [m.get_name() for m in c.get_materials()],
            c.is_visible(), a.is_hidden()))
        c.set_editor_property("cast_shadow", False)
        c.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    if a.get_class().get_name() == "SkyLight":
        c = g(a, "sky_light_component") or g(a, "light_component")
        if c:
            c.set_editor_property("real_time_capture", True)
            c.recapture_sky()
            unreal.log("[天空修复] 天光已重捕获")

unreal.EditorLevelLibrary.save_current_level()
unreal.log("[天空修复] 完成")