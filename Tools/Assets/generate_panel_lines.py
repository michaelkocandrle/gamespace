"""A tiling sheet of panel seams for the hull material, as T_Ship_Panels.png.

    python Tools/Assets/generate_panel_lines.py

    R, G  the seam's normal, x and y (z is rebuilt in the shader, so one texture is one sample)
    B     the seam itself, 1 in the groove and 0 on the plate: the material darkens and roughens it

Why generated and tiling rather than painted into the ship's atlas: the atlas is thousands of tiny
islands from smart_project (Docs/Ships/ShipPipeline.md), so a line drawn across it would break at
every island edge. M_Ship_PBR projects this triplanar in the ship's own space instead, the same way
the micro detail is projected (generate_detail_textures.py), so the seams keep their size in
centimetres and do not swim when the ship moves.

The layout is plates, not a grid: full-width and full-height cuts make the sheet tile, and a second
cut inside some of the plates breaks the regularity up. Rivets sit along part of the seams.
"""

import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "ArtSource", "Ships", "Shared", "Textures", "T_Ship_Panels.png")

SIZE = 1024
SEAM_PX = 12          # how wide a groove is drawn before blurring. At a 180 cm tile one pixel is
                      # 1.8 mm, so this is a ~2 cm groove: thinner and the mip chain eats it before
                      # the camera is close enough to see it at all (20. 9. 2026).
GROOVE_BLUR = 2.5     # softens the groove's walls; a hard step reads as aliasing in the game
NORMAL_STRENGTH = 5.0
RIVET_RADIUS = 5
RIVET_SPACING = 62
MIN_PLATE = 110       # no plate narrower than this, so the sheet does not turn into a grid of squares
SEED = 11


def cuts(rng, length, count):
    """count cut positions, never closer than MIN_PLATE to each other or to the edge."""
    chosen = []
    for _ in range(600):
        if len(chosen) >= count:
            break
        x = int(rng.integers(MIN_PLATE, length - MIN_PLATE))
        if all(abs(x - c) >= MIN_PLATE for c in chosen):
            chosen.append(x)
    return sorted(chosen)


def draw(rng):
    """The groove depth, 1 in a seam and 0 on a plate, as a tiling image.

    Three cuts each way go all the way across - those are what make the sheet tile - and then every
    plate is split again, and sometimes a third time, with thinner seams. Cuts that all run the full
    width turn the sheet into wallpaper; the splits are what stop it (20. 9. 2026).
    """
    image = Image.new("L", (SIZE, SIZE), 0)
    pen = ImageDraw.Draw(image)

    def cut(x0, y0, x1, y1, width):
        half = max(width // 2, 1)
        if x1 - x0 > y1 - y0:                      # a horizontal seam
            middle = (y0 + y1) // 2
            pen.rectangle((x0, middle - half, x1, middle + half), fill=255)
            return (x0, y0, x1, middle), (x0, middle, x1, y1)
        middle = (x0 + x1) // 2
        pen.rectangle((middle - half, y0, middle + half, y1), fill=255)
        return (x0, y0, middle, y1), (middle, y0, x1, y1)

    columns = cuts(rng, SIZE, 3)
    rows = cuts(rng, SIZE, 3)
    half = SEAM_PX // 2
    for x in columns:
        pen.rectangle((x - half, 0, x + half, SIZE), fill=255)
    for y in rows:
        pen.rectangle((0, y - half, SIZE, y + half), fill=255)

    # Split each plate, and sometimes one of its halves again. These seams stay inside the plate, so
    # they never reach the sheet's edge and the tiling still holds.
    bounds_x = [0] + columns + [SIZE]
    bounds_y = [0] + rows + [SIZE]
    for i in range(len(bounds_x) - 1):
        for j in range(len(bounds_y) - 1):
            plate = (bounds_x[i] + half, bounds_y[j] + half, bounds_x[i + 1] - half, bounds_y[j + 1] - half)
            if min(plate[2] - plate[0], plate[3] - plate[1]) < MIN_PLATE or rng.random() < 0.25:
                continue
            for part in cut(*plate, width=SEAM_PX - 4):
                if min(part[2] - part[0], part[3] - part[1]) >= MIN_PLATE and rng.random() < 0.5:
                    cut(*part, width=SEAM_PX - 6)
    return image, columns, rows


def rivets(image, rng, columns, rows):
    """Bolt heads in a row beside some of the through cuts: a plate is bolted down, not glued."""
    pen = ImageDraw.Draw(image)
    offset = SEAM_PX // 2 + RIVET_RADIUS + 3
    for x in columns:
        if rng.random() < 0.4:
            continue
        side = offset if rng.random() < 0.5 else -offset
        for y in range(RIVET_SPACING // 2, SIZE, RIVET_SPACING):
            pen.ellipse((x + side - RIVET_RADIUS, y - RIVET_RADIUS, x + side + RIVET_RADIUS, y + RIVET_RADIUS), fill=200)
    for y in rows:
        if rng.random() < 0.4:
            continue
        side = offset if rng.random() < 0.5 else -offset
        for x in range(RIVET_SPACING // 2, SIZE, RIVET_SPACING):
            pen.ellipse((x - RIVET_RADIUS, y + side - RIVET_RADIUS, x + RIVET_RADIUS, y + side + RIVET_RADIUS), fill=200)
    return image


def normal_xy(depth):
    """The slope of the groove's walls. Gradients wrap, because the sheet has to tile."""
    dx = np.roll(depth, -1, axis=1) - np.roll(depth, 1, axis=1)
    dy = np.roll(depth, -1, axis=0) - np.roll(depth, 1, axis=0)
    # A groove goes down, so the wall's normal leans towards the middle of the groove.
    return np.clip(dx * NORMAL_STRENGTH, -1.0, 1.0), np.clip(-dy * NORMAL_STRENGTH, -1.0, 1.0)


def main():
    rng = np.random.default_rng(SEED)
    grooves, columns, rows = draw(rng)
    grooves = rivets(grooves, rng, columns, rows)
    depth = np.asarray(grooves.filter(ImageFilter.GaussianBlur(GROOVE_BLUR)), dtype=np.float32) / 255.0
    nx, ny = normal_xy(depth)
    out = np.stack([nx * 0.5 + 0.5, ny * 0.5 + 0.5, depth], axis=-1)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    Image.fromarray(np.clip(out * 255.0, 0, 255).astype(np.uint8)).save(OUT)
    print("%s %dx%d: %d plates, seams on %.1f %% of the sheet -> %s" % (
        os.path.basename(OUT), SIZE, SIZE, (len(columns) + 1) * (len(rows) + 1),
        100.0 * (depth > 0.2).mean(), os.path.relpath(OUT, REPO)))


if __name__ == "__main__":
    main()
