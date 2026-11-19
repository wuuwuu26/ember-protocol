# -*- coding: utf-8 -*-
"""从 Poly Haven 筛选契合「余火协议」科幻工业风的 PBR 材质，列出候选。

Poly Haven API（公开、CC0、无需登录）：
  GET /assets?t=textures          列出所有贴图资产
  GET /files/{id}                 某资产的下载直链（按 1k/2k/4k/8k + png/jpg/exr）
"""
import urllib.request
import ssl
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def get(u):
    r = urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                               timeout=60, context=ctx)
    return json.loads(r.read().decode("utf-8", "replace"))


assets = get("https://api.polyhaven.com/assets?t=textures")
print("Poly Haven 贴图资产总数：%d" % len(assets))

# 工业 / 科幻相关关键词（按用途分组）
GROUPS = {
    "地面(混凝土/水泥)": ["concrete", "cement", "asphalt", "pavement", "floor"],
    "风化金属/锈": ["rust", "metal", "steel", "corrugated", "painted_metal", "iron"],
    "碎石/瓦砾": ["gravel", "rock", "rubble", "debris", "ground"],
    "工业墙面": ["brick", "concrete_wall", "plaster", "panel", "warehouse"],
}

sel = {}
for group, kws in GROUPS.items():
    hits = []
    for aid, a in assets.items():
        name = (a.get("name", "") + " " + aid).lower()
        tags = " ".join(a.get("tags", [])).lower()
        cats = " ".join(str(c) for c in a.get("categories", [])).lower()
        blob = name + " " + tags + " " + cats
        if any(k in blob for k in kws):
            hits.append((aid, a.get("name"), a.get("categories")))
    sel[group] = hits
    print("\n=== %s：%d 个 ===" % (group, len(hits)))
    for aid, name, cats in hits[:18]:
        print("  %-38s %-34s %s" % (aid[:38], str(name)[:34], str(cats)[:40]))

with open(r"C:\Users\25227\Documents\robot_game\docs\polyhaven_candidates.json",
          "w", encoding="utf-8") as f:
    json.dump({g: [list(x) for x in v] for g, v in sel.items()},
              f, indent=2, ensure_ascii=False)
print("\nPOLYHAVEN_LIST_DONE")
