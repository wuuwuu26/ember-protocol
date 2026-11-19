# -*- coding: utf-8 -*-
"""深查地面贴图资产是否真的有像素数据（第一百一十一轮）。"""
import unreal

PH = "/Game/RobotGame/Art/Materials/PolyHaven"
EAL = unreal.EditorAssetLibrary
out = []

NAMES = ["concrete_floor_02_BaseColor", "concrete_floor_02_Normal",
         "concrete_floor_02_ARM"]

for n in NAMES:
    p = "%s/concrete_floor_02/%s" % (PH, n)
    t = EAL.load_asset(p)
    out.append("=== %s ===" % n)
    if not t:
        out.append("  !! 加载失败")
        continue
    out.append("  class=%s" % t.get_class().get_name())
    # 各种尺寸读取方式
    for fn in ("blueprint_get_size_x", "blueprint_get_size_y"):
        try:
            f = getattr(t, fn)
            out.append("  %s = %s" % (fn, f()))
        except Exception as e:
            out.append("  %s err %s" % (fn, str(e)[:40]))
    # 平台数据
    try:
        pd = t.get_platform_data()
        if pd:
            out.append("  platform=%s sizeX=%s sizeY=%s format=%s numMips=%s" % (
                pd.get_editor_property("platform"),
                pd.get_editor_property("size_x"),
                pd.get_editor_property("size_y"),
                pd.get_editor_property("pixel_format"),
                pd.get_editor_property("num_mips")))
        else:
            out.append("  !! platform_data 为空（贴图没有编译数据！）")
    except Exception as e:
        out.append("  platform_data err %s" % str(e)[:60])
    # 源文件
    try:
        out.append("  source_file=%s" % t.get_editor_property("source_file"))
    except Exception:
        pass
    # 是否在磁盘上有 .uasset
    pkg = p + ".uasset"
    import os
    disk = pkg.replace("/Game/", r"C:\Users\25227\Documents\robot_game\ue\Content/")
    out.append("  disk=%s exists=%s size=%s" % (
        disk, os.path.exists(disk),
        os.path.getsize(disk) if os.path.exists(disk) else -1))

with open(r"C:\Users\25227\Documents\robot_game\docs\floor_diag2.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("FLOOR_DIAG2_DONE")
