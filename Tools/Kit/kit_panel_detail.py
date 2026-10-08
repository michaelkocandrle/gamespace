"""The cockpit's panel trim v2 (author 9. 10. 2026: "one uniform white - vary it, layer more on it, SC level: textures,
mesh decals, everything stacked into shapes full of detail, the textures must look real"): one tileable 0.8 x 0.8 m
height field AND tone map of paneling, laid out by a seeded recursive split so no two panels repeat:

  panel kinds   plain raised, recessed bay, louvre band, perforated grille, bolted hatch, label plate (engraved
                "type" rows), double-step panel, rivet-edged skin
  on every one  V-seams round it, hex screws in its corners, fine engraved lines, fastener rows on some edges
  tone          each panel its own shade of the paint (+-5 %), ~1 in 6 in the secondary grey paint, ~1 in 12 a
                graphite insert, label plates and stencil marks darker - the cavity map multiplies the base colour,
                so this variation shows on every surface in the panel paint

  T_Kit_PanelDetail_N.png   tangent normal (OpenGL, the importer flips green)
  T_Kit_PanelDetail_C.png   tone x cavity: 1 on bright open paint, darker in seams, recesses, round screw heads,
                            on the grey and graphite panels and the printed marks

    python Tools/Kit/kit_panel_detail.py
"""
import os
import random

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "ArtSource", "Kit", "Textures")
N = 2048
TILE_MM = 800.0
PX = TILE_MM / N                                   # mm per texel
SEED = 20261009

yy, xx = np.meshgrid(np.arange(N) * PX, np.arange(N) * PX, indexing="ij")   # mm, y down the image


def box_sdf(x0, y0, x1, y1):
    """Signed distance (mm) to an axis box, negative inside."""
    cx, cy, hx, hy = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    dx, dy = np.abs(xx - cx) - hx, np.abs(yy - cy) - hy
    out = np.hypot(np.maximum(dx, 0), np.maximum(dy, 0))
    return out + np.minimum(np.maximum(dx, dy), 0)


def window(x0, y0, x1, y1, pad=4.0):
    """Index slices of the texels near a box (speed: most features are small)."""
    i0, i1 = max(0, int((y0 - pad) / PX)), min(N, int((y1 + pad) / PX) + 1)
    j0, j1 = max(0, int((x0 - pad) / PX)), min(N, int((x1 + pad) / PX) + 1)
    return slice(i0, i1), slice(j0, j1)


def add_box(H, x0, y0, x1, y1, fn):
    s = window(x0, y0, x1, y1)
    cx, cy, hx, hy = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    dx, dy = np.abs(xx[s] - cx) - hx, np.abs(yy[s] - cy) - hy
    sdf = np.hypot(np.maximum(dx, 0), np.maximum(dy, 0)) + np.minimum(np.maximum(dx, dy), 0)
    H[s] += fn(sdf)


def plateau(height, chamfer):
    return lambda sdf: height * np.clip(-sdf / chamfer, 0.0, 1.0)


def groove(width, depth):
    return lambda sdf: -depth * np.clip(1.0 - np.abs(sdf) / (width / 2), 0.0, 1.0)


def hexhead(H, cx, cy, r, h):
    s = window(cx - r, cy - r, cx + r, cy + r)
    dx, dy = np.abs(xx[s] - cx), np.abs(yy[s] - cy)
    hexd = np.maximum(dx * 0.866 + dy * 0.5, dy) - r
    sock = np.maximum(dx * 0.866 + dy * 0.5, dy) - r * 0.4
    H[s] += h * np.clip(-hexd / 0.8, 0.0, 1.0) - 0.6 * h * np.clip(-sock / 0.4, 0.0, 1.0)


def dome(H, cx, cy, r, h):
    s = window(cx - r, cy - r, cx + r, cy + r)
    d = np.hypot(xx[s] - cx, yy[s] - cy)
    H[s] += h * np.sqrt(np.clip(1.0 - (d / r) ** 2, 0.0, 1.0))


def hole(H, cx, cy, r, depth):
    s = window(cx - r, cy - r, cx + r, cy + r)
    d = np.hypot(xx[s] - cx, yy[s] - cy)
    H[s] -= depth * np.clip((r - d) / 0.5, 0.0, 1.0)


def set_tone(T, x0, y0, x1, y1, v):
    s = window(x0, y0, x1, y1, pad=0.0)
    inside = (xx[s] >= x0) & (xx[s] <= x1) & (yy[s] >= y0) & (yy[s] <= y1)
    T[s] = np.where(inside, v, T[s])


def split(rng, rect, out, depth=0):
    x0, y0, x1, y1 = rect
    w, h = x1 - x0, y1 - y0
    if (max(w, h) < rng.uniform(130, 260) and depth > 1) or min(w, h) < 70:
        out.append(rect)
        return
    if w >= h:
        cut = x0 + w * rng.uniform(0.3, 0.7)
        split(rng, (x0, y0, cut, y1), out, depth + 1)
        split(rng, (cut, y0, x1, y1), out, depth + 1)
    else:
        cut = y0 + h * rng.uniform(0.3, 0.7)
        split(rng, (x0, y0, x1, cut), out, depth + 1)
        split(rng, (x0, cut, x1, y1), out, depth + 1)


def type_rows(H, T, rng, x0, y0, x1, rows, size):
    """Printed / engraved 'type': rows of small blocks like stencilled text, darker in tone, a hair recessed."""
    y = y0
    for _ in range(rows):
        x = x0
        while x < x1 - size:
            gw = size * rng.choice((0.5, 0.6, 0.6, 0.8, 1.0))
            if rng.random() < 0.85:
                add_box(H, x, y, x + gw, y + size, plateau(-0.12, 0.2))
                set_tone(T, x, y, x + gw, y + size, 0.55)
            x += gw + size * (0.35 if rng.random() < 0.8 else 1.4)
        y += size * 1.8


def main():
    rng = random.Random(SEED)
    H = np.zeros((N, N), np.float64)
    T = np.ones((N, N), np.float64)
    panels = []
    split(rng, (0.0, 0.0, TILE_MM, TILE_MM), panels)
    kinds = ["plain", "plain", "recess", "louvre", "grille", "hatch", "label", "step", "rivets", "plain"]
    for (x0, y0, x1, y1) in panels:
        w, h = x1 - x0, y1 - y0
        kind = rng.choice(kinds)
        # tone: the paint's own shade, the secondary grey, a graphite insert
        roll = rng.random()
        tone = 0.44 if roll < 0.06 else (0.82 if roll < 0.2 else rng.uniform(0.95, 1.0))
        set_tone(T, x0, y0, x1, y1, tone)
        add_box(H, x0, y0, x1, y1, groove(3.0, 1.2))                     # the seam round it
        m = 6.0
        if kind == "recess":
            add_box(H, x0 + m, y0 + m, x1 - m, y1 - m, plateau(-1.6, 2.5))
            add_box(H, x0 + 2 * m + 6, y0 + 2 * m + 6, x1 - 2 * m - 6, y1 - 2 * m - 6, plateau(1.2, 2.0))
            add_box(H, x0 + 2 * m + 14, y0 + 2 * m + 14, x1 - 2 * m - 14, y1 - 2 * m - 14, groove(0.8, 0.3))
        elif kind == "louvre":
            add_box(H, x0 + m, y0 + m, x1 - m, y1 - m, plateau(-1.0, 1.5))
            set_tone(T, x0 + m, y0 + m, x1 - m, y1 - m, min(tone, 0.72))
            n = int((w - 2 * m - 20) / 22)
            for k in range(max(n, 1)):
                sx = x0 + m + 12 + k * 22
                add_box(H, sx, y0 + m + 10, sx + 12, y1 - m - 10, plateau(1.4, 4.0))
        elif kind == "grille":
            add_box(H, x0 + m, y0 + m, x1 - m, y1 - m, plateau(0.6, 1.5))
            gx0, gy0, gx1, gy1 = x0 + m + 14, y0 + m + 14, x1 - m - 14, y1 - m - 14
            add_box(H, gx0 - 3, gy0 - 3, gx1 + 3, gy1 + 3, groove(0.9, 0.35))
            cy = gy0 + 3
            while cy < gy1 - 2:
                cx = gx0 + 3
                while cx < gx1 - 2:
                    hole(H, cx, cy, 1.6, 1.2)
                    cx += 6.5
                cy += 6.5
            set_tone(T, gx0, gy0, gx1, gy1, min(tone, 0.82))
        elif kind == "hatch":
            add_box(H, x0 + m, y0 + m, x1 - m, y1 - m, plateau(0.8, 2.5))
            hx0, hy0 = x0 + w * 0.2, y0 + h * 0.2
            hx1, hy1 = x1 - w * 0.2, y1 - h * 0.2
            add_box(H, hx0, hy0, hx1, hy1, groove(1.2, 0.5))
            add_box(H, hx0 + 4, hy0 + 4, hx1 - 4, hy1 - 4, plateau(0.6, 1.5))
            for cx in (hx0 + 9, hx1 - 9):
                for cy in (hy0 + 9, hy1 - 9):
                    hexhead(H, cx, cy, 3.0, 0.8)
            add_box(H, (hx0 + hx1) / 2 - 14, hy1 - 22, (hx0 + hx1) / 2 + 14, hy1 - 14, plateau(-0.8, 1.0))   # the pull
        elif kind == "label":
            add_box(H, x0 + m, y0 + m, x1 - m, y1 - m, plateau(0.8, 2.5))
            lx0, ly0 = x0 + m + 16, y0 + m + 16
            lx1, ly1 = min(x1 - m - 16, lx0 + rng.uniform(70, 150)), ly0 + rng.uniform(26, 44)
            add_box(H, lx0, ly0, lx1, ly1, plateau(0.5, 0.6))
            set_tone(T, lx0, ly0, lx1, ly1, 0.9)
            type_rows(H, T, rng, lx0 + 4, ly0 + 5, lx1 - 4, 2, 4.0)
            for cx in (lx0 + 3, lx1 - 3):
                dome(H, cx, (ly0 + ly1) / 2, 1.2, 0.4)
            type_rows(H, T, rng, x0 + m + 16, ly1 + 10, x1 - m - 30, 1, 6.0)    # a stencil line under it
        elif kind == "step":
            add_box(H, x0 + m, y0 + m, x1 - m, y1 - m, plateau(1.0, 2.5))
            add_box(H, x0 + 2.5 * m, y0 + 2.5 * m, x1 - 2.5 * m, y1 - 2.5 * m, plateau(0.9, 2.0))
            add_box(H, x0 + 2.5 * m + 8, y0 + 2.5 * m + 8, x1 - 2.5 * m - 8, y1 - 2.5 * m - 8, groove(0.7, 0.25))
        elif kind == "rivets":
            add_box(H, x0 + m, y0 + m, x1 - m, y1 - m, plateau(0.7, 2.0))
            for k in range(int((w - 30) / 16)):
                dome(H, x0 + 15 + k * 16, y0 + 14, 1.6, 0.6)
                dome(H, x0 + 15 + k * 16, y1 - 14, 1.6, 0.6)
        else:
            add_box(H, x0 + m, y0 + m, x1 - m, y1 - m, plateau(1.0, 3.0))
            add_box(H, x0 + m + 30, y0 + m + 30, x1 - m - 30, y1 - m - 30, groove(0.9, 0.35))
            if rng.random() < 0.5:
                type_rows(H, T, rng, x0 + m + 12, y1 - m - 22, x0 + m + 12 + min(120, w * 0.5), 1, 5.0)
        # screws in the corners of most panels, a fastener row along a long edge of some
        if kind not in ("hatch",) and rng.random() < 0.8:
            for cx in (x0 + 13, x1 - 13):
                for cy in (y0 + 13, y1 - 13):
                    hexhead(H, cx, cy, 3.2, 0.9)
        if rng.random() < 0.3 and w > 160:
            for k in range(int((w - 60) / 40)):
                hexhead(H, x0 + 40 + k * 40, y0 + 13, 2.6, 0.7)
    # engraved hairlines across a few panels (service routing marks)
    for _ in range(10):
        x0, y0, x1, y1 = rng.choice(panels)
        if rng.random() < 0.5:
            yv = rng.uniform(y0 + 20, y1 - 20)
            add_box(H, x0 + 18, yv - 0.3, x1 - 18, yv + 0.3, groove(0.6, 0.2))
        else:
            xv = rng.uniform(x0 + 20, x1 - 20)
            add_box(H, xv - 0.3, y0 + 18, xv + 0.3, y1 - 18, groove(0.6, 0.2))

    dx = (np.roll(H, -1, 1) - np.roll(H, 1, 1)) / (2 * PX)
    dy = (np.roll(H, -1, 0) - np.roll(H, 1, 0)) / (2 * PX)
    n = np.dstack((-dx, dy, np.ones_like(H)))
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    Image.fromarray(((n * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8), "RGB").save(os.path.join(OUT, "T_Kit_PanelDetail_N.png"))

    def blur(a, r):
        out = a.copy()
        for axis in (0, 1):
            acc = np.zeros_like(out)
            for k in range(-r, r + 1):
                acc += np.roll(out, k, axis)
            out = acc / (2 * r + 1)
        return out
    local = blur(blur(H, 6), 6)
    cav = 1.0 - np.clip((local - H) * 1.6, 0.0, 0.8)
    C = np.clip(cav * T, 0.0, 1.0)
    Image.fromarray((C * 255).clip(0, 255).astype(np.uint8), "L").save(os.path.join(OUT, "T_Kit_PanelDetail_C.png"))
    print("PANELDETAIL v2", OUT, "panels", len(panels), round(float(H.min()), 2), round(float(H.max()), 2), round(float(C.mean()), 3))


if __name__ == "__main__":
    main()
