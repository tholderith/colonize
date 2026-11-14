"""Title post: downsample the raw render to 1920x1080 (cheap denoise), left-third calm gradient, bloom, vignette, rain streaks, grain-free."""
import os, numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(os.path.dirname(HERE), "public", "assets", "ui")
WORK = os.environ.get("NWORK", "/tmp/colonize_art_work"); os.makedirs(OUT, exist_ok=True)
im = Image.open(os.path.join(WORK, 'title_raw.png')).convert('RGB').resize((1920, 1080), Image.LANCZOS)
a = np.asarray(im).astype('float32') / 255
a = np.stack([gaussian_filter(a[..., c], 0.6) for c in range(3)], -1)                         # light blur removes residual fireflies
hi = np.clip(a - 0.55, 0, 1); a = a + np.stack([gaussian_filter(hi[..., c], 14) for c in range(3)], -1) * 1.1   # bloom
H, W = a.shape[:2]; x = np.linspace(0, 1, W)[None, :]; y = np.linspace(0, 1, H)[:, None]
left = 0.30 + 0.70 * np.clip((x - 0.18) / 0.30, 0, 1) ** 1.3                                   # darker + calmer left third for menu text
vig = 1 - 0.5 * (((x - 0.55) / 0.75) ** 2 + ((y - 0.5) / 0.8) ** 2)
a = a * (left * vig)[..., None]
a[..., 2] += 0.012 * (1 - x)[..., None][..., 0]                                                 # cool tint where the text sits
rng = np.random.default_rng(7); rain = np.zeros((H, W), 'float32')
for _ in range(900):                                                                          # slanted rain streaks
    x0 = rng.integers(0, W + 200); y0 = rng.integers(-100, H); L = rng.integers(30, 90); v = rng.uniform(0.04, 0.12)
    for t in range(L):
        px = int(x0 - t * 0.28); py = y0 + t
        if 0 <= px < W and 0 <= py < H: rain[py, px] += v * (1 - t / L)
rain = gaussian_filter(rain, 0.7) * (0.45 + 0.55 * np.clip((x - 0.1) / 0.4, 0, 1))
a = a + rain[..., None] * np.array([0.6, 0.75, 1.0])
a = np.clip(a, 0, 1)
Image.fromarray((a * 255 + 0.5).astype('uint8')).save(os.path.join(OUT, 'title.png')); print('title written')
