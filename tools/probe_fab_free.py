# -*- coding: utf-8 -*-
"""验证 Fab 上 Quixel 资产 isFree 字段的真实情况（是否与 11-05 免费官宣一致）。

匿名接口返回 isFree=false + $4.99，但 Quixel 官宣 2026-11-05 全库免费。
这里：
  1) 搜带 "free" 过滤参数看能否列出免费 Quixel 资产
  2) 看 isFree / startingPrice 的原始结构
  3) 查几个 Megascans Sample 包（历史上是免费的）
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


def first_price(res):
    out = []
    for r in res:
        seller = (r.get("user") or {}).get("sellerName", "")
        out.append((str(r.get("title"))[:40], r.get("isFree"),
                    str(r.get("startingPrice"))[:60], "Quixel" if "quixel" in seller.lower() else seller[:12]))
    return out


tests = [
    "https://www.fab.com/i/listings/search?q=quixel&is_free=true&count=10",
    "https://www.fab.com/i/listings/search?q=quixel%20free&count=10",
    "https://www.fab.com/i/listings/search?q=Derelict%20Corridor%20Megascans%20Sample&count=5",
    "https://www.fab.com/i/listings/search?q=Dark%20Ruins%20Megascans%20Sample&count=5",
    "https://www.fab.com/i/listings/search?q=Industrial%20Abandoned%20Factory&count=3",
]

for u in tests:
    try:
        j = get(u)
        res = j.get("results", [])
        print("=== %s ===" % u.split("?")[1][:55])
        for t in first_price(res[:6]):
            print("   %-42s free=%-6s price=%-30s seller=%s" % t)
    except Exception as e:
        print("=== %s ERR %s ===" % (u.split("?")[1][:55], e))
print("FAB_FREE_DONE")
