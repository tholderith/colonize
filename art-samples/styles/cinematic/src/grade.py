"""Cinematic colour grade shared by the terrain underlay and every sprite (so the whole world feels like one lit scene).
Operates on linear-ish display RGB 0..1 (post AgX).  Warm highlights, slight teal in the shadows, gentle S-curve."""
import numpy as np

def luma(a): return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722

def grade(a, strength=1.0):
    a = np.clip(a, 0, 1).astype(np.float32)
    l = luma(a)[..., None]
    # split-toning: shadows -> teal, highlights -> warm gold
    sh = np.clip(1 - l * 2.2, 0, 1) ** 1.5
    hi = np.clip((l - 0.45) * 2.0, 0, 1)
    tint_sh = np.array([-0.020, 0.012, 0.030], np.float32)
    tint_hi = np.array([0.040, 0.018, -0.040], np.float32)
    out = a + strength * (sh * tint_sh + hi * tint_hi)
    # saturation lift (slightly stronger in mids)
    l2 = luma(out)[..., None]
    out = l2 + (out - l2) * (1.0 + 0.10 * strength)
    # gentle S curve + warm global gain
    out = np.clip(out, 0, 1)
    out = out * out * (3 - 2 * out) * 0.35 + out * 0.65
    out = out * np.array([1.025, 1.0, 0.965], np.float32)
    # lift blacks a touch with teal
    out = out * 0.975 + np.array([0.008, 0.014, 0.020], np.float32)
    return np.clip(out, 0, 1)

def bloom(a, thr=0.72, sigma=(6, 22), amt=(0.20, 0.26)):
    from scipy import ndimage as ndi
    l = luma(a)
    m = np.clip((l - thr) / (1 - thr), 0, 1)[..., None] * a
    out = a.copy()
    for s, k in zip(sigma, amt):
        b = np.stack([ndi.gaussian_filter(m[..., c], s) for c in range(3)], -1)
        out = out + k * b * np.array([1.0, 0.92, 0.78], np.float32)
    return np.clip(out, 0, 1)
