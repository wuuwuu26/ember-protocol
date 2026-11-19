# -*- coding: utf-8 -*-
"""把 -AutoShot 连拍的 14 张截图拼成一张步态对比图。

单张图看不出步态对不对（走路是连续的），必须把"抬腿/落地/换腿"几个
关键姿态并排放在一起看。
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

SRC = r"C:\Users\25227\Documents\robot_game\ue\Saved\Screenshots\WindowsEditor"
OUT = sys.argv[1] if len(sys.argv) > 1 else \
    r"C:\Users\25227\Documents\robot_game\ue\Saved\Screenshots\步态对比.png"

# 裁剪窗口：角色在画面中的位置（1280x720 下大致居中）
#
# 由 -SideCam 的相机几何推出（见 RobotCharacter.cpp 里 -SideCam 那段注释）：
#   相机在水平 400cm、比胶囊中心高 120cm 处俯视 15°，视线落点 Z≈135cm
#   = 机体胸口，也就是**画面正中心**。机体高 250cm，在画面里约占 54% 高度，
#   即 y ∈ [181, 566]、x 以 640 居中。裁一个稍宽的框把整机含进去。
CROP = (380, 180, 900, 560)      # left, top, right, bottom
COLS = 5
SCALE = 1.0

files = sorted(f for f in os.listdir(SRC) if f.lower().endswith(".png"))
if not files:
    print("没有截图")
    sys.exit(1)

try:
    font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 22)
except Exception:
    font = ImageFont.load_default()

tiles = []
for f in files:
    im = Image.open(os.path.join(SRC, f)).convert("RGB")
    im = im.crop(CROP)
    if SCALE != 1.0:
        im = im.resize((int(im.width * SCALE), int(im.height * SCALE)),
                       Image.LANCZOS)
    tiles.append((f, im))

tw, th = tiles[0][1].size
rows = (len(tiles) + COLS - 1) // COLS
LABEL = 30
sheet = Image.new("RGB", (tw * COLS, (th + LABEL) * rows), (18, 18, 20))
d = ImageDraw.Draw(sheet)

for i, (name, im) in enumerate(tiles):
    r, c = divmod(i, COLS)
    x, y = c * tw, r * (th + LABEL)
    sheet.paste(im, (x, y + LABEL))
    d.text((x + 8, y + 3), name.replace("ScreenShot", "#").replace(".png", ""),
           fill=(235, 235, 240), font=font)

sheet.save(OUT)
print("已生成 %s  (%d 张, %dx%d)" % (OUT, len(tiles), sheet.width, sheet.height))
