"""Micro-surface normals for new factory paint and graphite (author 8. 10. 2026: the parts are brand new - no wear; the
critic read the console as one flat matte grey CG paint): tileable 1024 x 1024 detail normals for the layered master's
DetailNormalMap (triplanar in local space, DetailTileCm per tile).

  T_Kit_OrangePeel_N.png  a sprayed paint's orange peel: soft round bumps a few mm across, under a clear coat
  T_Kit_Grain_N.png       a powder-coated graphite: a fine sandy grain

    python Tools/Kit/kit_paint_normals.py
"""
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "ArtSource", "Kit", "Textures")
N = 1024


def _blur(h, r):
    """A box blur r texels wide, wrapped (tileable)."""
    out = h.copy()
    for axis in (0, 1):
        acc = np.zeros_like(out)
        for k in range(-r, r + 1):
            acc += np.roll(out, k, axis)
        out = acc / (2 * r + 1)
    return out


def _normal(h, strength):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * strength
    n = np.dstack((-dx, -dy, np.ones_like(h)))
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return ((n * 0.5 + 0.5) * 255.0).clip(0, 255).astype(np.uint8)


def main():
    rng = np.random.default_rng(11)
    # orange peel: two octaves of blurred noise, the bumps ~ 1/40 of the tile (a 15 cm tile: ~4 mm)
    peel = _blur(rng.normal(0, 1, (N, N)), 10) * 1.0 + _blur(rng.normal(0, 1, (N, N)), 4) * 0.35
    peel /= np.abs(peel).max()
    Image.fromarray(_normal(peel, 40.0), "RGB").save(os.path.join(OUT, "T_Kit_OrangePeel_N.png"))
    # grain: fine sandy noise with a little clustering
    grain = _blur(rng.normal(0, 1, (N, N)), 1) + 0.4 * _blur(rng.normal(0, 1, (N, N)), 3)
    grain /= np.abs(grain).max()
    Image.fromarray(_normal(grain, 6.0), "RGB").save(os.path.join(OUT, "T_Kit_Grain_N.png"))
    print("PAINTNORMALS", OUT)


if __name__ == "__main__":
    main()
