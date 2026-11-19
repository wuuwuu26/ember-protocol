# -*- coding: utf-8 -*-
"""检测截图是否存在"平铺重影"：找使图像与自身平移后几乎相同的最小周期。

做法：对候选周期 p，比较 img[:, :-p] 与 img[:, p:] 的差异。平铺图在 p 处
差异接近 0；正常图差异很大。同时对 y 轴做同样的事。
"""
import sys
import numpy as np
from PIL import Image

for path in sys.argv[1:]:
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.float32)
    h, w, _ = a.shape
    best = []
    for p in range(8, w // 2):
        d = np.abs(a[:, :-p] - a[:, p:]).mean()
        best.append((d, p))
    best.sort()
    bt = best[0]
    bestv = []
    for p in range(8, h // 2):
        d = np.abs(a[:-p] - a[p:]).mean()
        bestv.append((d, p))
    bestv.sort()
    bv = bestv[0]
    print("%-22s x: min_diff=%.2f @p=%d   y: min_diff=%.2f @p=%d"
          % (path.split('\\')[-1], bt[0], bt[1], bv[0], bv[1]))
