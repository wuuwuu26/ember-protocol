"""截取整机画面：用 -ReviewEnemies 之类的固定机位不行，这里直接看侧视连拍里
敌我整体的比例关系。仅用于人工核查姿态。"""
import glob
import sys

from PIL import Image

pat = sys.argv[1]
box = tuple(int(x) for x in sys.argv[2].split(","))
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 4
out = sys.argv[4] if len(sys.argv) > 4 else r"C:\Users\25227\AppData\Local\Temp\opencode\sheet.png"
start = int(sys.argv[5]) if len(sys.argv) > 5 else 0

fs = sorted(glob.glob(pat))
sel = fs[start:start + cols * 2]
if not sel:
    print("no frames")
    raise SystemExit
w = box[2] - box[0]
h = box[3] - box[1]
tw, th = 240, int(240 * h / w)
sheet = Image.new("RGB", (tw * cols, th * 2))
for i, f in enumerate(sel):
    t = Image.open(f).crop(box).resize((tw, th), Image.Resampling.LANCZOS)
    sheet.paste(t, ((i % cols) * tw, (i // cols) * th))
sheet.save(out)
print("ok", len(sel), out)
