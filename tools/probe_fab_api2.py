# -*- coding: utf-8 -*-
"""摸清 Fab 匿名搜索接口返回结构 + Quixel 免费资产的公开信息。"""
import urllib.request
import ssl
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def get(u):
    r = urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                               timeout=30, context=ctx)
    return r.read().decode("utf-8", "replace")


queries = [
    "https://www.fab.com/i/listings/search?count=3",
    "https://www.fab.com/i/listings/search?q=megascans&count=3",
    "https://www.fab.com/i/listings/search?seller_name=Quixel%20Megascans&count=3",
]

for u in queries:
    try:
        raw = get(u)
        j = json.loads(raw)
        res = j.get("results", [])
        print("=== %s ===" % u.split("?")[1][:50])
        print("  keys:", list(j.keys()))
        print("  count=%s results=%d next=%s" % (j.get("count"), len(res),
                                                 str(j.get("next"))[:50]))
        if res:
            r0 = res[0]
            print("  result[0] keys:", list(r0.keys()))
            for k in ("uid", "title", "seller", "user", "price", "thumbnails",
                      "listing_type", "formats", "is_free"):
                if k in r0:
                    print("    %s = %s" % (k, str(r0[k])[:150]))
    except Exception as e:
        print("=== %s ERR %s ===" % (u.split("?")[1][:50], e))

with open(r"C:\Users\25227\Documents\robot_game\docs\fab_api_probe.txt", "w",
          encoding="utf-8") as f:
    f.write("done\n")
print("FAB_API_DONE")
