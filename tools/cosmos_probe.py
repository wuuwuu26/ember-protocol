# -*- coding: utf-8 -*-
"""探测 Cosmos 免费资产的公开 viewer glTF 是否可直接取用。

背景：
  正式下载接口 POST /products/download/{slug} 返回 401 (需要登录)。
  但网页的 3D 预览器用了一组公开的 glTF（details.gltf），
  位于 https://cdn.cosmos.leartesstudios.com/viewer/{folder}/ 下，
  含几何 .bin + PBR 贴图。这里验证能否完整拿到一个资产。
"""
import json
import urllib.request
import urllib.error
import os
import ssl

API = "https://api.cosmos.leartesstudios.com/products/"
CDN = "https://cdn.cosmos.leartesstudios.com/viewer/"
OUT = r"C:\Users\25227\Documents\robot_game\docs\cosmos_probe.txt"
DL = r"C:\Users\25227\Documents\robot_game\art_src\cosmos_probe"
os.makedirs(DL, exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

UA = {"User-Agent": "Mozilla/5.0", "Accept": "*/*"}


def get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.read(), r.status


def head(url, timeout=20):
    req = urllib.request.Request(url, headers=UA, method="HEAD")
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return int(r.headers.get("Content-Length", -1)), r.status


lines = []


def log(s):
    lines.append(str(s))
    print(s)


# 科幻 / 工业 / 掩体候选
CANDIDATES = [
    "cs1-pipe",
    "cs1-double-barrier-b",
    "cs1-wallfanhatch",
    "cs1-wall-light-6",
    "cs1-television",
    "pad-street-lamp-overgrown",
    "rps-fire-extinguisher-02",
    "ww2-sandbag-stack-02b-smoked",
    "met-wooden-crate01a",
    "met-barrel01-set01",
    "ww2-field-fences-01a",
    "cs1-wired-fence-start",
    "cs1-globe",
    "cs1-folding-table",
]

summary = []
for slug in CANDIDATES:
    row = {"slug": slug}
    try:
        raw, _ = get(API + slug)
        d = json.loads(raw.decode("utf-8"))
        det = d.get("details") or {}
        row["title"] = d.get("title")
        row["folder"] = (d.get("plugin") or {}).get("folder")
        row["lods"] = det.get("lods")
        row["poly_lod0"] = (det.get("polycount") or {}).get("lod0")
        row["size"] = det.get("object_size")
        g = det.get("gltf")
        row["gltf"] = bool(g)
        if g:
            try:
                graw, st = get(g, timeout=30)
                gj = json.loads(graw.decode("utf-8"))
                row["gltf_bytes"] = len(graw)
                row["n_images"] = len(gj.get("images", []))
                row["n_meshes"] = len(gj.get("meshes", []))
                row["buffers"] = [b.get("uri") for b in gj.get("buffers", [])]
                row["image_uris"] = [im.get("uri") for im in gj.get("images", [])]
                # 目录前缀（gltf 所在目录）
                base = g.rsplit("/", 1)[0] + "/"
                # 试下载 bin 与第一张贴图
                if row["buffers"] and row["buffers"][0]:
                    bu = base + row["buffers"][0]
                    blen, bst = head(bu)
                    row["bin_len"] = blen
                    row["bin_status"] = bst
                if row["image_uris"] and row["image_uris"][0]:
                    iu = base + row["image_uris"][0]
                    ilen, ist = head(iu)
                    row["img_len"] = ilen
                    row["img_status"] = ist
            except Exception as e:
                row["gltf_err"] = str(e)
        summary.append(row)
        log("%-34s folder=%-24s gltf=%s imgs=%s bin=%s img=%s" % (
            slug, str(row.get("folder")), row.get("gltf"),
            row.get("n_images"), row.get("bin_len"), row.get("img_len")))
    except Exception as e:
        row["err"] = str(e)
        summary.append(row)
        log("%-34s ERR %s" % (slug, e))

with open(OUT, "wb") as f:
    f.write("\n".join(lines).encode("utf-8"))
with open(os.path.join(DL, "summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print("COSMOS_PROBE_DONE")
