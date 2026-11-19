"""
截图统计 —— 给"光影/调色"提供客观依据，而不是靠肉眼猜。

为什么需要：调色时人眼只能判断"好像亮了一点"，但判断不了：
  · 高光是不是过曝了（p99 贴着 1.0 就说明洗白了）
  · 暗部是不是死黑（p01 贴 0 就说明细节全丢）
  · 色相是不是偏了（R/B 比值）
这三件事各自都要连续迭代十几次，眼睛会习惯、会骗自己。

用法：
    python tools/shot_stats.py <图片或目录> [更多...]
    python tools/shot_stats.py ue/Saved/Screenshots/WindowsEditor --mask-hud

输出每张图一行：
    mean/p01/p05/p50/p95/p99   —— 亮度分位数（0~1）
    clip                       —— 过曝像素占比（>0.98）
    crush                      —— 死黑像素占比（<0.02）
    R/B                        —— 红蓝比（1.0 = 中性；>1.1 偏暖，<0.9 偏冷）
    sky                        —— 画面上 1/3 的平均色（看天空是否发灰/发暖）

--mask-hud 会跳过左下角 HUD 面板区域（那里是固定亮度的 UI，会污染统计）。
"""
import os
import sys

try:
    from PIL import Image
except ImportError:
    print("需要 Pillow：pip install pillow")
    sys.exit(1)


def stats(path, mask_hud=False):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()

    # 采样步长：1600x900 全量统计要 ~0.5 秒/张，采样 4 像素一次够用
    step = max(1, w // 400)
    lums = []
    r_sum = g_sum = b_sum = 0
    n = 0
    clip = crush = 0
    sky_r = sky_g = sky_b = sky_n = 0

    for y in range(0, h, step):
        for x in range(0, w, step):
            if mask_hud and x < w * 0.32 and y > h * 0.62:
                continue
            r, g, b = px[x, y]
            lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
            lums.append(lum)
            r_sum += r
            g_sum += g
            b_sum += b
            n += 1
            if lum > 0.98:
                clip += 1
            elif lum < 0.02:
                crush += 1
            if y < h / 3:
                sky_r += r
                sky_g += g
                sky_b += b
                sky_n += 1

    if n == 0:
        return None
    lums.sort()

    def q(p):
        return lums[min(len(lums) - 1, int(len(lums) * p))]

    mean = sum(lums) / len(lums)
    rb = (r_sum / max(b_sum, 1))
    sky = (sky_r / max(sky_n, 1), sky_g / max(sky_n, 1), sky_b / max(sky_n, 1))
    return {
        "mean": mean,
        "p01": q(0.01),
        "p05": q(0.05),
        "p50": q(0.50),
        "p95": q(0.95),
        "p99": q(0.99),
        "clip": clip / n,
        "crush": crush / n,
        "rb": rb,
        "sky": sky,
    }


def fmt(name, s):
    return ("%-34s mean=%.3f p01=%.3f p05=%.3f p50=%.3f p99=%.3f "
            "clip=%4.1f%% crush=%4.1f%% R/B=%.2f sky=(%.0f,%.0f,%.0f)"
            % (name, s["mean"], s["p01"], s["p05"], s["p50"], s["p99"],
               s["clip"] * 100, s["crush"] * 100, s["rb"],
               s["sky"][0], s["sky"][1], s["sky"][2]))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    mask = "--mask-hud" in sys.argv
    if not args:
        print(__doc__)
        return

    paths = []
    for a in args:
        if os.path.isdir(a):
            for f in sorted(os.listdir(a)):
                if f.lower().endswith(".png") and f.startswith("ScreenShot"):
                    paths.append(os.path.join(a, f))
        else:
            paths.append(a)

    for p in paths:
        try:
            s = stats(p, mask)
        except Exception as e:
            print("%-34s ERROR %s" % (os.path.basename(p), str(e)[:60]))
            continue
        if s:
            print(fmt(os.path.basename(p), s))


if __name__ == "__main__":
    main()
