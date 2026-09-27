"""Interior kit trim sheet (batch 1 of the kit, 26. 9. 2026): procedural, 4096 x 2048 px at 1024 px/m
(ArtSource/Kit/kit_rules.json texel_density). Strips run along U (they repeat every 4 m along a part);
their heights are real millimetres.

    python Tools/Kit/kit_trim_sheet.py

Writes ArtSource/Kit/Textures/T_Kit_Trim_BC.png (sRGB), T_Kit_Trim_N.png (OpenGL normal, the importer flips
green), T_Kit_Trim_ORM.png (R occlusion, G roughness, B metallic) and trim_index.json with each strip's rows
and its Blender V range (Blender UVs have v = 0 at the bottom, the image row 0 at the top). A preview with the
strip names: trim_preview.jpg. Deterministic, no outside texture.
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RULES = json.load(open(os.path.join(ROOT, "ArtSource", "Kit", "kit_rules.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "ArtSource", "Kit", "Textures")
W, H = RULES["texel_density"]["trim_sheet_size_px"]
PPM = RULES["texel_density"]["trim_sheet"]          # px per metre
GAP = 4                                             # px between strips (bleed)


def lin2srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def px(mm):
    return max(1, int(round(mm / 1000.0 * PPM)))


# palette (linear): the kit's design language
GRAPHITE = np.array([0.06, 0.06, 0.065])
GUNMETAL = np.array([0.33, 0.33, 0.34])
DARK = np.array([0.02, 0.02, 0.022])
RUBBER = np.array([0.018, 0.018, 0.02])
ORANGE = np.array([0.85, 0.34, 0.06])
CREAM = np.array([0.7, 0.66, 0.58])
LEATHER = np.array([0.035, 0.032, 0.03])


class Strip:
    """h (height, m), col (linear RGB), rough, metal - arrays of shape (rows, W)."""

    def __init__(self, name, mm):
        self.name, self.mm = name, mm
        self.rows = px(mm)
        self.h = np.zeros((self.rows, W), np.float32)
        self.col = np.zeros((self.rows, W, 3), np.float32)
        self.rough = np.zeros((self.rows, W), np.float32)
        self.metal = np.zeros((self.rows, W), np.float32)
        self.v = np.linspace(0, 1, self.rows, dtype=np.float32)[:, None] * np.ones((1, W), np.float32)   # 0 top .. 1 bottom
        self.u = np.arange(W, dtype=np.float32)[None, :] / PPM * np.ones((self.rows, 1), np.float32)       # metres along

    def fill(self, col, rough, metal):
        self.col[:] = col
        self.rough[:] = rough
        self.metal[:] = metal

    def edge_bevel(self, mm=2.0, depth=0.0015):
        """Rounded edges top and bottom (the strip reads as a separate part)."""
        e = px(mm)
        ramp = np.clip(np.minimum(np.arange(self.rows), np.arange(self.rows)[::-1]) / max(1, e), 0, 1)[:, None]
        self.h += (np.sin(ramp * np.pi / 2) - 1.0) * depth

    def bolts(self, pitch_mm, dia_mm, v_rel=0.5, countersunk=True, col=None):
        pitch = pitch_mm / 1000.0
        r = dia_mm / 2000.0
        du = (np.mod(self.u, pitch) - pitch / 2)
        dv = (self.v - v_rel) * self.rows / PPM
        d = np.sqrt(du ** 2 + dv ** 2)
        inside = d < r
        dome = np.sqrt(np.clip(1 - (d / r) ** 2, 0, 1)) * (0.0006 if countersunk else 0.0012)
        self.h = np.where(inside, np.maximum(self.h, dome - (0.0003 if countersunk else 0)), self.h)
        # hex socket
        hexr = r * 0.45
        sock = (np.maximum(np.abs(du), np.abs(dv) * 0.87 + np.abs(du) * 0.5) < hexr)
        self.h = np.where(sock, self.h - 0.0008, self.h)
        if col is not None:
            self.col[inside] = col
        self.metal[inside] = 1.0
        self.rough[inside] = 0.35


def perlin_like(shape, scale_px, seed):
    rng = np.random.default_rng(seed)
    small = rng.random((shape[0] // scale_px + 2, shape[1] // scale_px + 2)).astype(np.float32)
    big = np.kron(small, np.ones((scale_px, scale_px), np.float32))[:shape[0], :shape[1]]
    # cheap blur
    k = max(1, scale_px // 2)
    c = np.cumsum(np.pad(big, ((0, 0), (k, k)), mode="edge"), axis=1)
    big = (c[:, 2 * k:] - c[:, :-2 * k]) / (2 * k)
    c = np.cumsum(np.pad(big, ((k, k), (0, 0)), mode="edge"), axis=0)
    big = (c[2 * k:, :] - c[:-2 * k, :]) / (2 * k)
    return (big - big.min()) / max(1e-6, big.max() - big.min())


def build():
    strips = []
    # rail: satin gunmetal bar, two grooves, bolts every 80 mm
    s = Strip("rail_bolted", 50)
    s.fill(GUNMETAL, 0.34, 1.0)
    s.edge_bevel(3)
    for vg in (0.18, 0.82):
        s.h -= (np.abs(s.v - vg) < 0.02) * 0.0008
    s.bolts(80, 7, 0.5, col=GUNMETAL * 0.8)
    strips.append(s)
    # bolted flange, graphite paint
    s = Strip("flange_bolted", 30)
    s.fill(GRAPHITE, 0.5, 0.0)
    s.edge_bevel(2)
    s.bolts(50, 6, 0.5, col=GUNMETAL * 0.9)
    strips.append(s)
    # ribbed rubber (ribs across the strip every 8 mm)
    s = Strip("rubber_ribbed", 60)
    s.fill(RUBBER, 0.86, 0.0)
    rib = 0.5 + 0.5 * np.cos(2 * np.pi * s.u / 0.008)
    s.h += (rib ** 3) * 0.0012
    s.edge_bevel(4, 0.002)
    strips.append(s)
    # perforated plate: 5 mm holes on a 10 mm grid, staggered
    s = Strip("perforated", 100)
    s.fill(GRAPHITE, 0.55, 0.0)
    gv = s.v * s.rows / PPM
    row = np.floor(gv / 0.010)
    du = np.mod(s.u + (row % 2) * 0.005, 0.010) - 0.005
    dv = np.mod(gv, 0.010) - 0.005
    hole = np.sqrt(du ** 2 + dv ** 2) < 0.0025
    s.h = np.where(hole, -0.004, s.h)
    s.col[hole] = DARK
    s.edge_bevel(3)
    strips.append(s)
    # hazard stripes, 45 deg, 40 mm bands, painted over graphite, worn a little at the edges
    s = Strip("hazard", 60)
    s.fill(GRAPHITE, 0.5, 0.0)
    band = np.mod((s.u + s.v * s.rows / PPM) / 0.04, 2.0) < 1.0
    wear = perlin_like(s.h.shape, 24, 3) > 0.82
    s.col[band & ~wear] = ORANGE
    s.rough[band] = 0.42
    s.edge_bevel(2)
    strips.append(s)
    # diamond tread plate
    s = Strip("antislip_tread", 80)
    s.fill(GUNMETAL * 0.7, 0.45, 1.0)
    a = np.mod(s.u / 0.025, 1.0) - 0.5
    b = np.mod(s.v * s.rows / PPM / 0.025, 1.0) - 0.5
    alt = (np.floor(s.u / 0.025) + np.floor(s.v * s.rows / PPM / 0.025)) % 2
    dx, dy = np.where(alt > 0, a + b, a - b), np.where(alt > 0, a - b, a + b)
    lug = (np.abs(dx) < 0.12) & (np.abs(dy) < 0.36)
    s.h += lug * 0.0012
    s.edge_bevel(3)
    strips.append(s)
    # stitched seam: leather with a double stitch line
    s = Strip("seam_stitched", 40)
    s.fill(LEATHER, 0.62, 0.0)
    grain = perlin_like(s.h.shape, 3, 7)
    s.h += (grain - 0.5) * 0.0002
    s.h -= np.exp(-((s.v - 0.5) / 0.05) ** 2) * 0.0015                 # the seam's valley
    for vs in (0.3, 0.7):
        dash = (np.abs(s.v - vs) < 0.035) & (np.mod(s.u, 0.006) < 0.0038)
        s.col[dash] = CREAM * 0.55
        s.h += dash * 0.0003
        s.rough[dash] = 0.7
    strips.append(s)
    # label band: repeating small text on graphite (printed, no height)
    s = Strip("label_band", 30)
    s.fill(GRAPHITE, 0.5, 0.0)
    img = Image.new("L", (W, s.rows), 0)
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(os.path.join(ROOT, "Content", "UI", "Fonts", "ShareTechMono-Regular.ttf"), int(s.rows * 0.45))
    except OSError:
        font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", int(s.rows * 0.45))
    text = "HALCYON FREIGHTWORKS  //  KIT-A  //  24V DC  //  DO NOT PAINT  //  "
    x = 0
    while x < W:
        d.text((x, int(s.rows * 0.25)), text, font=font, fill=255)
        x += int(d.textlength(text, font=font))
    t = np.asarray(img, np.float32)[:, :] / 255.0
    s.col = s.col * (1 - t[..., None]) + (CREAM * 0.8)[None, None, :] * t[..., None]
    s.edge_bevel(2)
    for vl in (0.08, 0.92):
        line = np.abs(s.v - vl) < 0.03
        s.col[line] = CREAM * 0.8
    strips.append(s)
    # panel edge: a bevel into a groove (the lip of a panel)
    s = Strip("edge_groove", 40)
    s.fill(GRAPHITE, 0.48, 0.0)
    s.h += np.clip((0.35 - s.v) / 0.35, 0, 1) * -0.002
    s.h -= (np.abs(s.v - 0.62) < 0.05) * 0.0015
    strips.append(s)
    # vent slots: 6 mm slots at 16 mm pitch, 60 mm long
    s = Strip("vent_slots", 80)
    s.fill(GRAPHITE, 0.52, 0.0)
    su = np.mod(s.u, 0.016) - 0.008
    sv = (s.v - 0.5) * s.rows / PPM
    slot = (np.abs(su) < 0.003) & (np.abs(sv) < 0.03)
    s.h = np.where(slot, -0.005, s.h)
    s.col[slot] = DARK
    s.edge_bevel(3)
    strips.append(s)
    # kick plate: brushed gunmetal, bolt rows near both edges
    s = Strip("kickplate", 100)
    s.fill(GUNMETAL * 0.85, 0.4, 1.0)
    brush = perlin_like((s.rows, W), 2, 11)
    s.rough += (brush - 0.5) * 0.08
    s.h += (brush - 0.5) * 0.00005
    s.edge_bevel(3)
    s.bolts(120, 7, 0.16, col=GUNMETAL)
    s.bolts(120, 7, 0.84, col=GUNMETAL)
    strips.append(s)
    # structural rib face: graphite with a centre groove and bolts every 100 mm
    s = Strip("rib_face", 30)
    s.fill(GRAPHITE * 0.9, 0.46, 0.0)
    s.edge_bevel(3)
    s.h -= (np.abs(s.v - 0.5) < 0.06) * 0.001
    s.bolts(100, 6, 0.5, col=GUNMETAL * 0.9)
    strips.append(s)
    # gasket: a dark rubber bulb seal
    s = Strip("gasket", 20)
    s.fill(RUBBER, 0.8, 0.0)
    s.h += np.sin(np.clip(s.v, 0, 1) * np.pi) * 0.002
    strips.append(s)
    return strips


def main():
    os.makedirs(OUT, exist_ok=True)
    strips = build()
    h = np.zeros((H, W), np.float32)
    col = np.zeros((H, W, 3), np.float32) + GRAPHITE
    rough = np.full((H, W), 0.5, np.float32)
    metal = np.zeros((H, W), np.float32)
    index, r = {}, GAP
    for s in strips:
        # bleed: repeat the strip's edge rows into the gap so mips do not mix neighbours
        r0, r1 = r, r + s.rows
        h[r0:r1], col[r0:r1], rough[r0:r1], metal[r0:r1] = s.h, s.col, s.rough, s.metal
        for g in range(1, GAP):
            if r0 - g >= 0:
                h[r0 - g], col[r0 - g], rough[r0 - g], metal[r0 - g] = s.h[0], s.col[0], s.rough[0], s.metal[0]
            if r1 - 1 + g < H:
                h[r1 - 1 + g], col[r1 - 1 + g], rough[r1 - 1 + g], metal[r1 - 1 + g] = s.h[-1], s.col[-1], s.rough[-1], s.metal[-1]
        index[s.name] = {"rows": [r0, r1], "height_m": s.mm / 1000.0,
                         "v_blender": [round(1.0 - r1 / H, 6), round(1.0 - r0 / H, 6)], "u_repeat_m": W / PPM}
        r = r1 + GAP
    # occlusion from height (cavities darker), normals from height (OpenGL)
    def blur(a, k):
        c = np.cumsum(np.pad(a, ((0, 0), (k, k)), mode="edge"), axis=1)
        a = (c[:, 2 * k:] - c[:, :-2 * k]) / (2 * k)
        c = np.cumsum(np.pad(a, ((k, k), (0, 0)), mode="edge"), axis=0)
        return (c[2 * k:, :] - c[:-2 * k, :]) / (2 * k)
    ao = np.clip(1.0 - np.clip(blur(h, 6) - h, 0, None) * 400.0, 0.35, 1.0)
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * PPM / 2
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * PPM / 2
    n = np.dstack([-gx, gy, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    Image.fromarray((lin2srgb(col) * 255 + 0.5).astype(np.uint8), "RGB").save(os.path.join(OUT, "T_Kit_Trim_BC.png"))
    Image.fromarray(((n * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8), "RGB").save(os.path.join(OUT, "T_Kit_Trim_N.png"))
    Image.fromarray(np.dstack([ao, rough, metal]).clip(0, 1).__mul__(255).astype(np.uint8), "RGB").save(os.path.join(OUT, "T_Kit_Trim_ORM.png"))
    json.dump({"size_px": [W, H], "px_per_m": PPM, "strips": index}, open(os.path.join(OUT, "trim_index.json"), "w", encoding="utf-8"), indent=1)
    # preview: the used rows at 1:1 for the first 1024 px, with names
    used = r
    prev = Image.open(os.path.join(OUT, "T_Kit_Trim_BC.png")).crop((0, 0, 1024, used))
    shade = ((n[:used, :1024, 0] * 0.4 + n[:used, :1024, 1] * 0.6 + 0.3) * 200).clip(0, 255).astype(np.uint8)
    sh = Image.fromarray(shade, "L").convert("RGB")
    canvas = Image.new("RGB", (2 * 1024 + 300, used), (20, 20, 22))
    canvas.paste(prev, (300, 0))
    canvas.paste(sh, (300 + 1024, 0))
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 16)
    for name, e in index.items():
        d.text((8, e["rows"][0]), "%s %d mm" % (name, round(e["height_m"] * 1000)), font=f, fill=(230, 230, 230))
    canvas = canvas.resize((canvas.width, used * 2), Image.NEAREST)
    canvas.save(os.path.join(OUT, "trim_preview.jpg"), quality=90)
    print("TRIM", OUT, "rows used", used, "of", H)


if __name__ == "__main__":
    main()
