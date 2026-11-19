import unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
# 复刻游戏里相机的实际位置与朝向：玩家(-600,0,121)，相机臂 480、俯 20°
unreal.EditorLevelLibrary.set_level_viewport_camera_info(
    unreal.Vector(-1051.0, 0.0, 470.0), unreal.Rotator(-20.0, 0.0, 0.0))
print("[视角] 已复刻游戏相机")
unreal.SystemLibrary.execute_console_command(None, "HighResShot 1")
