"""第二批海报：补充场地其他区域的告示牌。

第一批是"安全/规范"类；这批补"作业/后勤/警示"类，
让场地读起来像真的有人在这里倒班干活。
全部用 moss（图上要出文字）。
"""
import os
import sys

sys.path.insert(0, r"C:\Users\25227\Documents\robot_game\tools")
import easyai

OUT = r"C:\Users\25227\Documents\robot_game\art_src\posters"
os.makedirs(OUT, exist_ok=True)

JOBS = [
    ("poster_highvoltage", (
        'Industrial high voltage warning sign, landscape, dirty yellow enamel plate with '
        'rust streaks and chipped edges. Big black lightning bolt symbol on the left. '
        'Bold black text "HIGH VOLTAGE" across the top, smaller text "415V AC" underneath. '
        'A red border stripe around the plate. Flat front view, straight on, no perspective')),
    ("poster_runoff", (
        'Stencilled metal placard, landscape, dark grey steel with white stencil letters, '
        'paint worn and scratched. Main text "RUNOFF WATER" in large stencil caps, '
        'below it in smaller red letters "DO NOT DRINK". '
        'A simple water-drop icon at the right. Flat front view, straight on, no perspective')),
    ("poster_bay07", (
        'Numbered bay marker plate, landscape, heavy steel plate painted yellow with black '
        'border, numerals "07" punched large in the centre, thin scratches and grime, '
        'two rivets at the corners. Industrial wayfinding signage, flat front view, '
        'straight on, no perspective')),
    ("poster_evac", (
        'Emergency evacuation route sign, landscape, dark green enamel with white graphics, '
        'a running figure arrow pointing right, text "EVACUATION ROUTE" in bold white caps, '
        'small text "ASSEMBLY POINT B" underneath, worn edges and dirt, '
        'flat front view, straight on, no perspective')),
    ("poster_toolcrib", (
        'Workshop tool crib sign, landscape, weathered cream painted board with black serif '
        'lettering "TOOL CRIB", a hanging key symbol below, small text "SIGN OUT REQUIRED", '
        'grease smudges on the corners, flat front view, straight on, no perspective')),
    ("poster_roster", (
        'Shift roster board, landscape, whiteboard with yellowed paper sheets pinned on it, '
        'header printed in black bold "SHIFT ROSTER", below it a printed table grid with '
        'rows of unreadable small type and a few handwritten scribbles in blue marker, '
        'magnets in the corners, flat front view, straight on, no perspective')),
]

ok = 0
for name, prompt in JOBS:
    out = os.path.join(OUT, name + ".png")
    if os.path.exists(out):
        print("[skip] %s" % name)
        ok += 1
        continue
    p = easyai.generate(prompt, out, engine="moss", ratio="16:9",
                        resolution="fast_1k",
                        negative="blurry, unreadable text, gibberish letters, watermark, "
                                 "logo, cartoon, 3d render")
    if p:
        ok += 1
print("[posters2] %d / %d" % (ok, len(JOBS)))
