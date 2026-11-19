# -*- coding: utf-8 -*-
"""下载 Hunyuan3D 多视图权重（hunyuan3d-dit-v2-mv）到本地 models 目录。

背景：当前只装了 hunyuan3d-dit-v2-mini（单图版）。多视图版能同时吃
前/后/左/右 4 张图，背面不再是"猜"出来的。

权重：tencent/Hunyuan3D-2mv / hunyuan3d-dit-v2-mv / model.fp16.safetensors
      （4.59 GB，HF 公开可下）
放置：C:\\AI\\Hunyuan3D\\models\\hunyuan3d-dit-v2-mv\\model.fp16.safetensors
      + config.yaml（HF 仓库里那个）

⚠️ 断点续传：用 Range 请求，已下部分不重下。
"""
import os
import sys
import ssl
import json
import urllib.request

BASE = "https://huggingface.co/tencent/Hunyuan3D-2mv/resolve/main/hunyuan3d-dit-v2-mv/"
DEST = r"C:\AI\Hunyuan3D\models\hunyuan3d-dit-v2-mv"
FILES = ["config.yaml", "model.fp16.safetensors"]

ctx = ssl.create_default_context()
UA = {"User-Agent": "Mozilla/5.0"}


def download(name):
    os.makedirs(DEST, exist_ok=True)
    dst = os.path.join(DEST, name)
    url = BASE + name + "?download=true"
    have = os.path.getsize(dst) if os.path.exists(dst) else 0
    headers = dict(UA)
    if have:
        headers["Range"] = "bytes=%d-" % have
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=120, context=ctx) as r:
        total = r.headers.get("Content-Length")
        total = int(total) + have if total else None
        mode = "ab" if have and r.status == 206 else "wb"
        if mode == "wb":
            have = 0
        print("%s: 开始 %s (已有 %.1f MB, 总 %s MB)" % (
            name, mode, have / 1048576.0,
            "%.0f" % (total / 1048576.0) if total else "?"), flush=True)
        done = have
        last = 0
        with open(dst, mode) as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                mb = done / 1048576.0
                if mb - last >= 100:
                    last = mb
                    print("  %s %.0f MB%s" % (
                        name, mb, (" / %.0f" % (total / 1048576.0)) if total else ""),
                        flush=True)
    print("%s 完成 %.1f MB" % (name, os.path.getsize(dst) / 1048576.0), flush=True)


for f in FILES:
    try:
        download(f)
    except Exception as e:
        print("!! %s 失败: %s" % (f, e), flush=True)
        sys.exit(1)
print("HY3D_MV_DOWNLOAD_DONE", flush=True)
