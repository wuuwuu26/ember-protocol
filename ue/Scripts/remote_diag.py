"""
在运行中的编辑器里执行的诊断脚本
================================================================
通过 Python 远程执行（ExecuteFile 模式）在编辑器进程内运行。
"""

import unreal


def main():
    out = []

    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    out.append("Actor 总数: %d" % len(actors))

    sm = [a for a in actors if isinstance(a, unreal.StaticMeshActor)]
    out.append("静态网格 Actor: %d" % len(sm))

    if sm:
        c = sm[0].static_mesh_component
        out.append("样例 %s:" % sm[0].get_name())
        out.append("  mobility=%s" % c.get_editor_property("mobility"))
        out.append("  可见=%s" % c.is_visible())
        out.append("  有网格=%s" % (c.static_mesh.get_name() if c.static_mesh else "无"))

    # 灯光
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
                out.append("%s: mobility=%s intensity=%s" % (
                    cn, lc.get_editor_property("mobility"),
                    lc.get_editor_property("intensity")))
                break

    # 编辑器视口状态
    try:
        ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        out.append("编辑器视口可用: %s" % (ues is not None))
    except Exception as e:
        out.append("视口查询失败: %s" % str(e)[:60])

    print("[远程诊断] " + "\n[远程诊断] ".join(out))


main()
