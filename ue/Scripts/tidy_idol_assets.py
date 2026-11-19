# -*- coding: utf-8 -*-
"""整理 IdolMech 资产（第一百零三轮）

背景：这个模型其实已经有一次**正确的** glTF 导入（Materials/ + StaticMeshes/），
材质是 M_IdolMech_VC，内部是 MaterialExpressionVertexColor —— 颜色全靠顶点色。
我先前绕道 Blender 转 FBX 导入，反而把材质退化成了 glTF 默认的灰色实例。

这一步做三件事：
  1. 删掉 FBX 导入产生的两份错误资产（根目录下的 SM_IdolMech / IdolMechMat）
  2. 把 StaticMeshes/SM_IdolMech 移到 IdolMech/ 根（对齐用户说的路径）
  3. 保留 Materials/ 下的 M_IdolMech_VC 与 IdolMechMat
"""
import unreal

BASE = "/Game/RobotGame/Art/Props/IdolMech"
EAL = unreal.EditorAssetLibrary

out = []


def log(s):
    unreal.log("[IdolTidy] %s" % s)
    out.append(str(s))


# ── 1. 删掉错误资产 ──
for name in ("SM_IdolMech", "IdolMechMat"):
    p = "%s/%s" % (BASE, name)
    if EAL.does_asset_exist(p):
        mat = EAL.load_asset(p)
        if mat and mat.get_class().get_name() == "StaticMesh":
            # 别删掉正确的那份（正确的在 StaticMeshes/ 下）
            slots = mat.get_editor_property("static_materials")
            is_bad = False
            for s in slots:
                mi = s.get_editor_property("material_interface")
                if mi and "IdolMechMat" in mi.get_name():
                    is_bad = True
            if not is_bad:
                log("跳过 %s（材质正常，可能是正确的那份）" % p)
                continue
        EAL.delete_asset(p)
        log("删除错误资产 %s" % p)

# ── 2. 移动正确的网格到根目录 ──
src = BASE + "/StaticMeshes/SM_IdolMech"
dst_dir = BASE
dst_name = "SM_IdolMech"
if EAL.does_asset_exist(src):
    if EAL.does_asset_exist("%s/%s" % (dst_dir, dst_name)):
        EAL.delete_asset("%s/%s" % (dst_dir, dst_name))
    ok = EAL.rename_asset(src, "%s/%s" % (dst_dir, dst_name))
    log("移动 %s → %s/%s : %s" % (src, dst_dir, dst_name, ok))
else:
    log("源资产不存在（可能已经移动过）: %s" % src)

# ── 3. 复核 ──
final = BASE + "/SM_IdolMech"
m = EAL.load_asset(final)
if not m:
    log("!! 最终资产缺失 %s" % final)
else:
    log("最终资产 %s" % final)
    bb = m.get_bounding_box()
    log("  包围盒 size=(%.2f, %.2f, %.2f)  minZ=%.2f  maxZ=%.2f"
        % (bb.max.x - bb.min.x, bb.max.y - bb.min.y, bb.max.z - bb.min.z,
           bb.min.z, bb.max.z))
    for i, s in enumerate(m.get_editor_property("static_materials")):
        mi = s.get_editor_property("material_interface")
        log("  slot%d -> %s" % (i, mi.get_path_name() if mi else "None"))
    EAL.save_asset(final, only_if_is_dirty=False)
    log("  已保存")

with open(r"C:\Users\25227\Documents\robot_game\docs\idol_tidy.txt", "wb") as f:
    f.write("\n".join(out).encode("utf-8"))
unreal.log("IDOL_TIDY_DONE")
