# -*- coding: utf-8 -*-
"""全自动批量下载 Poly Haven CC0 工业 PBR 材质（第一百零六轮）。

用户不想在 Fab 一个个点下载 —— 改用公开 CC0 源，我全自动抓。

每套材质取 3 张 2K JPG：
  Diffuse -> BaseColor
  nor_gl  -> Normal (OpenGL, UE 用这套)
  arm     -> 打包 AO/Roughness/Metallic（UE 里按通道拆）

材质精选（契合「深蓝工业竞技场 / 余火协议」）：
  concrete_floor_02   工业混凝土地面（主地面）
  concrete_wall_001   风化混凝土墙（围墙）
  factory_wall        工厂墙面（金属+漆，工业感强）
  rusty_metal         锈铁（掩体/道具）
  corrugated_iron     波纹铁皮（临时挡板）
  metal_grate_rusty   锈金属格栅（地面/平台细节）
"""
import urllib.request
import ssl
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = r"C:\Users\25227\Documents\robot_game\art_src\polyhaven"
os.makedirs(ROOT, exist_ok=True)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

MATERIALS = [
    "concrete_floor_02",
    "concrete_wall_001",
    "factory_wall",
    "rusty_metal",
    "corrugated_iron",
    "metal_grate_rusty",
]
# channel -> 本地文件名后缀 + UE 用途
CHANNELS = [
    ("Diffuse", "BaseColor"),
    ("nor_gl", "Normal"),
    ("arm", "ARM"),
]
RES = "2k"
FMT = "jpg"


def get_json(u):
    r = urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                               timeout=60, context=ctx)
    return json.loads(r.read().decode("utf-8", "replace"))


def download(url, dst, timeout=180):
    if os.path.exists(dst) and os.path.getsize(dst) > 10000:
        return os.path.getsize(dst), "cached"
    r = urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                               timeout=timeout, context=ctx)
    data = r.read()
    with open(dst, "wb") as f:
        f.write(data)
    return len(data), "new"


def one(aid):
    t0 = time.time()
    try:
        files = get_json("https://api.polyhaven.com/files/" + aid)
        out = os.path.join(ROOT, aid)
        os.makedirs(out, exist_ok=True)
        got = 0
        total = 0
        for chan, suffix in CHANNELS:
            if chan not in files:
                return (aid, False, "缺通道 %s" % chan)
            node = files[chan]
            if RES not in node:
                res = [k for k in ("2k", "1k", "4k") if k in node]
                if not res:
                    return (aid, False, "无 %s 档位" % RES)
                r2 = res[0]
            else:
                r2 = RES
            fmts = node[r2]
            fmt = FMT if FMT in fmts else list(fmts.keys())[0]
            meta = fmts[fmt]
            url = meta["url"] if isinstance(meta, dict) else meta
            dst = os.path.join(out, "%s_%s.jpg" % (aid, suffix))
            n, st = download(url, dst)
            got += 1
            total += n
        return (aid, True, "%d 张 %.1fMB  %ds" %
                (got, total / 1048576.0, round(time.time() - t0)))
    except Exception as e:
        return (aid, False, "%s: %s" % (type(e).__name__, e))


results = []
with ThreadPoolExecutor(max_workers=6) as ex:
    futs = {ex.submit(one, a): a for a in MATERIALS}
    for fu in as_completed(futs):
        r = fu.result()
        results.append(r)
        print("%-24s %-5s %s" % (r[0], "OK" if r[1] else "FAIL", r[2]), flush=True)

with open(r"C:\Users\25227\Documents\robot_game\docs\polyhaven_dl.txt",
          "w", encoding="utf-8") as f:
    for r in sorted(results):
        f.write("%s\t%s\t%s\n" % (r[0], "OK" if r[1] else "FAIL", r[2]))
ok = sum(1 for r in results if r[1])
print("\nPOLYHAVEN_DL_DONE  %d/%d" % (ok, len(results)))
