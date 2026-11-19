import unreal

print("[探测] === 查找渲染目标相关 API ===")
# 找所有含 Rendering 的模块
names = [n for n in dir(unreal) if 'ender' in n or 'apture' in n or 'exture' in n]
for n in sorted(names)[:40]:
    print("[探测] %s" % n)

print("[探测] === EditorLevelLibrary 里的截图/渲染函数 ===")
for n in dir(unreal.EditorLevelLibrary):
    if not n.startswith('_'):
        print("[探测] ELL.%s" % n)

print("[探测] === UnrealEditorSubsystem 方法 ===")
try:
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    for n in dir(ues):
        if not n.startswith('_'):
            print("[探测] UES.%s" % n)
except Exception as e:
    print("[探测] 失败: %s" % e)
