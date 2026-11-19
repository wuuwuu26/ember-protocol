# -*- coding: utf-8 -*-
"""探测 Fab 是否有可匿名获取的资产数据/下载（对标上一轮 Cosmos 的做法）。"""
import urllib.request
import ssl
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
      "Accept": "application/json"}

URLS = [
    # Fab 前端用的搜索/商品 API（从 github gist 里看到的 search?seller=Quixel）
    "https://www.fab.com/i/listings/search?seller=Quixel&count=3",
    "https://www.fab.com/api/v1/listings/search?seller=Quixel",
    "https://api.fab.com/v1/listings/search?seller=Quixel",
    # Epic 的公开 catalog 接口
    "https://catalog-public-service-prod06.ol.epicgames.com/catalog/api/shared/namespace/ue/bulk/offers?namespace=89efe5924d3d467c839449ab6ab52e7f",
]

for u in URLS:
    try:
        req = urllib.request.Request(u, headers=UA)
        with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
            body = r.read(400)
            print("OK  %s  status=%s  head=%s" % (u[:70], r.status, body[:120]))
    except Exception as e:
        print("ERR %s  -> %s" % (u[:70], str(e)[:100]))
print("FAB_PROBE_DONE")
