"""在 BP_Enemy 附近临时加一盏补光点光源（标签 DiagFill），用于验证部件是否真的在网格里。"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
ELL = unreal.EditorLevelLibrary
ELL.load_level(LEVEL)

for a in list(ELL.get_all_level_actors()):
    if a.get_actor_label() == "DiagFill":
        ELL.destroy_actor(a)

light = ELL.spawn_actor_from_class(unreal.PointLight,
                                   unreal.Vector(250.0, -600.0, 320.0),
                                   unreal.Rotator(0.0, 0.0, 0.0))
light.set_actor_label("DiagFill")
lc = light.get_component_by_class(unreal.PointLightComponent)
lc.set_editor_property("intensity", 60000.0)
lc.set_editor_property("attenuation_radius", 2500.0)
lc.set_editor_property("light_color", unreal.Color(255, 255, 255, 255))
ELL.save_current_level()
print("DIAG_FILL_ON_OK")
