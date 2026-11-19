# -*- coding: utf-8 -*-
import unreal
L = "[Alpha]"
for n in ("T_MechDetail", "T_ConcreteDetail"):
    t = unreal.EditorAssetLibrary.load_asset("/Game/RobotGame/Art/Materials/%s" % n)
    if not t:
        unreal.log("%s ❌ %s" % (L, n)); continue
    out = []
    for p in ("compression_settings", "compression_no_alpha", "srgb",
              "has_alpha_channel", "max_texture_size", "never_stream",
              "lod_group", "filter"):
        try:
            out.append("%s=%s" % (p, t.get_editor_property(p)))
        except Exception as e:
            out.append("%s=?" % p)
    unreal.log("%s %-18s %s" % (L, n, " ".join(out)))
