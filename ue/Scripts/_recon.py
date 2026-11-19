import unreal

def L(s):
    print("[侦察] %s" % s)

# ── 1. 骨骼名称 ──
L("========== 骨骼结构 ==========")
for p in ("/Game/RobotGame/Art/Characters/SK_Chassis_Light",
          "/Game/RobotGame/Art/Characters/SK_Enemy_Guard"):
    sk = unreal.EditorAssetLibrary.load_asset(p)
    if not sk:
        L("  %s 加载失败" % p.split("/")[-1])
        continue
    L("  --- %s ---" % p.split("/")[-1])
    try:
        skel = sk.get_editor_property("skeleton")
        L("    Skeleton 资产: %s" % (skel.get_name() if skel else "无"))
        if skel:
            names = []
            try:
                names = [str(b) for b in skel.get_editor_property("bone_names")]
            except Exception as e1:
                try:
                    names = [str(b) for b in skel.get_editor_property("bone_tree")]
                except Exception as e2:
                    L("    读取骨骼名失败: %s / %s" % (str(e1)[:60], str(e2)[:60]))
            L("    骨骼数: %d" % len(names))
            L("    骨骼: %s" % ", ".join(names[:40]))
    except Exception as e:
        L("    异常: %s" % str(e)[:120])

# ── 2. 关卡现状 ──
L("========== 关卡现状 ==========")
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
les.load_level("/Game/RobotGame/Maps/Persistent/L_TestArena")
actors = unreal.EditorLevelLibrary.get_all_level_actors()
L("  Actor 总数: %d" % len(actors))
counts = {}
for a in actors:
    n = a.get_class().get_name()
    counts[n] = counts.get(n, 0) + 1
for k, v in sorted(counts.items(), key=lambda x: -x[1]):
    L("    %-32s x%d" % (k, v))

L("  --- 敌人实例 ---")
for a in actors:
    if "Enemy" in a.get_class().get_name():
        comp = None
        try:
            comp = a.get_editor_property("mesh")
        except Exception:
            pass
        loc = a.get_actor_location()
        L("    %s @ (%.0f,%.0f,%.0f) mesh=%s" % (
            a.get_name(), loc.x, loc.y, loc.z,
            comp.skeletal_mesh.get_name() if (comp and comp.skeletal_mesh) else "❌无"))

# ── 3. 蓝图默认值 ──
L("========== 蓝图默认值 ==========")
for p, label in (("/Game/RobotGame/Blueprints/BP_Enemy", "BP_Enemy"),
                 ("/Game/RobotGame/Blueprints/BP_RobotCharacter", "BP_RobotCharacter")):
    bp = unreal.EditorAssetLibrary.load_asset(p)
    if not bp:
        L("  %s 加载失败" % label)
        continue
    cdo = unreal.get_default_object(bp.generated_class())
    try:
        mesh = cdo.get_editor_property("mesh")
        L("  %s: mesh=%s" % (label,
            mesh.skeletal_mesh.get_name() if mesh.skeletal_mesh else "❌无"))
        if mesh.skeletal_mesh:
            L("    相对位置=%s 缩放=%s" % (mesh.get_editor_property("relative_location"),
                                          mesh.get_editor_property("relative_scale3d")))
            for i in range(mesh.get_num_materials()):
                L("    材质槽%d = %s" % (i, mesh.get_material(i).get_name() if mesh.get_material(i) else "空"))
    except Exception as e:
        L("  %s 读取 mesh 失败: %s" % (label, str(e)[:100]))

# ── 4. 分辨率设置 ──
L("========== 显示设置 ==========")
try:
    gus = unreal.GameUserSettings.get_game_user_settings()
    L("  当前分辨率: %s" % gus.get_screen_resolution())
    L("  全屏模式: %s" % gus.get_fullscreen_mode())
    res = gus.get_supported_fullscreen_resolutions()
    L("  支持的分辨率数: %d" % len(res))
    L("  前 12 个: %s" % ", ".join("%dx%d" % (r.x, r.y) for r in res[:12]))
except Exception as e:
    L("  读取失败: %s" % str(e)[:150])
