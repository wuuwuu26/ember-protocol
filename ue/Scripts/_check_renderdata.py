import unreal

MESHES = [
    "/Game/RobotGame/Art/Environment/SM_Env_Floor",
    "/Game/RobotGame/Art/Characters/SK_Chassis_Light",
    "/Engine/BasicShapes/Cube",
]

print("[渲染数据] === 检查网格体的渲染数据 ===")
for p in MESHES:
    m = unreal.EditorAssetLibrary.load_asset(p)
    if not m:
        print("[渲染数据] ❌ 加载失败: %s" % p)
        continue
    print("[渲染数据] --- %s ---" % p.split("/")[-1])
    # 三角形数（LOD0）
    for fn in ("get_num_triangles", "get_num_vertices"):
        try:
            f = getattr(m, fn)
            print("[渲染数据]   %s(0) = %s" % (fn, f(0)))
        except Exception as e:
            print("[渲染数据]   %s 失败: %s" % (fn, str(e)[:50]))
    # LOD 信息
    try:
        print("[渲染数据]   num_lods = %s" % m.get_num_lods())
    except Exception as e:
        print("[渲染数据]   num_lods 失败: %s" % str(e)[:40])
    # 材质槽
    try:
        print("[渲染数据]   材质槽数 = %s" % m.get_num_materials(0))
    except Exception as e:
        print("[渲染数据]   材质槽数失败: %s" % str(e)[:40])

# DDC 路径
print("[渲染数据] === DDC 位置 ===")
import os
for p in (os.path.expandvars(r"%LOCALAPPDATA%\UnrealEngine\Common\DerivedDataCache"),
          r"C:/Users/25227/Documents/robot_game/ue/DerivedDataCache"):
    print("[渲染数据]   %s  存在=%s" % (p, os.path.isdir(p)))
