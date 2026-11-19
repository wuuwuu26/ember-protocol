# -*- coding: utf-8 -*-
"""在 Fab 匿名搜索接口里找 Quixel Megascans 的真实资产，按工业/科幻场景筛选。

用户要去 Launcher 领取，所以清单里的名字必须是 Fab 上真实可搜到的。
这里搜多个关键词，只保留 sellerName == "Quixel Megascans" 的结果。
"""
import urllib.request
import ssl
import json
import urllib.parse

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def get(u):
    r = urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                               timeout=30, context=ctx)
    return json.loads(r.read().decode("utf-8", "replace"))


def search(q, count=20):
    u = "https://www.fab.com/i/listings/search?q=%s&count=%d" % (
        urllib.parse.quote(q), count)
    try:
        return get(u).get("results", [])
    except Exception as e:
        print("  ERR %s: %s" % (q, e))
        return []


QUERIES = [
    "quixel industrial",
    "quixel abandoned",
    "quixel concrete rubble",
    "quixel rusty metal",
    "quixel factory",
    "quixel debris",
    "quixel pipe",
    "quixel sci-fi",
    "quixel concrete wall",
    "quixel gravel ground",
    "megascans industrial",
    "megascans abandoned factory",
    "quixel megascans 3d props",
]

seen = {}
qx = []
for q in QUERIES:
    res = search(q)
    hit = 0
    for r in res:
        seller = (r.get("user") or {}).get("sellerName", "")
        if "quixel" not in seller.lower():
            continue
        uid = r.get("uid")
        if uid in seen:
            continue
        seen[uid] = True
        hit += 1
        rec = {
            "title": r.get("title"),
            "uid": uid,
            "type": r.get("listingType"),
            "productType": r.get("productType"),
            "isFree": r.get("isFree"),
            "startingPrice": r.get("startingPrice"),
            "formats": [f.get("code") if isinstance(f, dict) else str(f)
                        for f in (r.get("assetFormats") or [])],
            "category": (r.get("category") or {}).get("name")
                        if isinstance(r.get("category"), dict) else r.get("category"),
            "catalogItemId": r.get("catalogItemId"),
            "offerId": r.get("offerId"),
        }
        qx.append(rec)
    print("%-34s quixel hits=%d (of %d)" % (q, hit, len(res)))

print("\n=== Quixel 去重后共 %d 条 ===" % len(qx))
for r in qx:
    print("  %-52s [%s] free=%s price=%s cat=%s" %
          (str(r["title"])[:52], r["productType"], r["isFree"],
           str(r["startingPrice"])[:18], str(r["category"])[:22]))

with open(r"C:\Users\25227\Documents\robot_game\docs\fab_quixel_assets.json", "w",
          encoding="utf-8") as f:
    json.dump(qx, f, indent=2, ensure_ascii=False)
print("\nFAB_QX_DONE")
