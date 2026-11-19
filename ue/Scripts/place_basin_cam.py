# -*- coding: utf-8 -*-
"""在水渠上方架一台相机拍特写（第一百一十二轮诊断用）。

临时生成一个 CameraActor 并设为 ViewTarget，然后由外部截图工具抓图。
"""
import unreal

LEVEL = "/Game/RobotGame/Maps/Persistent/L_TestArena"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level(LEVEL)
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# 水渠位置：(450, 300) 是 CoolantSpill，(-200,350) (800,-150) (-650,-450) (400,750) 是毒液池
# 相机放在池子上方斜看
TAG = "BasinCamProbe"

# 清理旧的
for a in list(sub.get_all_level_actors()):
    try:
        tags = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        continue
    if TAG in tags:
        sub.destroy_actor(a)

cam_loc = unreal.Vector(450, 700, 700)
target = unreal.Vector(450, 300, 0)
rot = (target - cam_loc).Rotation()

cam_actor = sub.spawn_actor_from_class(
    unreal.CameraActor, cam_loc, rot)
if cam_actor:
    cam_actor.set_actor_label("BasinProbeCam")
    cam_actor.set_editor_property("tags", [TAG])
    c = cam_actor.get_camera_component()
    if c:
        c.set_editor_property("field_of_view", 70.0)
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(cam_loc, rot)
    unreal.log("[BasinCam] 相机已放置 (%.0f,%.0f,%.0f)" % (
        cam_loc.x, cam_loc.y, cam_loc.z))

unreal.log("BASIN_CAM_DONE")
