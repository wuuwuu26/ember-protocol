# -*- coding: utf-8 -*-
"""通用 Cosmos viewer glTF 下载器。

给定 slug，从公开 CDN 拉取 glTF + 所有 buffer(.bin) + 所有 image，
落盘到 art_src/cosmos/<slug>/，供 Blender/UE 导入。

用法：
  python tools/cosmos_fetch.py cs1-pipe
  python tools/cosmos_fetch.py cs1-pipe cs1-wall-light-6 ...
"""
import json
import urllib.request
import os
import ssl
import sys
import time

API = "https://api.cosmos.leartesstudios.com/products/"
ROOT = r"C:\Users\25227\Documents\robot_game\art_src\cosmos"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0", "Accept": "*/*"}


def fetch(url, timeout=120):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.read()


def fetch_one(slug):
    d = json.loads(fetch(API + slug, 30).decode("utf-8"))
    det = d.get("details") or {}
    gltf_url = det.get("gltf")
    if not gltf_url:
        return {"slug": slug, "ok": False, "err": "no details.gltf (可能没有预览)"}

    base = gltf_url.rsplit("/", 1)[0] + "/"
    outdir = os.path.join(ROOT, slug)
    os.makedirs(outdir, exist_ok=True)

    graw = fetch(gltf_url, 60)
    gj = json.loads(graw.decode("utf-8"))
    gltf_name = "model.gltf"
    with open(os.path.join(outdir, gltf_name), "wb") as f:
        f.write(graw)

    files = []
    for b in gj.get("buffers", []):
        uri = b.get("uri")
        if uri and not uri.startswith("data:"):
            files.append(uri)
    for im in gj.get("images", []):
        uri = im.get("uri")
        if uri and not uri.startswith("data:"):
            files.append(uri)

    total = 0
    got = 0
    for uri in files:
        # uri 可能带子目录
        safe = uri.replace("/", "_").replace("\\", "_")
        dst = os.path.join(outdir, safe)
        try:
            data = fetch(base + uri, 180)
            with open(dst, "wb") as f:
                f.write(data)
            total += len(data)
            got += 1
            # 把 gltf 里的 uri 改成本地文件名
            for b in gj.get("buffers", []):
                if b.get("uri") == uri:
                    b["uri"] = safe
            for im in gj.get("images", []):
                if im.get("uri") == uri:
                    im["uri"] = safe
        except Exception as e:
            return {"slug": slug, "ok": False, "err": "fetch %s: %s" % (uri, e),
                    "partial": got}

    # 回写 uri 修正后的 gltf
    with open(os.path.join(outdir, gltf_name), "wb") as f:
        f.write(json.dumps(gj, ensure_ascii=False).encode("utf-8"))

    return {"slug": slug, "ok": True, "title": d.get("title"),
            "folder": (d.get("plugin") or {}).get("folder"),
            "files": got, "bytes": total, "size_mb": round(total / 1048576.0, 1),
            "outdir": outdir,
            "meshes": len(gj.get("meshes", [])),
            "materials": len(gj.get("materials", [])),
            "images": len(gj.get("images", []))}


def main():
    slugs = sys.argv[1:]
    if not slugs:
        print("usage: cosmos_fetch.py <slug> [slug ...]")
        return
    results = []
    for s in slugs:
        t = time.time()
        r = fetch_one(s)
        r["secs"] = round(time.time() - t, 1)
        results.append(r)
        print("%-34s ok=%-5s files=%-3s %6s MB  %ss  %s" % (
            s, r["ok"], r.get("files"), r.get("size_mb"),
            r["secs"], r.get("err", "")))
    with open(os.path.join(ROOT, "fetch_results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("COSMOS_FETCH_DONE")


main()
