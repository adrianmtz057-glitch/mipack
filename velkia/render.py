"""Renders de control: relieve sombreado cenital, hipsometría y pendientes."""
import numpy as np
from PIL import Image

from .layout import SEA


def hillshade(z, dx, az=315.0, alt=40.0, zf=1.0):
    gy, gx = np.gradient(z.astype(np.float64) * zf, dx)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    a = np.deg2rad(az)
    e = np.deg2rad(alt)
    hs = np.sin(e) * np.cos(slope) + np.cos(e) * np.sin(slope) * np.cos(a - aspect - np.pi / 2)
    return np.clip(hs, 0, 1)


_STOPS = [(-80, (20, 40, 90)), (-20, (40, 80, 150)), (-0.01, (80, 130, 190)), (0, (210, 200, 160)),
          (20, (190, 180, 130)), (60, (170, 150, 100)), (120, (150, 120, 85)), (200, (130, 110, 95)),
          (280, (150, 145, 140)), (350, (215, 215, 220)), (450, (255, 255, 255))]


def hypso_color(h):
    hs = np.array([s[0] for s in _STOPS], np.float32)
    cs = np.array([s[1] for s in _STOPS], np.float32)
    out = np.empty(h.shape + (3,), np.float32)
    for c in range(3):
        out[..., c] = np.interp(h, hs, cs[:, c])
    return out


def relief_image(y, dx, water=None, path=None, colors=None, scale=1):
    """y: cotas absolutas (Y). Devuelve imagen RGB con sombreado."""
    h = y - SEA
    col = hypso_color(h) if colors is None else colors.astype(np.float32)
    hs = hillshade(y, dx)
    shade = 0.35 + 0.85 * hs
    img = col * shade[..., None]
    if water is not None:
        img[water] = img[water] * 0.3 + np.array([40, 90, 200]) * 0.7
    img = np.clip(img, 0, 255).astype(np.uint8)
    im = Image.fromarray(img)
    if scale != 1:
        im = im.resize((im.width // scale, im.height // scale), Image.LANCZOS)
    if path:
        im.save(path)
    return im
