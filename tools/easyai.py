# -*- coding: utf-8 -*-
"""调用本地 EasyAI 生成图片的封装。

引擎：
  krea2  —— Krea 2 Turbo（默认，最通用）
  zimage —— Z-Image（8 步，快）
  moss   —— MOSS-Image（文字排版强，**要求图上出现文字时必须用这个**）

服务端 http://127.0.0.1:7860
"""
import json
import os
import shutil
import time
import urllib.request


API = "http://127.0.0.1:7860/api/generate"
STATUS = "http://127.0.0.1:7860/api/status"
OUT_DIR = r"C:\AI\EasyAI\outputs"


def status():
    with urllib.request.urlopen(STATUS, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def generate(prompt, out_path, engine="krea2", ratio="1:1",
             resolution="fast_1k", negative="", timeout=600, mode="text2image",
             denoise=0.65, ref_image=None, second_pass=True):
    """生成一张图并复制到 out_path。返回 out_path（失败返回 None）。"""
    payload = {
        "mode": mode,
        "engine": engine,
        "prompt": prompt,
        "negative_prompt": negative,
        "ratio": ratio,
        "resolution_mode": resolution,
        "denoise": denoise,
        "enable_second_pass": second_pass,
    }
    if ref_image:
        payload["ref_image"] = ref_image

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API, data=data,
                                 headers={"Content-Type": "application/json"})
    print("[gen] engine=%s ratio=%s : %s" % (engine, ratio, prompt[:70]))
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            res = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print("[gen] 请求异常: %s" % e)
        return None

    if not res.get("success"):
        print("[gen] 失败: %s" % str(res)[:300])
        return None

    url = res.get("image_url") or res.get("media_url") or res.get("path")
    if not url:
        print("[gen] 返回里没有图片路径: %s" % str(res)[:300])
        return None

    src = url if os.path.isabs(url) else os.path.join(OUT_DIR, os.path.basename(url))
    if not os.path.exists(src):
        alt = os.path.join(OUT_DIR, os.path.basename(url))
        src = alt if os.path.exists(alt) else src
    if not os.path.exists(src):
        print("[gen] 找不到生成的文件: %s" % src)
        return None

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    shutil.copy2(src, out_path)
    print("[gen] ok %.1fs -> %s" % (time.time() - t0, out_path))
    return out_path


if __name__ == "__main__":
    print(status())
