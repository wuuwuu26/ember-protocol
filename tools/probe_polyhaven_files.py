# -*- coding: utf-8 -*-
"""查 Poly Haven 材质 /files/{id} 的结构，确认 2K 直链与可用贴图通道。"""
import urllib.request
import ssl
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

IDS = ["concrete_floor_02", "factory_wall", "rusty_metal", "corrugated_iron",
       "metal_grate_rusty", "concrete_wall_001", "blue_metal_plate"]

for aid in IDS:
    try:
        r = urllib.request.urlopen(urllib.request.Request(
            "https://api.polyhaven.com/files/" + aid, headers=UA),
            timeout=30, context=ctx)
        j = json.loads(r.read().decode("utf-8", "replace"))
        print("=== %s ===" % aid)
        print("  channels:", list(j.keys()))
        ch = j.get("Diffuse") or j.get("diffuse") or {}
        if ch:
            print("  Diffuse res:", list(ch.keys()))
            k2 = "2k" if "2k" in ch else list(ch.keys())[-1]
            print("  Diffuse %s formats: %s" % (k2, list(ch[k2].keys())))
            for fmt, meta in ch[k2].items():
                if isinstance(meta, dict):
                    print("    %s size=%s url=%s" % (
                        fmt, meta.get("size"), str(meta.get("url"))[:90]))
    except Exception as e:
        print("=== %s ERR %s ===" % (aid, str(e)[:100]))
print("POLYHAVEN_FILES_DONE")
