"""The cockpit's panel trim (author 8. 10. 2026: "plastic vibe" - every surface needs SC's engraved panel detail; boxes
of geometry did not get there): one tileable 0.8 x 0.8 m height field of paneling - raised and recessed panels with
chamfered edges, V-seams, hex screws, rivet rows, a louvre band, a small access hatch, fine engraved lines - turned
into a detail normal and a cavity map for the layered master's triplanar detail (DetailTileCm 80).

  T_Kit_PanelDetail_N.png   tangent normal (OpenGL, the importer flips green)
  T_Kit_PanelDetail_C.png   cavity: 1 on the open surface, darker in seams, recesses and round screw heads

    python Tools/Kit/kit_panel_detail.py
"""
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "ArtSource", "Kit", "Textures")
N = 2048
TILE_MM = 800.0
PX = TILE_MM / N                                   # mm per texel

yy, xx = np.meshgrid(np.arange(N) * PX, np.arange(N) * PX, indexing="ij")   # mm, y down the image


def box_sdf(x0, y0, x1, y1):
    """Signed distance (mm) to an axis box, negative inside."""
    cx, cy, hx, hy = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    dx, dy = np.abs(xx - cx) - hx, np.abs(yy - cy) - hy
    out = np.hypot(np.maximum(dx, 0), np.maximum(dy, 0))
    return out + np.minimum(np.maximum(dx, dy), 0)


def plateau(sdf, height, chamfer):
    """A raised (height > 0) or sunk (< 0) flat with a 45-ish chamfer `chamfer` mm wide round its edge."""
    t = np.clip(-sdf / chamfer, 0.0, 1.0)
    return height * t


def groove(sdf, width, depth):
    """A V-groove along the box's outline (the seam between panels)."""
    t = np.clip(1.0 - np.abs(sdf) / (width / 2), 0.0, 1.0)
    return -depth * t


def dome(cx, cy, r, h):
    d = np.hypot(xx - cx, yy - cy)
    t = np.clip(1.0 - (d / r) ** 2, 0.0, 1.0)
    return h * np.sqrt(t)


def hexhead(cx, cy, r, h):
    """A hex screw head: a flat-topped hexagon with a chamfered rim and a hex socket."""
    dx, dy = np.abs(xx - cx), np.abs(yy - cy)
    hexd = np.maximum(dx * 0.866 + dy * 0.5, dy) - r          # flat-topped hexagon distance
    head = h * np.clip(-hexd / 0.8, 0.0, 1.0)
    sock = np.maximum(np.abs(xx - cx) * 0.866 + np.abs(yy - cy) * 0.5, np.abs(yy - cy)) - r * 0.4
    return head - 0.6 * h * np.clip(-sock / 0.4, 0.0, 1.0)


H = np.zeros((N, N), np.float64)
# the panel grid (mm): seams wrap at the tile's edges
panels = [(0, 0, 500, 480), (500, 0, 800, 480), (0, 560, 300, 800), (300, 560, 800, 800)]
for (x0, y0, x1, y1) in panels:
    H += groove(box_sdf(x0, y0, x1, y1), 3.0, 1.2)
# A: a big panel raised 1.2 mm with a 3 mm chamfer, an engraved inner line, screws at its corners
H += plateau(box_sdf(6, 6, 494, 474), 1.2, 3.0)
H += groove(box_sdf(40, 40, 460, 440), 0.9, 0.35)
# B: a recessed bay with a raised hatch in it
H += plateau(box_sdf(8, 8, 792, 472), -1.6, 2.5) * (xx > 500)
H += plateau(box_sdf(560, 100, 740, 380), 2.0, 2.0)
H += groove(box_sdf(575, 115, 725, 365), 0.8, 0.3)
for cx, cy in ((575, 115), (725, 115), (575, 365), (725, 365)):
    H += hexhead(cx, cy, 3.2, 0.9)
# C: the louvre band (y 480 .. 560): slats across the full width, a frame round it
H += plateau(box_sdf(0, 482, 800, 558), -1.0, 1.5)
for k in range(14):
    x0 = 20 + k * 56
    H += plateau(box_sdf(x0, 492, x0 + 36, 548), 1.4, 6.0)
# D: two lower panels - a rivet row along the left one's top, an access hatch with bolts in the right one
H += plateau(box_sdf(6, 566, 294, 794), 0.8, 2.5)
for k in range(15):
    H += dome(20 + k * 18.0, 584, 1.6, 0.6)
H += plateau(box_sdf(306, 566, 794, 794), 0.5, 2.0)
H += plateau(box_sdf(470, 610, 760, 760), -0.9, 1.5)
H += groove(box_sdf(470, 610, 760, 760), 1.0, 0.4)
for cx in (490, 740):
    for cy in (630, 740):
        H += hexhead(cx, cy, 3.0, 0.8)
H += groove(box_sdf(330, 600, 440, 770), 0.7, 0.25)
# screws at the main panels' corners (12 mm in)
for (x0, y0, x1, y1) in panels:
    for cx in (x0 + 14, x1 - 14):
        for cy in (y0 + 14, y1 - 14):
            H += hexhead(cx, cy, 3.4, 0.9)

# normal: slope per texel in mm / texel size
dx = (np.roll(H, -1, 1) - np.roll(H, 1, 1)) / (2 * PX)
dy = (np.roll(H, -1, 0) - np.roll(H, 1, 0)) / (2 * PX)
n = np.dstack((-dx, dy, np.ones_like(H)))       # image y runs down: +dy is the texture's -v
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


# cavity: lower than the neighbourhood -> darker (seams, recess edges, round the screw heads)
local = blur(blur(H, 6), 6)
cav = 1.0 - np.clip((local - H) * 1.6, 0.0, 0.8)
Image.fromarray((cav * 255).clip(0, 255).astype(np.uint8), "L").save(os.path.join(OUT, "T_Kit_PanelDetail_C.png"))
print("PANELDETAIL", OUT, round(float(H.min()), 2), round(float(H.max()), 2), round(float(cav.min()), 2))
