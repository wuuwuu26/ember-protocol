# -*- coding: utf-8 -*-
"""重生成 mech_head_wreck：上一版被理解成人类骷髅，改用明确的"机甲头盔"描述。"""
import json
import urllib.request
import urllib.parse
import time
import os

HOST = "http://127.0.0.1:8188"
OUTDIR = r"C:\AI\Hunyuan3D\input"
NAME = "mech_head_wreck"

PROMPT = (
    "A single detached sci-fi MECH ROBOT HELMET, angular white armored "
    "metal plating with a T-shaped glowing cyan visor slit, side antenna fin, "
    "battle-scarred dented surface and rust streaks, exposed neck coupling "
    "rings and mechanical connectors at the bottom, clearly a machine helmet "
    "NOT a human skull, no bones no teeth no eye sockets, "
    "isolated on plain light grey background, product shot, centered, "
    "entire object visible, photorealistic, high detail, studio lighting, "
    "no text, no people"
)


def api(path, payload=None):
    url = HOST + path
    if payload is None:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=30) as r:
            return json.loads(r.read())
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


wf = {
    "1": {"class_type": "UNETLoader",
          "inputs": {"unet_name": "z_image_turbo_int8_convrot.safetensors",
                     "weight_dtype": "default"}},
    "2": {"class_type": "CLIPLoader",
          "inputs": {"clip_name": "qwen_3_4b_fp8_mixed.safetensors",
                     "type": "lumina2"}},
    "3": {"class_type": "VAELoader",
          "inputs": {"vae_name": "z_image_ae.safetensors"}},
    "4": {"class_type": "CLIPTextEncode",
          "inputs": {"text": PROMPT, "clip": ["2", 0]}},
    "5": {"class_type": "EmptyLatentImage",
          "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
    "6": {"class_type": "KSampler",
          "inputs": {"model": ["1", 0], "positive": ["4", 0],
                     "negative": ["7", 0], "latent_image": ["5", 0],
                     "seed": 777001, "steps": 8, "cfg": 1.0,
                     "sampler_name": "euler", "scheduler": "simple",
                     "denoise": 1.0}},
    "7": {"class_type": "CLIPTextEncode",
          "inputs": {"text": "skull, skeleton, bones, teeth, human, organic, "
                             "blurry, low quality, multiple objects, text, watermark",
                     "clip": ["2", 0]}},
    "8": {"class_type": "VAEDecode",
          "inputs": {"samples": ["6", 0], "vae": ["3", 0]}},
    "9": {"class_type": "SaveImage",
          "inputs": {"images": ["8", 0], "filename_prefix": "hy3d_src_mechhead2"}},
}

pid = api("/prompt", {"prompt": wf}).get("prompt_id")
print("pid", pid, flush=True)
hist = None
t0 = time.time()
while time.time() - t0 < 400:
    h = api("/history/" + pid)
    if pid in h:
        hist = h[pid]
        break
    time.sleep(1.5)

if not hist:
    print("!! 超时")
    raise SystemExit(1)

dest = os.path.join(OUTDIR, "gen_%s.png" % NAME)
for node in hist.get("outputs", {}).values():
    for img in node.get("images", []):
        q = urllib.parse.urlencode({"filename": img["filename"],
                                    "subfolder": img.get("subfolder", ""),
                                    "type": img.get("type", "output")})
        with urllib.request.urlopen(HOST + "/view?" + q, timeout=60) as r:
            data = r.read()
        with open(dest, "wb") as f:
            f.write(data)
        print("saved %s %.0f KB" % (dest, len(data) / 1024), flush=True)
        break
print("HEAD_REGEN_DONE")
