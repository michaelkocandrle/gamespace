"""The anti-slip tread's detail normal for the factory floor (Kit_AntiSlip, parts factory pilot 1, 6. 10. 2026: the author
wants today's kit floor pattern back in the lanes, at half its contrast): ArtSource/Kit/Textures/T_Kit_Tread_N.png,
512 x 512, tileable. Raised lozenges in alternating directions (a tread plate's pattern), with soft shoulders, a fine
grain over it. The layered master takes it as DetailNormalMap (triplanar in local space, DetailTileCm per tile).

    python Tools/Kit/kit_tread_normal.py
"""
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "ArtSource", "Kit", "Textures", "T_Kit_Tread_N.png")
N, CELLS, STRENGTH = 512, 4, 4.0


def lozenge(fu, fv, angle):
    """Height of one raised lozenge (long 0.7 x short 0.18 of the cell) rotated by angle, rounded shoulders."""
    c, s = np.cos(angle), np.sin(angle)
    x, y = (fu - 0.5) * c + (fv - 0.5) * s, -(fu - 0.5) * s + (fv - 0.5) * c
    d = np.abs(x) / 0.35 + np.abs(y) / 0.09            # 1 at the lozenge's outline
    return np.clip((1.15 - d) / 0.3, 0.0, 1.0) ** 0.8


def main():
    v, u = np.mgrid[0:N, 0:N].astype(np.float64) / N * CELLS
    iu, iv = np.floor(u).astype(int), np.floor(v).astype(int)
    fu, fv = u - iu, v - iv
    alt = (iu + iv) % 2 == 0                               # neighbouring cells turn the other way
    h = np.where(alt, lozenge(fu, fv, np.radians(45.0)), lozenge(fu, fv, np.radians(-45.0)))
    rng = np.random.default_rng(11)
    grain = rng.normal(0.0, 1.0, (N, N))
    grain = (np.roll(grain, 1, 0) + grain + np.roll(grain, 1, 1)) / 3.0
    h = h + 0.03 * grain
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * STRENGTH
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * STRENGTH
    n = np.dstack((-dx, -dy, np.ones_like(h)))
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    img = ((n * 0.5 + 0.5) * 255.0).clip(0, 255).astype(np.uint8)
    Image.fromarray(img, "RGB").save(OUT)
    print("TREAD", OUT)


if __name__ == "__main__":
    main()
