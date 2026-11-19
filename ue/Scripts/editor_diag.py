"""
编辑器内诊断脚本 —— 在运行中的编辑器里执行
================================================================
在编辑器的 Output Log 里输入以下命令执行：
    py exec(open(r'C:/Users/25227/Documents/robot_game/ue/Scripts/editor_diag.py').read())

它会报告：材质、网格渲染数据、着色器编译状态、关卡内容。
"""

import unreal


def log(m):
    unreal.log("[编辑器诊断] %s" % m)
    print("[编辑器诊断] %s" % m)


def main():
    log("=" * 50)

    # ── 1. 引擎材质能否正常加载 ──
    mat = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/BasicShapeMaterial")
    log("BasicShapeMaterial 加载: %s" % ("成功" if mat else "失败"))

    # ── 2. 网格体渲染数据 ──
    for p in ("/Game/RobotGame/Art/Environment/SM_Env_Floor",
              "/Engine/BasicShapes/Cube"):
        m = unreal.EditorAssetLibrary.load_asset(p)
        if not m:
            log("%s: ❌ 加载失败" % p.split("/")[-1])
            continue
        try:
            tri = m.get_num_triangles(0)
            vtx = m.get_num_vertices(0)
            log("%s: 三角形=%d 顶点=%d" % (p.split("/")[-1], tri, vtx))
        except Exception as e:
            log("%s: 读取失败 %s" % (p.split("/")[-1], str(e)[:50]))

    # ── 3. 关卡内容 ──
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    sm = [a for a in actors if isinstance(a, unreal.StaticMeshActor)]
    log("Actor 总数=%d  静态网格=%d" % (len(actors), len(sm)))

    if sm:
        c = sm[0].static_mesh_component
        mesh = c.static_mesh
        log("样例 %s: mobility=%s 可见=%s 网格=%s" % (
            sm[0].get_name(),
            c.get_editor_property("mobility"),
            c.is_visible(),
            mesh.get_name() if mesh else "无"))
        # 材质
        try:
            n = mesh.get_num_materials(0) if mesh else 0
            for i in range(n):
                mm = mesh.get_material(i)
                log("  材质槽%d: %s" % (i, mm.get_name() if mm else "空"))
        except Exception as e:
            log("  材质读取失败: %s" % str(e)[:50])

    # ── 4. 灯光 ──
    for a in actors:
        cn = a.get_class().get_name()
        if "DirectionalLight" in cn or "SkyLight" in cn:
            for p in ("light_component", "sky_light_component"):
                try:
                    lc = a.get_editor_property(p)
                except Exception:
                    continue
                if not lc:
                    continue
                log("%s: mobility=%s intensity=%s" % (
                    cn, lc.get_editor_property("mobility"),
                    lc.get_editor_property("intensity")))
                break

    # ── 5. 关键 CVar 的运行时值 ──
    import unreal as u
    names = ["r.Nanite", "r.Nanite.ProjectEnabled", "r.ForwardShading",
             "r.Shadow.Virtual.Enable", "r.AllowStaticLighting",
             "r.AntiAliasingMethod", "r.ScreenPercentage",
             "r.DefaultFeature.AutoExposure"]
    for n in names:
        try:
            cv = u.SystemLibrary.get_console_variable_value(n)
            log("CVar %-32s = %s" % (n, cv))
        except Exception:
            pass

    log("=" * 50)


main()
