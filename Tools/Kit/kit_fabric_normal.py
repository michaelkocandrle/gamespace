"""A woven fabric's detail normal for the kit's upholstery (Kit_Cushion, 30. 9. 2026: the cabin's critic, rounds 1-2 -
"smooth vinyl"): ArtSource/Kit/Textures/T_Kit_Fabric_N.png, 512 x 512, tileable. A plain weave: warp and weft threads
over and under by turns, each a rounded ridge, a fine fibre noise over it. The layered master takes it as
DetailNormalMap (triplanar in local space, DetailTileCm per tile).

    python Tools/Kit/kit_fabric_normal.py
"""
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "ArtSource", "Kit", "Textures", "T_Kit_Fabric_N.png")
N, THREADS, STRENGTH = 512, 16, 3.0


def main():
    v, u = np.mgrid[0:N, 0:N].astype(np.float64) / N * THREADS        # thread coordinates
    iu, iv = np.floor(u).astype(int), np.floor(v).astype(int)
    fu, fv = u - iu, v - iv
    over_warp = (iu + iv) % 2 == 0                                    # the warp (along v) over the weft here
    ridge_u = np.cos((fu - 0.5) * np.pi) ** 0.7                       # a warp thread's round, across it
    ridge_v = np.cos((fv - 0.5) * np.pi) ** 0.7                       # a weft thread's round
    # the thread on top at full height, dipping at the cell's ends where it goes under
    dip_v = 0.65 + 0.35 * np.sin(fv * np.pi)
    dip_u = 0.65 + 0.35 * np.sin(fu * np.pi)
    # the fibres: three strands along each thread (the plain rounded ridge read as tiles)
    h = np.where(over_warp, ridge_u * dip_v + 0.18 * np.sin(fu * 6 * np.pi) ** 2, ridge_v * dip_u + 0.18 * np.sin(fv * 6 * np.pi) ** 2)
    rng = np.random.default_rng(7)
    fibre = rng.normal(0.0, 1.0, (N, N))
    fibre = (np.roll(fibre, 1, 0) + fibre + np.roll(fibre, 1, 1)) / 3.0
    h = h + 0.04 * fibre
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * STRENGTH
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * STRENGTH
    n = np.dstack((-dx, -dy, np.ones_like(h)))
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    img = ((n * 0.5 + 0.5) * 255.0).clip(0, 255).astype(np.uint8)
    Image.fromarray(img, "RGB").save(OUT)
    print("FABRIC", OUT)


if __name__ == "__main__":
    main()
