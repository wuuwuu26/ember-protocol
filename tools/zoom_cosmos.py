# -*- coding: utf-8 -*-
from PIL import Image
im = Image.open(r"C:\Users\25227\AppData\Local\Temp\opencode\geo_cosmos_v2.png").convert("RGB")
print("size", im.size)
# 左侧箱堆 + 蓝白机甲件 + 白色尖刺
im.crop((120, 280, 470, 500)).resize((1050, 660), Image.Resampling.LANCZOS).save(
    r"C:\Users\25227\AppData\Local\Temp\opencode\cosmos_left_zoom.png")
# 右侧箱堆
im.crop((820, 300, 1180, 520)).resize((1080, 660), Image.Resampling.LANCZOS).save(
    r"C:\Users\25227\AppData\Local\Temp\opencode\cosmos_right_zoom.png")
print("ok")
