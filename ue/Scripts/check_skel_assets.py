# -*- coding: utf-8 -*-
"""检查骨骼网格的骨架与材质槽。

为什么要单独查：重导入后最容易出的问题是「网格换了、骨架还是旧的」——
UE 的 FBX 导入器遇到同名但层级不同的骨架会拒绝合并，只留一个警告。
表现是程序化动画按名字找不到 thigh_L/shin_L，静默退回单段腿。
这里直接把每个 SK 资产的骨骼名与材质槽打出来，一眼就能确认。

用法: UnrealEditor-Cmd.exe <项目> -ExecutePythonScript="<本文件>"
"""
import unreal

DEST = "/Game/RobotGame/Art/Characters"


def log(m):
    unreal.log("[资产检查] %s" % m)
    print("[资产检查] %s" % m)


def main():
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for ad in ar.get_assets_by_path(DEST, recursive=False):
        if str(ad.asset_class_path.asset_name) != "SkeletalMesh":
            continue
        nm = str(ad.asset_name)
        m = ad.get_asset()
        if not m:
            continue
        try:
            sk = m.get_editor_property("skeleton")
            bones = []
            if sk:
                fr = sk.get_editor_property("reference_skeleton")
                bones = [str(fr.get_bone_name(i))
                         for i in range(fr.get_num())]
        except Exception as e:
            bones = ["<读取失败 %s>" % str(e)[:40]]
        slots = []
        try:
            for s in m.get_editor_property("materials"):
                mi = s.get_editor_property("material_interface")
                slots.append(mi.get_name() if mi else "None")
        except Exception:
            pass
        log("%-26s 骨骼%d %s" % (nm, len(bones), ",".join(bones)))
        log("%-26s 槽%d %s" % ("", len(slots), " | ".join(slots)))


main()
