# -*- coding: utf-8 -*-
"""用 ComfyUI API 生成工业资产概念图（第一百一十轮）。

产出：干净的、单主体的工业设备图（白/灰背景），供 Hunyuan3D 单图转 3D。

模型选择：z_image_turbo（5.78GB，8GB 显存友好）+ z_image_ae VAE
        + qwen_3_4b_fp8_mixed 文本编码器（按 ComfyUI 目录推测的组合）

⚠️ 先跑一张验证链路，成功再批量。
"""
import json
import urllib.request
import time
import os

HOST = "http://127.0.0.1:8188"
OUTDIR = r"C:\AI\Hunyuan3D\input"


def api(path, payload=None):
    url = HOST + path
    if payload is None:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def build_workflow(prompt, seed, w=1024, h=1024, steps=8):
    """z_image_turbo 的 API 工作流（UNETLoader + CLIPLoader + VAELoader + KSampler）。"""
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
              "inputs": {"text": "blurry, low quality, multiple objects, text, watermark",
                         "clip": ["2", 0]}},
        "8": {"class_type": "VAEDecode",
              "inputs": {"samples": ["6", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage",
              "inputs": {"images": ["8", 0], "filename_prefix": "hy3d_src"}},
    }


PROMPTS = {
    "pipe_junction": (
        "A single industrial pipe junction with flanged connectors, weathered dark "
        "steel and rust, sci-fi factory equipment, isolated on plain light grey "
        "background, product shot, centered, full object visible, photorealistic, "
        "high detail, studio lighting, no text"),
    "airlock": (
        "A single heavy industrial airlock door, thick riveted steel frame, hydraulic "
        "pistons, warning stripes, sci-fi facility, isolated on plain light grey "
        "background, product shot, centered, full object visible, photorealistic, "
        "high detail, studio lighting, no text"),
    "crane_arm": (
        "A single abandoned industrial robotic crane arm, rusted orange and steel, "
        "hydraulic joints, sci-fi scrapyard machine, isolated on plain light grey "
        "background, product shot, centered, full object visible, photorealistic, "
        "high detail, studio lighting, no text"),
}


def queue(prompt, prefix, seed):
    wf = build_workflow(prompt, seed)
    # 改输出前缀，便于区分
    wf["9"]["inputs"]["filename_prefix"] = prefix
    res = api("/prompt", {"prompt": wf})
    return res.get("prompt_id")


def wait_done(pid, timeout=300):
    t0 = time.time()
    while time.time() - t0 < timeout:
        h = api("/history/" + pid)
        if pid in h:
            return h[pid]
        time.sleep(2)
    return None


def fetch_image(history, dest):
    outs = history.get("outputs", {})
    for node in outs.values():
        for img in node.get("images", []):
            q = urllib.parse.urlencode({
                "filename": img["filename"],
                "subfolder": img.get("subfolder", ""),
                "type": img.get("type", "output")})
            url = HOST + "/view?" + q
            with urllib.request.urlopen(url, timeout=60) as r:
                data = r.read()
            with open(dest, "wb") as f:
                f.write(data)
            return dest, len(data)
    return None, 0


import urllib.parse

if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    name = "pipe_junction"
    print("[1/3] 提交任务 %s" % name, flush=True)
    pid = queue(PROMPTS[name], "hy3d_src", 12345)
    print("    prompt_id =", pid, flush=True)
    print("[2/3] 等待完成...", flush=True)
    h = wait_done(pid, timeout=420)
    if not h:
        print("!! 超时")
        raise SystemExit(1)
    print("[3/3] 取图", flush=True)
    dest = os.path.join(OUTDIR, "gen_%s.png" % name)
    p, n = fetch_image(h, dest)
    print("    saved %s  %.0f KB" % (p, n / 1024))
    print("COMFY_GEN_DONE")
