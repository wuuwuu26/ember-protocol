"""
排查黑屏：给骨骼网格体组件设置占位材质
================================================
SkeletalMesh 资产本身在 Python 里没有 set_material（未暴露），
但 USkeletalMeshComponent 有 —— 所以改蓝图 CDO 上的 Mesh 组件。

配合 fix_materials.py 使用：那个脚本处理静态网格体，这个处理骨骼网格体。
"""

import unreal

PLACEHOLDER_MAT = "/Engine/BasicShapes/BasicShapeMaterial"

BLUEPRINTS = [
    "/Game/RobotGame/Blueprints/BP_RobotCharacter",
    "/Game/RobotGame/Blueprints/BP_Enemy",
]


def log(m):
    unreal.log("[骨骼材质] %s" % m)
    print("[骨骼材质] %s" % m)


def main():
    mat = unreal.EditorAssetLibrary.load_asset(PLACEHOLDER_MAT)
    if not mat:
        log("❌ 找不到 %s" % PLACEHOLDER_MAT)
        return
    log("占位材质: %s" % mat.get_name())

    for bp_path in BLUEPRINTS:
        bp = unreal.EditorAssetLibrary.load_asset(bp_path)
        if not bp:
            log("  跳过（蓝图不存在）: %s" % bp_path.split("/")[-1])
            continue

        name = bp.get_name()
        cdo = unreal.get_default_object(bp.generated_class())

        # 找 Mesh 组件。角色类里它叫 Mesh（ACharacter 的默认名字）
        comp = None
        for prop in ("mesh", "Mesh"):
            try:
                comp = cdo.get_editor_property(prop)
                if comp:
                    break
            except Exception:
                continue

        if not comp:
            log("  ❌ %s 找不到 Mesh 组件" % name)
            continue

        # 设所有材质槽
        n = 0
        try:
            n = comp.get_num_materials()
        except Exception:
            n = 1
        if n <= 0:
            n = 1
        for i in range(n):
            try:
                comp.set_material(i, mat)
                log("  ✅ %s 槽%d 已设为占位材质" % (name, i))
            except Exception as e:
                log("  ❌ %s 槽%d 失败: %s" % (name, i, str(e)[:60]))

        try:
            unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        except Exception:
            pass
        unreal.EditorAssetLibrary.save_loaded_asset(bp)
        log("  %s 已保存" % name)

    log("完成")


main()
