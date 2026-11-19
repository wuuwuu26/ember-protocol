import numpy as np, glob
from PIL import Image

for f in sorted(glob.glob(r'ue/Saved/Screenshots/WindowsEditor/*.png')):
    a = np.asarray(Image.open(f).convert('RGB')).astype(np.float32) / 255.0
    sky = a[0:420, :, :]
    lum = sky @ np.array([0.2126, 0.7152, 0.0722])
    print(f.split('\\')[-1],
          'sky_mean', round(float(lum.mean()), 4),
          'sky_max', round(float(lum.max()), 3),
          'p99', round(float(np.percentile(lum, 99)), 3),
          'bright_px', int((lum > 0.35).sum()),
          'hot_px', int((lum > 0.55).sum()))
