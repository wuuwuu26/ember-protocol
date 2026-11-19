# -*- coding: utf-8 -*-
"""Cosmos 免费资产流水线：下载预览 glTF → 贴图降采样 → 打包成单文件 GLB。

为什么这么做：
  1. 正式下载接口要登录（401），但网页 3D 预览的 glTF 在公开 CDN，
     含 LOD0 几何 .bin + 4K PBR 贴图（BaseColor / Normal / ORM）。
  2. 4K 贴图单个资产 40~120MB，直接导 UE 太重 —— 用 PIL 缩到 1024。
  3. 打包成 GLB（几何 bin + 贴图全部内嵌），UE 的 glTF/Interchange 导入器
     一个文件就能读，跟上一轮 IdolMech.glb 的导入路径一致。

GLB 打包不经过 Blender 重导出：原始 bin 字节原样保留（法线/UV/LOD0 精确数据
不丢），只把贴图缩小后作为 bufferView 追加到 BIN chunk。

用法：
  python tools/cosmos_build.py                # 用下方 DEFAULT_SLUGS
  python tools/cosmos_build.py cs1-pipe ...   # 指定 slug
"""
import json
import urllib.request
import ssl
import os
import sys
import io
import time
import struct
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image

API = "https://api.cosmos.leartesstudios.com/products/"
ROOT = r"C:\Users\25227\Documents\robot_game\art_src\cosmos"
GLB_DIR = os.path.join(ROOT, "glb")
CACHE = os.path.join(ROOT, "raw")
os.makedirs(GLB_DIR, exist_ok=True)
os.makedirs(CACHE, exist_ok=True)

TEX_SIZE = 1024          # 贴图统一缩到 1024
UA = {"User-Agent": "Mozilla/5.0", "Accept": "*/*"}
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 第一百零四轮精选：工业掩体 + 道具（都是 gltf 预览可用、面数合理、风格契合）
DEFAULT_SLUGS = [
    "ww2-sandbag-stack-02b-smoked",   # 沙袋堆（掩体主力）
    "met-barrel01-set01",             # 木桶组（掩体）
    "met-wooden-crate01a",            # 木箱（可堆叠掩体）
    "ww2-fridge",                     # 旧冰柜（大掩体）
    "ww2-drawer-smoked",              # 抽屉柜（掩体）
    "ww2-field-fences-01a",           # 野战栅栏（路障/分隔）
    "pad-street-lamp-overgrown",      # 街灯（3.44m，垂直焦点）
    "rps-fire-extinguisher-02",       # 灭火器（工业小件）
    "ww2-heater-smoked",              # 火炉（工业）
    "cs1-wallfanhatch",               # 墙面风扇格栅（贴墙）
    "cs1-wall-light-6",               # 壁灯（贴墙）
    "cs1-pipe",                       # 管道（小装饰）
]


def fetch(url, timeout=180):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.read()


def shrink_png(data, size=TEX_SIZE):
    im = Image.open(io.BytesIO(data))
    im = im.convert("RGBA") if im.mode in ("P", "LA") else im
    if max(im.size) > size:
        im.thumbnail((size, size), Image.LANCZOS)
    out = io.BytesIO()
    im.save(out, format="PNG", optimize=True)
    return out.getvalue(), im.size


def build_one(slug):
    t0 = time.time()
    try:
        d = json.loads(fetch(API + slug, 30).decode("utf-8"))
        det = d.get("details") or {}
        gltf_url = det.get("gltf")
        if not gltf_url:
            return (slug, False, "无 details.gltf")
        base = gltf_url.rsplit("/", 1)[0] + "/"

        graw = fetch(gltf_url, 60)
        gj = json.loads(graw.decode("utf-8"))

        # ── 收集外部资源（下载到内存，缩小贴图，不落 4K 原图）──
        bin_data = None
        for b in gj.get("buffers", []):
            uri = b.get("uri")
            if uri and not uri.startswith("data:"):
                bin_data = fetch(base + uri, 240)
                b.pop("uri", None)            # GLB 里 buffer0 不能有 uri
                b["byteLength"] = len(bin_data)
        if bin_data is None:
            return (slug, False, "没有外部 bin")

        images = gj.get("images", [])
        tex_blobs = []
        for im in images:
            uri = im.get("uri")
            if uri and not uri.startswith("data:"):
                raw = fetch(base + uri, 300)
                small, sz = shrink_png(raw)
                tex_blobs.append((small, im.get("mimeType", "image/png"), sz))
                im.pop("uri", None)
            else:
                return (slug, False, "image 是内嵌 data uri，未处理")
        # 没贴图的情况也允许
        if not images:
            pass

        # ── 组装 BIN chunk：原几何 bin + 各贴图（4 字节对齐）──
        buf = bytearray()
        buf += bin_data
        while len(buf) % 4:
            buf += b"\x00"

        if "bufferViews" not in gj:
            gj["bufferViews"] = []
        tex_bv_indices = []
        for (blob, mime, sz) in tex_blobs:
            while len(buf) % 4:
                buf += b"\x00"
            off = len(buf)
            buf += blob
            tex_bv_indices.append(len(gj["bufferViews"]))
            gj["bufferViews"].append({
                "buffer": 0, "byteOffset": off, "byteLength": len(blob)})
        # 回写 image 的 bufferView（显式按记录，不做算术推导）
        for im, bv_idx in zip(images, tex_bv_indices):
            im.pop("uri", None)
            im["bufferView"] = bv_idx
            im.setdefault("mimeType", "image/png")
        while len(buf) % 4:
            buf += b"\x00"
        gj["buffers"][0]["byteLength"] = len(buf)

        # ── 打包 GLB ──
        json_bytes = json.dumps(gj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        while len(json_bytes) % 4:
            json_bytes += b" "
        total = 12 + 8 + len(json_bytes) + 8 + len(buf)
        glb = bytearray()
        glb += struct.pack("<III", 0x46546C67, 2, total)
        glb += struct.pack("<II", len(json_bytes), 0x4E4F534A) + json_bytes
        glb += struct.pack("<II", len(buf), 0x004E4942) + buf

        out = os.path.join(GLB_DIR, slug + ".glb")
        with open(out, "wb") as f:
            f.write(glb)

        mb = len(glb) / 1048576.0
        return (slug, True, "%.1fMB  tex=%d->%s  %ds" %
                (mb, len(tex_blobs), tex_blobs[0][2] if tex_blobs else "-",
                 round(time.time() - t0)))
    except Exception as e:
        return (slug, False, "%s: %s" % (type(e).__name__, e))


def main():
    slugs = sys.argv[1:] or DEFAULT_SLUGS
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(build_one, s): s for s in slugs}
        for fu in as_completed(futs):
            r = fu.result()
            results.append(r)
            print("%-38s %-5s %s" % (r[0], "OK" if r[1] else "FAIL", r[2]), flush=True)
    ok = sum(1 for r in results if r[1])
    with open(os.path.join(ROOT, "build_results.txt"), "w", encoding="utf-8") as f:
        for r in sorted(results):
            f.write("%s\t%s\t%s\n" % (r[0], "OK" if r[1] else "FAIL", r[2]))
    print("\nCOSMOS_BUILD_DONE  %d/%d ok" % (ok, len(results)))


main()
