# -*- coding: utf-8 -*-
"""批量拉取全部免费 asset 的详情：真实尺寸、面数、gltf 预览是否可用。
用于筛选适合做掩体/道具的资产（输出 docs/cosmos_assets_table.txt）。
"""
import json
import urllib.request
import ssl
import time

API = "https://api.cosmos.leartesstudios.com/products/"
FREE = r"C:\Users\25227\Documents\robot_game\art_src\cosmos_probe\..\..\..\..\..\..\docs\cosmos_free.json"
FREE = r"C:\Users\25227\AppData\Local\Temp\opencode\cosmos_free.json"
OUT = r"C:\Users\25227\Documents\robot_game\docs\cosmos_assets_table.txt"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0", "Accept": "*/*"}


def get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.read()


allp = json.load(open(FREE, encoding="utf-8-sig"))
assets = [p for p in allp if p.get("type") == "asset"]
lines = []
rows = []
for p in assets:
    slug = p["slug"]
    try:
        d = json.loads(get(API + slug).decode("utf-8"))
        det = d.get("details") or {}
        sz = det.get("object_size") or {}
        try:
            dims = (float(sz.get("x", 0)), float(sz.get("y", 0)), float(sz.get("z", 0)))
        except Exception:
            dims = (0, 0, 0)
        poly = (det.get("polycount") or {}).get("lod0", "?")
        g = bool(det.get("gltf"))
        folder = (d.get("plugin") or {}).get("folder", "")
        rows.append((slug, p["title"], dims, poly, g, folder))
        lines.append("%-36s %-30s size=(%5.2f,%5.2f,%5.2f)m tris=%-7s gltf=%-5s %s" %
                     (slug, p["title"][:30], dims[0], dims[1], dims[2],
                      str(poly), str(g), folder))
        time.sleep(0.05)
    except Exception as e:
        lines.append("%-36s ERR %s" % (slug, e))

with open(OUT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
print("\n".join(lines))
print("\nCOSMOS_TABLE_DONE  assets=%d" % len(assets))
