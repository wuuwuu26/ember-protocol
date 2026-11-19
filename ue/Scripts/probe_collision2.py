# -*- coding: utf-8 -*-
import unreal
L = "[碰撞体]"
unreal.log(L + " 开始")
for nm in ("SM_Env_Wall", "SM_Env_Floor", "SM_Prop_Container", "SM_Prop_Terminal"):
    folder = "Environment" if nm.startswith("SM_Env") else "Props"
    sm = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/%s/%s" % (folder, nm))
    if not sm:
        unreal.log("%s 找不到 %s" % (L, nm))
        continue
    out = []
    try:
        bs = sm.get_editor_property("body_setup")
        ag = bs.get_editor_property("agg_geom")
        for k in ("box_elems", "sphere_elems", "convex_elems", "sphyl_elems",
                  "tapered_capsule_elems"):
            try:
                out.append("%s=%d" % (k, len(ag.get_editor_property(k))))
            except Exception as e:
                out.append("%s=?" % k)
        try:
            out.append("simplified=%s" % bs.get_editor_property("b_has_been_simplified"))
        except Exception:
            pass
    except Exception as e:
        out.append("body_setup 读取失败 %s" % str(e)[:60])
    try:
        out.append("complex_as_simple=%s" % sm.get_editor_property("complex_collision_as_simple"))
    except Exception:
        pass
    unreal.log("%s %-22s %s" % (L, nm, "  ".join(out)))
