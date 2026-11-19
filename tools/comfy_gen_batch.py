# -*- coding: utf-8 -*-
"""批量生成工业资产概念图（第一百一十轮）。

为「余火协议」工业竞技场补充专属资产：
  - pipe_junction  管道接头（已成）
  - airlock        气闸门（远端闸门处的重型门）
  - crane_arm      废弃机械吊臂
  - bunker_vent    地堡通风机组
  - mech_core      废弃机甲核心（场景叙事焦点）

全部：单体、干净浅灰背景、主体居中完整、写实工业风 —— 喂给 Hunyuan3D。
"""
import json
import urllib.request
import urllib.parse
import time
import os

HOST = "http://127.0.0.1:8188"
OUTDIR = r"C:\AI\Hunyuan3D\input"


def api(path, payload=None):
    url = HOST + path
    if payload is None:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=30) as r:
            return json.loads(r.read())
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def workflow(prompt, prefix, seed, w=1024, h=1024, steps=8):
    return {
        "1": {"class_type": "UNETLoader",
              "inputs": {"unet_name": "z_image_turbo_int8_convrot.safetensors",
                         "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader",
              "inputs": {"clip_name": "qwen_3_4b_fp8_mixed.safetensors",
                         "type": "lumina2"}},
        "3": {"class_type": "VAELoader",
              "inputs": {"vae_name": "z_image_ae.safetensors"}},
        "4": {"class_type": "CLIPTextEncode",
              "inputs": {"text": prompt, "clip": ["2", 0]}},
        "5": {"class_type": "EmptyLatentImage",
              "inputs": {"width": w, "height": h, "batch_size": 1}},
        "6": {"class_type": "KSampler",
              "inputs": {"model": ["1", 0], "positive": ["4", 0],
                         "negative": ["7", 0], "latent_image": ["5", 0],
                         "seed": seed, "steps": steps, "cfg": 1.0,
                         "sampler_name": "euler", "scheduler": "simple",
                         "denoise": 1.0}},
        "7": {"class_type": "CLIPTextEncode",
              "inputs": {"text": "blurry, low quality, multiple objects, "
                                 "text, watermark, people",
                         "clip": ["2", 0]}},
        "8": {"class_type": "VAEDecode",
              "inputs": {"samples": ["6", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage",
              "inputs": {"images": ["8", 0], "filename_prefix": prefix}},
    }


TAIL = (" isolated on plain light grey background, product shot, "
        "centered, entire object visible, photorealistic, high detail, "
        "studio lighting, no text, no people")

ASSETS = {
    "airlock": "A single heavy industrial airlock door, thick riveted steel frame, "
               "hydraulic pistons, yellow-black hazard stripes, sci-fi facility door",
    "crane_arm": "A single abandoned industrial robotic crane arm, rusted orange "
                 "and dark steel, exposed hydraulic joints and cables, "
                 "sci-fi scrapyard machine",
    "bunker_vent": "A single heavy industrial ventilation unit, boxy metal housing, "
                   "large fan grille, rusty bolts, sci-fi bunker equipment",
    "mech_core": "A single damaged mech core cylinder, torn armor plating, "
                 "exposed glowing blue energy conduit, sci-fi reactor unit",
    "generator": "A single industrial power generator unit, heavy steel casing, "
                 "copper pipes, warning labels, sci-fi facility equipment",
}


def queue(name, seed):
    wf = workflow(ASSETS[name] + TAIL, "hy3d_src_" + name, seed)
    return api("/prompt", {"prompt": wf}).get("prompt_id")


def wait(pid, timeout=400):
    t0 = time.time()
    while time.time() - t0 < timeout:
        h = api("/history/" + pid)
        if pid in h:
            return h[pid]
        time.sleep(1.5)
    return None


def fetch(hist, dest):
    for node in hist.get("outputs", {}).values():
        for img in node.get("images", []):
            q = urllib.parse.urlencode({
                "filename": img["filename"],
                "subfolder": img.get("subfolder", ""),
                "type": img.get("type", "output")})
            with urllib.request.urlopen(HOST + "/view?" + q, timeout=60) as r:
                data = r.read()
            with open(dest, "wb") as f:
                f.write(data)
            return len(data)
    return 0


if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    seed = 1000
    for name in ASSETS:
        dest = os.path.join(OUTDIR, "gen_%s.png" % name)
        if os.path.exists(dest) and os.path.getsize(dest) > 10000:
            print("[skip] %s 已存在" % name, flush=True)
            continue
        pid = queue(name, seed)
        seed += 7
        print("[gen] %-12s pid=%s" % (name, pid), flush=True)
        h = wait(pid)
        if not h:
            print("   !! 超时", flush=True)
            continue
        n = fetch(h, dest)
        print("   saved %.0f KB" % (n / 1024), flush=True)
    print("COMFY_BATCH_DONE")
