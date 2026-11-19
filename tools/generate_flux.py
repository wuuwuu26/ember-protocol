# -*- coding: utf-8 -*-
"""
调用本地 FLUX.3 模型生成游戏美术资产
服务端: http://127.0.0.1:7860
模型: FLUX.3 Image Klein (2026旗舰) + 4x-UltraSharp
"""
import os
import sys
import json
import urllib.request

API_URL = "http://127.0.0.1:7860/api/generate"
OUTPUT_DIR = r"C:\AI\EasyAI\outputs"

def generate(prompt, style="product", ratio="1:1", quality="1k", mode="text2image"):
    payload = {
        "mode": mode,
        "prompt": prompt,
        "negative_prompt": "blurry, low quality, cartoon, organic, flesh, messy",
        "style": style,
        "ratio": ratio,
        "model_choice": "flux3",
        "quality_tier": quality,
        "denoise": 0.65
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API_URL, data=data, headers={"Content-Type": "application/json"})
    
    print(f"[FLUX.3] 正在生成: '{prompt[:60]}...' (style={style}, ratio={ratio}, quality={quality})")
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if res.get("success"):
                url = res.get("image_url") or res.get("media_url")
                filename = os.path.basename(url)
                local_path = os.path.join(OUTPUT_DIR, filename)
                print(f"[FLUX.3] 生成成功! 耗时: {res.get('elapsed')}s, 文件: {local_path}")
                return local_path
            else:
                print(f"[FLUX.3] 失败: {res}")
                return None
    except Exception as e:
        print(f"[FLUX.3] 请求异常: {e}")
        return None

if __name__ == "__main__":
    test_prompt = "seamless sci-fi industrial metal floor plate, heavy steel grating, dark titanium hex panel texture, top down view, PBR game texture"
    generate(test_prompt, style="product", ratio="1:1", quality="1k")
