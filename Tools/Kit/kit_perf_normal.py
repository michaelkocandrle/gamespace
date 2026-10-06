"""The perforated insert's detail normal (Kit_Perforated, decal stack step, author 6. 10. 2026: SC's dark inserts are a
fine regular perforation - Docs/Kit/etalon/decal_stack.md): ArtSource/Kit/Textures/T_Kit_Perf_N.png, 512 x 512,
tileable. Round holes on a staggered (hex) grid, sunk with soft rims, a fine grain over the plate. The layered master
takes it as DetailNormalMap (DetailTileCm per tile).

    python Tools/Kit/kit_perf_normal.py
"""
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "ArtSource", "Kit", "Textures", "T_Kit_Perf_N.png")
N, COLS, STRENGTH = 512, 8, 5.0


def main():
    v, u = np.mgrid[0:N, 0:N].astype(np.float64) / N
    rows = COLS * 2                                       # a staggered grid: every other row shifted half a cell
    fv = v * rows
    iv = np.floor(fv).astype(int)
    fu = u * COLS + np.where(iv % 2 == 0, 0.0, 0.5)
    cu, cv = fu - np.floor(fu) - 0.5, (fv - iv - 0.5) * 0.5   # cells twice as wide as tall -> round holes
    d = np.sqrt(cu ** 2 + cv ** 2) / 0.3                  # 1 at the hole's rim
    h = -np.clip((1.1 - d) / 0.25, 0.0, 1.0)              # sunk holes with a soft rim
    rng = np.random.default_rng(7)
    grain = rng.normal(0.0, 1.0, (N, N))
    grain = (np.roll(grain, 1, 0) + grain + np.roll(grain, 1, 1)) / 3.0
    h = h + 0.02 * grain
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * STRENGTH
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * STRENGTH
    n = np.dstack((-dx, -dy, np.ones_like(h)))
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    img = ((n * 0.5 + 0.5) * 255.0).clip(0, 255).astype(np.uint8)
    Image.fromarray(img, "RGB").save(OUT)
    print("PERF", OUT)


if __name__ == "__main__":
    main()
