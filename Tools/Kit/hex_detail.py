"""Hex texture for the dark zones of a ship's hull (SC exterior technique 7, measured 10. 10. 2026 on the Avenger
belly: a dark coating in hex cells ~20 cm across, satin). Grooves 5 mm wide and 1 mm deep with a soft shoulder and a
cell tone of 0.8-1: 1.5 mm x 0.3 mm grooves fell under a pixel from the chase camera and nothing showed on the 0.04
base.

    python Tools/Kit/hex_detail.py

Writes ArtSource/Kit/Textures/T_Ship_HexDetail_N.png (tangent normal, OpenGL like kit_panel_detail.py) and
T_Ship_HexDetail_C.png (tone x cavity). One tile holds 7 x 8 pointy-top hexes so it repeats seamlessly; with
DetailTileCm 120 a cell is 17 cm across the flats.
"""
import math
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "ArtSource", "Kit", "Textures")
N = 2048
COLS, ROWS = 7, 8                  # ROWS even: the offset rows repeat across the tile edge
TILE_MM = 1200.0
S = TILE_MM / (COLS * math.sqrt(3))  # hex radius (centre to corner), mm
GROOVE_MM = 5.0
DEPTH_MM = 1.0
SEED = 20261010


def main():
    px = TILE_MM / N
    yy, xx = np.meshgrid(np.arange(N) * px, np.arange(N) * px, indexing="ij")
    # the rows are 1.5 S apart; stretch y a hair so ROWS rows fill the tile (12 S vs 12.12 S across: 1 %)
    sy = TILE_MM / (ROWS * 1.5 * S)
    y = yy / sy
    w = math.sqrt(3) * S
    best = np.full(xx.shape, 1e9)
    cell = np.zeros(xx.shape, dtype=np.int64)
    j0 = np.floor(y / (1.5 * S)).astype(np.int64)
    for dj in (-1, 0, 1):
        j = j0 + dj
        off = (j % 2) * (w / 2)
        i0 = np.floor((xx - off) / w).astype(np.int64)
        for di in (0, 1):
            i = i0 + di
            cx = i * w + off
            cy = j * 1.5 * S
            px_, py_ = xx - cx, y - cy
            d = np.maximum.reduce([np.abs(px_) , np.abs(px_ * 0.5 + py_ * math.sqrt(3) / 2),
                                   np.abs(px_ * 0.5 - py_ * math.sqrt(3) / 2)])
            closer = d < best
            best = np.where(closer, d, best)
            cell = np.where(closer, (i % COLS) * 97 + (j % ROWS) * 13, cell)
    edge = w / 2 - best                                 # mm to the cell's edge (apothem w / 2)
    H = -DEPTH_MM * np.clip(1.0 - (edge - GROOVE_MM / 2) / 2.0, 0.0, 1.0)   # groove with a 2 mm soft shoulder
    dx = (np.roll(H, -1, 1) - np.roll(H, 1, 1)) / (2 * px)
    dy = (np.roll(H, -1, 0) - np.roll(H, 1, 0)) / (2 * px)
    n = np.dstack((-dx, dy, np.ones_like(H)))
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray(((n * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8), "RGB").save(
        os.path.join(OUT, "T_Ship_HexDetail_N.png"))
    rng = np.random.default_rng(SEED)
    tone = rng.uniform(0.8, 1.0, COLS * 97 + ROWS * 13 + 1)[cell]
    cav = 1.0 - 0.55 * np.clip(-H / DEPTH_MM, 0.0, 1.0)
    C = np.clip(cav * tone, 0.0, 1.0)
    Image.fromarray((C * 255).astype(np.uint8), "L").save(os.path.join(OUT, "T_Ship_HexDetail_C.png"))
    print("HEXDETAIL", OUT, "cell across flats %.0f mm" % w, "C mean %.3f" % float(C.mean()))


if __name__ == "__main__":
    main()
