import unreal
unreal.log("[关卡探针] LevelEditorSubsystem 方法: %s" % [m for m in dir(unreal.LevelEditorSubsystem) if "level" in m.lower()])
unreal.EditorLevelLibrary.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
w = unreal.EditorLevelLibrary.get_editor_world()
unreal.log("[关卡探针] world=%s current_level=%s" % (w.get_name(), w.get_current_level().get_name()))
unreal.log("[关卡探针] EditorLevelLibrary 存盘方法: %s" % [m for m in dir(unreal.EditorLevelLibrary) if "save" in m.lower()])
try:
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).get_levels()
    for l in levels:
        unreal.log("[关卡探针] level=%s" % l.get_name())
except Exception as e:
    unreal.log("[关卡探针] get_levels 失败: %s" % e)
unreal.log("[关卡探针] 完成")