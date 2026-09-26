"""Large grime decal cards for ship hulls (26. 9. 2026, from the SC breakdown: planes of streaky grime over the
engines and across the wings - starcitizenreference/ShipDetailing_VideoNotes.md, chapter 3).

    python Tools/Assets/generate_grime_textures.py

Writes ArtSource/Ships/Shared/Decals/Grime/T_Grime_BC.png (sRGB: grime colour, alpha = coverage) and
T_Grime_M.png (R 1 = the card applies, G roughness, B metallic 0), 2048 px, a 2 x 2 atlas. Each cell has its
source edge at the TOP of the cell (the card is laid with that edge towards where the dirt comes from) and
fades out to the other three edges, so a card never shows its outline:
  0 streaks  thin streaks running down from the top (rain / gravity on a side, air flow on a top surface)
  1 soot     a dark band at the top that thins out in turbulent tongues (behind exhausts)
  2 smear    broad blotches with faint streaks (wing roots, leading edges, around hatches)
  3 rim      dirt collected along the top edge with drips (under a seam, above a gear bay)
Procedural and deterministic (seed), no outside texture - nothing to license.
"""
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "ArtSource", "Ships", "Shared", "Decals", "Grime")
CELL = 1024
COLOUR = (58, 52, 45)        # sRGB, a warm dark grey-brown (reads on white and on graphite paint)
ROUGHNESS = 0.78


def blur_1d(a, r, axis):
    """Box blur along one axis, three passes (close to a gaussian), edge-clamped."""
    if r < 1:
        return a
    for _ in range(3):
        pad = [(0, 0)] * a.ndim
        pad[axis] = (r, r)
        p = np.pad(a, pad, mode="edge")
        c = np.cumsum(p, axis=axis, dtype=np.float64)
        c = np.concatenate([np.zeros_like(np.take(c, [0], axis=axis)), c], axis=axis)
        n = a.shape[axis]
        hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
        lo = np.take(c, np.arange(0, n), axis=axis)
        a = ((hi - lo) / (2 * r + 1)).astype(np.float32)
    return a


def blur(a, r):
    return blur_1d(blur_1d(a, r, 0), r, 1)


def noise(rng, scale, octaves=4):
    """Value noise in 0..1 from blurred random fields."""
    out = np.zeros((CELL, CELL), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        s = max(2, int(scale / (2 ** o)))
        field = rng.random((CELL // s + 2, CELL // s + 2)).astype(np.float32)
        big = np.kron(field, np.ones((s, s), np.float32))[:CELL, :CELL]
        out += blur(big, max(1, s // 2)) * amp
        total += amp
        amp *= 0.5
    out /= total
    return (out - out.min()) / max(1e-6, out.max() - out.min())


def window(top_soft=0.02, side=0.12, bottom=0.35):
    """1 inside, fading to 0 at the sides and the bottom (the top is the source edge, barely faded)."""
    y = np.linspace(0, 1, CELL, dtype=np.float32)[:, None]
    x = np.linspace(0, 1, CELL, dtype=np.float32)[None, :]
    sx = np.clip(np.minimum(x, 1 - x) / side, 0, 1)
    sy = np.clip((1 - y) / bottom, 0, 1) * np.clip(y / top_soft, 0, 1)
    return (sx * sx * (3 - 2 * sx)) * (sy * sy * (3 - 2 * sy))


def streak_lines(rng, count, length, width, start_max, strength, soft=4):
    """Streaks that break up along their length (low-frequency noise per streak) and drift a little sideways,
    blurred across: hard, even lines read as a barcode."""
    a = np.zeros((CELL, CELL), np.float32)
    for _ in range(count):
        x0 = rng.random() * CELL
        y0 = int(rng.random() * start_max * CELL)
        ln = int((length[0] + rng.random() * (length[1] - length[0])) * CELL)
        w = int(rng.integers(width[0], width[1] + 1))
        s = strength * (0.3 + 0.7 * rng.random())
        y1 = min(CELL, y0 + ln)
        n = y1 - y0
        if n < 4:
            continue
        fade = np.linspace(1.0, 0.0, n, dtype=np.float32) ** (0.6 + rng.random())
        breaks = blur_1d(rng.random(n).astype(np.float32)[:, None], max(2, n // 12), 0)[:, 0]
        breaks = np.clip((breaks - breaks.min()) / max(1e-6, breaks.max() - breaks.min()) * 1.6 - 0.3, 0, 1)
        drift = np.cumsum(rng.normal(0, 0.15, n)).astype(np.float32)
        for k in range(n):
            xc = int(x0 + drift[k])
            lo, hi = max(0, xc - w // 2), min(CELL, xc + w // 2 + 1)
            if lo < hi:
                a[y0 + k, lo:hi] = np.maximum(a[y0 + k, lo:hi], fade[k] * breaks[k] * s)
    return blur_1d(blur_1d(a, soft, 1), 2, 0)


def cell_streaks(rng):
    lines = streak_lines(rng, 150, (0.15, 0.95), (2, 14), 0.35, 0.75)
    wobble = noise(rng, 180)
    band = np.clip(1.0 - np.linspace(0, 1, CELL, dtype=np.float32)[:, None] / 0.18, 0, 1) * 0.35
    a = np.maximum(lines * (0.55 + 0.45 * wobble), band * wobble)
    return np.clip(a, 0, 1) * window()


def cell_soot(rng):
    y = np.linspace(0, 1, CELL, dtype=np.float32)[:, None]
    turb = noise(rng, 220, 5)
    streaks = blur_1d(rng.random((CELL, CELL)).astype(np.float32), 40, 0)
    streaks = (streaks - streaks.min()) / (streaks.max() - streaks.min())
    reach = 0.25 + 0.55 * turb * (0.6 + 0.4 * streaks)
    a = np.clip(1.0 - y / reach, 0, 1) ** 1.4
    return np.clip(a * (0.75 + 0.25 * turb), 0, 1) * window(side=0.18, bottom=0.2)


def cell_smear(rng):
    blot = noise(rng, 200, 5)
    blot = np.clip((blot - 0.22) / 0.55, 0, 1) ** 1.3
    lines = streak_lines(rng, 90, (0.1, 0.5), (2, 8), 0.9, 0.5)
    # mottled, capped: a flat dark core read as a stain, not as grime
    a = np.maximum(blot * 0.55 * (0.55 + 0.45 * noise(rng, 36, 3)), lines * blot)
    return np.clip(a, 0, 1) * window(top_soft=0.2, side=0.2, bottom=0.25)


def cell_rim(rng):
    y = np.linspace(0, 1, CELL, dtype=np.float32)[:, None]
    wav = noise(rng, 140)
    band = np.clip(1.0 - y / (0.06 + 0.1 * wav), 0, 1) ** 0.8
    drips = streak_lines(rng, 110, (0.05, 0.6), (2, 9), 0.08, 0.8, soft=3)
    a = np.maximum(band * 0.9, drips)
    return np.clip(a * (0.7 + 0.3 * noise(rng, 90)), 0, 1) * window(side=0.08, bottom=0.3)


def main():
    os.makedirs(OUT, exist_ok=True)
    rng = np.random.default_rng(26092026)
    cells = [cell_streaks(rng), cell_soot(rng), cell_smear(rng), cell_rim(rng)]
    alpha = np.zeros((2 * CELL, 2 * CELL), np.float32)
    for k, c in enumerate(cells):
        r, q = k // 2, k % 2
        alpha[r * CELL:(r + 1) * CELL, q * CELL:(q + 1) * CELL] = c
    bc = np.zeros((2 * CELL, 2 * CELL, 4), np.uint8)
    # a little tone variation inside the grime (not one flat colour)
    tone = 0.85 + 0.3 * np.kron(noise(rng, 120), np.ones((2, 2), np.float32))
    for i, v in enumerate(COLOUR):
        bc[..., i] = np.clip(v * tone, 0, 255).astype(np.uint8)
    bc[..., 3] = np.clip(alpha * 255, 0, 255).astype(np.uint8)
    Image.fromarray(bc, "RGBA").save(os.path.join(OUT, "T_Grime_BC.png"))
    m = np.zeros((2 * CELL, 2 * CELL, 3), np.uint8)
    m[..., 0] = 255
    m[..., 1] = int(ROUGHNESS * 255)
    Image.fromarray(m, "RGB").save(os.path.join(OUT, "T_Grime_M.png"))
    preview = Image.new("RGB", (2 * CELL, 2 * CELL), (235, 235, 232))
    over = Image.fromarray(bc, "RGBA")
    preview.paste(over, (0, 0), over)
    preview.resize((1024, 1024)).save(os.path.join(OUT, "grime_preview.jpg"), quality=90)
    print("GRIME", OUT)


if __name__ == "__main__":
    main()
