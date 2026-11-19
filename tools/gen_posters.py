"""生成场景海报与贴图素材（MOSS-Image：文字排版）。

场景是"余火协议"的废弃工业堆场：生锈钢墙、冷却液池、毒液地、
集装箱堆场、巨型维修机。海报必须是这个世界里真实会有的东西——
安全警示、禁区标识、检修公告、班组通告——而不是科幻电影道具。

所有含文字的图一律用 moss 引擎；纯纹理用 krea2。
"""
import os
import sys

sys.path.insert(0, r"C:\Users\25227\Documents\robot_game\tools")
import easyai

OUT = r"C:\Users\25227\Documents\robot_game\art_src\posters"
os.makedirs(OUT, exist_ok=True)

# (文件名, 提示词, 引擎, 比例)
JOBS = [
    # ── 安全警示（贴墙，最强可读性）──
    ("poster_sector7", (
        'Weathered industrial warning sign bolted to a steel wall, landscape orientation, '
        'rust streaks, scratched enamel surface, grime in the corners. '
        'Large bold stencil text "SECTOR 7" at the top in faded white paint. '
        'Below it a black-and-yellow hazard triangle with an exclamation mark. '
        'Beneath the triangle smaller yellow text "COOLANT LINE - HOT". '
        'Bottom edge has a thin yellow stripe. Soviet-era industrial signage, high contrast, '
        'photographed straight on, flat lighting, no perspective'),
     "moss", "16:9"),

    ("poster_no_entry", (
        'Old enamel safety placard, landscape, off-white with rust freckles and peeling paint edges. '
        'A red diagonal slash over a black gear symbol at the left. '
        'Bold condensed black text "AUTHORIZED PERSONNEL ONLY" across the middle. '
        'Smaller text underneath "MAINTENANCE BAY 4". '
        'A red border stripe runs around the whole plate. '
        'Industrial factory signage, flat front view, slightly dirty, no perspective'),
     "moss", "16:9"),

    ("poster_pressure", (
        'Rugged steel maintenance notice board, landscape, dark grey metal with orange rust bloom. '
        'Top row in worn white stencil letters "PRESSURE TEST". '
        'Center: a white outline schematic of a pipe with three small circles. '
        'Bottom right in yellow text "MAX 1800 kPa". '
        'A strip of yellow-black diagonal hazard tape along the bottom edge. '
        'Industrial engineering signage, flat straight-on view, matte, no perspective'),
     "moss", "16:9"),

    ("poster_shift", (
        'Faded printed paper notice stapled to corrugated steel, landscape, yellowed paper, '
        'water stains, staple marks in the corners, one torn corner. '
        'Header in bold black typewriter letters "NIGHT SHIFT". '
        'Below it three lines of smaller typewriter text "CREW 12 / BAY 3" and "LOG BOOK REQUIRED". '
        'A hand-stamped red oval seal in the lower right corner. '
        'Documentary photo, flat front view, natural light, no perspective'),
     "moss", "16:9"),

    # ── 工业纹理（无文字，用 krea2）──
    ("tex_wall_seamless", (
        'Seamless tileable texture of an old industrial steel wall plate, '
        'painted dark olive-grey with heavy rust bleeding from the bolt holes, '
        'weld seam running vertically, dust and oil stains, '
        'flat orthographic top-down view, even lighting, PBR albedo, no shadows'),
     "krea2", "1:1"),

    ("tex_concrete_seamless", (
        'Seamless tileable texture of cracked industrial concrete, '
        'stained concrete panel, aggregate visible, dark oil patches, '
        'faint formwork board lines, flat orthographic view, even lighting, PBR albedo'),
     "krea2", "1:1"),
]


def main():
    ok = 0
    for name, prompt, engine, ratio in JOBS:
        out = os.path.join(OUT, name + ".png")
        if os.path.exists(out):
            print("[skip] %s" % name)
            ok += 1
            continue
        p = easyai.generate(prompt, out, engine=engine, ratio=ratio,
                            resolution="fast_1k",
                            negative="blurry, unreadable text, gibberish letters, "
                                     "watermark, logo, cartoon, 3d render")
        if p:
            ok += 1
    print("[posters] %d / %d" % (ok, len(JOBS)))


main()
