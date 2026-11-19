# -*- coding: utf-8 -*-
"""第一百一十八轮：机甲/机器人碎骸概念图（ComfyUI 批量生图）。

主题：余火协议战场的机甲残骸，强化废墟叙事。
4 个单体、干净浅灰背景、主体居中完整 —— 喂给 Hunyuan3D 单图转 3D。
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
                                 "text, watermark, people, character standing",
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
    # 破损机甲躯干：胸腔外露、装甲剥落，作为场景里的"残骸"焦点
    "mech_torso_wreck": (
        "A single damaged humanoid mech torso, no head no limbs, "
        "torn white and dark steel armor plating, exposed internal frame, "
        "glowing cyan energy conduits, battle damage and scorch marks, "
        "sci-fi robot wreckage"),
    # 断裂机械臂：液压管外露
    "severed_mech_arm": (
        "A single severed robotic mech arm lying as debris, "
        "white armor plates over dark metal joints, exposed hydraulic "
        "pistons and torn cables at the broken shoulder, rust and battle damage, "
        "sci-fi scrapyard"),
    # 废弃机甲头颅：面甲破损、独眼
    "mech_head_wreck": (
        "A single broken mech robot head, cracked white armored faceplate, "
        "one glowing cyan eye sensor, exposed wiring at the neck, "
        "scorched and dented, sci-fi robot skull trophy"),
    # 装甲板碎片堆
    "armor_debris": (
        "A single pile of broken mech armor plate fragments stacked together, "
        "white and grey metal shards with copper inner layers, "
        "jagged torn edges, bolts and rivets, sci-fi battlefield scrap heap"),
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
    seed = 20261112
    for name in ASSETS:
        dest = os.path.join(OUTDIR, "gen_%s.png" % name)
        if os.path.exists(dest) and os.path.getsize(dest) > 10000:
            print("[skip] %s 已存在" % name, flush=True)
            continue
        pid = queue(name, seed)
        seed += 11
        print("[gen] %-20s pid=%s" % (name, pid), flush=True)
        h = wait(pid)
        if not h:
            print("   !! 超时", flush=True)
            continue
        n = fetch(h, dest)
        print("   saved %.0f KB" % (n / 1024), flush=True)
    print("COMFY_MECHWRECK_DONE", flush=True)
