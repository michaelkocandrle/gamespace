"""Draws the interior kit's standard sections, the plan rhythm and the pivot conventions from
ArtSource/Kit/kit_rules.json (step 2 of the kit brief, 26. 9. 2026).

    python Tools/Kit/draw_kit_sections.py

Output: Docs/Kit/kit_sections.png. Everything is read from the rules file, so the drawing stays true to them.
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RULES = json.load(open(os.path.join(ROOT, "ArtSource", "Kit", "kit_rules.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "Docs", "Kit", "kit_sections.png")
PX = 170                                  # pixels per metre
F = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 20)
FB = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 24)
FS = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 16)
BG, GRID, GRID2 = (24, 25, 28), (44, 46, 52), (62, 66, 74)
WALL, STRUCT, LIGHT_W, LIGHT_C, ORANGE, TXT, DIM = (120, 124, 132), (70, 74, 82), (255, 214, 160), (120, 190, 255), (230, 110, 30), (230, 230, 230), (170, 170, 170)


def section_outline(sec, width):
    """Half outline (x from the centreline, z) of the panel faces: floor edge, plinth, vertical, slope, cove, ceiling."""
    w2 = width / 2
    inset = 0.75 * sec["slope_rise"]
    z_slope_top = sec["vertical_to"] + sec["slope_rise"]
    return [(0, 0), (w2, 0), (w2, sec["vertical_to"]), (w2 - inset, z_slope_top), (w2 - inset, sec["ceiling"]), (0, sec["ceiling"])], w2 - inset, z_slope_top


def draw_section(d, ox, oy, key, sec, width):
    """Section with its origin (centreline, floor) at pixel (ox, oy)."""
    zones = RULES["zones"]
    sd = zones["structure_depth"]
    top = sec["ceiling"] + zones["ceiling_structure_depth"]
    # grid
    g = RULES["grid"]
    x = -width / 2 - sd
    while x <= width / 2 + sd + 1e-6:
        X = ox + x * PX
        d.line([(X, oy - top * PX), (X, oy + 0.2 * PX)], fill=GRID2 if abs(round(x / g["plan"]) * g["plan"] - x) < 1e-6 else GRID)
        x += g["vertical"]
    z = 0.0
    while z <= top + 1e-6:
        Y = oy - z * PX
        d.line([(ox - (width / 2 + sd) * PX, Y), (ox + (width / 2 + sd) * PX, Y)], fill=GRID2 if abs(z * 10 % 3) < 1e-6 else GRID)
        z += g["vertical"]
    half, x_top, z_slope_top = section_outline(sec, width)
    for side in (1, -1):
        pts = [(ox + side * px_ * PX, oy - pz * PX) for px_, pz in half]
        # structure band behind the faces
        band = [(ox + side * (px_ + (sd if px_ > 0 else 0)) * PX, oy - pz * PX) for px_, pz in half[1:5]]
        d.polygon(pts[1:5] + band[::-1], fill=STRUCT)
        d.line(pts, fill=WALL, width=4)
        # plinth chamfer and floor light, cove light
        w2 = width / 2
        ph = zones["plinth_height"]
        d.line([(ox + side * w2 * PX, oy - ph * PX), (ox + side * (w2 - ph) * PX, oy)], fill=WALL, width=3)
        d.line([(ox + side * (w2 - ph * 0.7) * PX, oy - 3), (ox + side * (w2 - ph * 0.2) * PX, oy - ph * 0.5 * PX)], fill=LIGHT_C, width=5)
        d.line([(ox + side * x_top * PX, oy - z_slope_top * PX - 4), (ox + side * (x_top - zones["cove_depth"]) * PX, oy - z_slope_top * PX - 4)], fill=LIGHT_W, width=6)
        # portal outline (dashed): the frame proud of the faces
        pp = sec.get("portal_protrusion") or 0
        if pp:
            prow = [(ox + side * (px_ - pp if px_ > 0 else px_) * PX, oy - (pz - (pp if pz >= sec["ceiling"] - 1e-6 else 0)) * PX) for px_, pz in half[1:6]]
            for a, b in zip(prow, prow[1:]):
                n = 12
                for k in range(0, n, 2):
                    d.line([(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n),
                            (a[0] + (b[0] - a[0]) * (k + 1) / n, a[1] + (b[1] - a[1]) * (k + 1) / n)], fill=ORANGE, width=2)
    # floor structure and ceiling tray
    d.rectangle([ox - width / 2 * PX, oy, ox + width / 2 * PX, oy + zones["floor_structure_depth"] * PX], fill=STRUCT)
    d.line([(ox - width / 2 * PX, oy), (ox + width / 2 * PX, oy)], fill=WALL, width=4)
    tw = min(0.3, (sec["ceiling_width"] or width) * 0.5)
    d.rectangle([ox - tw / 2 * PX, oy - sec["ceiling"] * PX - 0.18 * PX, ox + tw / 2 * PX, oy - sec["ceiling"] * PX], outline=DIM, width=2)
    # capsule for scale
    r, hh = 0.42, 0.96
    d.rounded_rectangle([ox - r * PX, oy - 2 * hh * PX, ox + r * PX, oy], radius=int(r * PX), outline=(120, 200, 120), width=2)
    # dimensions
    d.text((ox - 40, oy + 0.22 * PX), "%.2f m" % width, font=F, fill=TXT)
    # labels right of the section, pushed apart so they never overlap
    labels = [(sec["ceiling"], "strop %.1f" % sec["ceiling"]), (z_slope_top, "sklon 3:4 do %.1f" % z_slope_top),
              (sec["vertical_to"], "svislá do %.1f" % sec["vertical_to"])]
    last = -1e9
    for zz, text in labels:
        Y = max(oy - zz * PX - 10, last + 22)
        d.text((ox + (width / 2 + sd) * PX + 8, Y), text, font=FS, fill=DIM)
        last = Y
    d.text((ox - (width / 2 + sd) * PX, oy - top * PX - 34), "%s – %s" % (key, sec["name"]), font=FB, fill=TXT)


def main():
    S = RULES["sections"]
    W = 3000
    img = Image.new("RGB", (W, 1650), BG)
    d = ImageDraw.Draw(img)
    d.text((24, 16), "Interiérový kit – standardní průřezy, rytmus a pivoty (ArtSource/Kit/kit_rules.json)", font=FB, fill=TXT)
    d.text((24, 50), "Mřížka: půdorys 0,3 m (světlé čáry), svisle 0,1 m. Šedě líc panelů, tmavě zóna konstrukce 0,2 m, oranžově čárkovaně obrys portálu, "
           "modře lišta u podlahy, žlutě lišta ve vybrání, zeleně kapsle postavy (0,84 × 1,92 m).", font=FS, fill=DIM)
    oy = 560
    x = 260
    for key, width in (("S", S["S"]["width"]), ("N", S["N"]["width"]), ("W", S["W"]["width"]), ("T", 3.6)):
        sec = S[key]
        draw_section(d, x, oy, key, sec, width)
        x += (width + 2 * RULES["zones"]["structure_depth"]) * PX + 250
    # plan: portal rhythm along a W corridor
    g = RULES["grid"]
    px0, py0 = 120, 900
    d.text((px0, py0 - 70), "Půdorys chodby W: portál 0,3 + stěny 0,9 = rozteč %.1f m; moduly %s m, výplně %s m" % (
        g["portal_pitch"], ", ".join("%.1f" % v for v in g["module_lengths"]), ", ".join("%.1f" % v for v in g["filler_lengths"])), font=F, fill=TXT)
    L = 4.8
    wd = S["W"]["width"]
    for k in range(int(L / g["plan"]) + 1):
        X = px0 + k * g["plan"] * PX
        d.line([(X, py0 - 20), (X, py0 + wd * PX + 20)], fill=GRID2)
    d.rectangle([px0, py0, px0 + L * PX, py0 + wd * PX], outline=WALL, width=3)
    seq = [("P", 0.3), ("0.6", 0.6), ("0.3", 0.3), ("P", 0.3), ("0.9", 0.9), ("P", 0.3), ("1.2", 1.2), ("0.9", 0.9)]
    xx = 0.0
    for name, ln in seq:
        X0, X1 = px0 + xx * PX, px0 + (xx + ln) * PX
        for yy, h in ((py0 - 0.2 * PX, 0.2 * PX), (py0 + wd * PX, 0.2 * PX)):
            d.rectangle([X0 + 2, yy, X1 - 2, yy + h], fill=ORANGE if name == "P" else STRUCT, outline=WALL)
        if name == "P":
            d.rectangle([X0 + 2, py0, X1 - 2, py0 + 0.1 * PX], fill=(150, 80, 30))
            d.rectangle([X0 + 2, py0 + wd * PX - 0.1 * PX, X1 - 2, py0 + wd * PX], fill=(150, 80, 30))
        d.text((X0 + 6, py0 + wd * PX + 0.22 * PX), "portál" if name == "P" else name, font=FS, fill=TXT)
        xx += ln
    d.line([(px0 - 60, py0 + wd / 2 * PX), (px0 + L * PX + 40, py0 + wd / 2 * PX)], fill=DIM, width=1)
    d.text((px0 + L * PX + 50, py0 + wd / 2 * PX - 12), "+X (směr chodby)", font=F, fill=TXT)
    # pivot conventions
    bx, by = 1200, 900
    d.text((bx, by - 70), "Pivoty a osy (+X dopředu, +Y vlevo, +Z nahoru, měřítko 1, transformace aplikované)", font=F, fill=TXT)

    def axes(x0, y0, label, note):
        d.ellipse([x0 - 7, y0 - 7, x0 + 7, y0 + 7], fill=(255, 80, 80))
        d.line([(x0, y0), (x0 + 70, y0)], fill=(255, 80, 80), width=4)
        d.text((x0 + 74, y0 - 12), "X", font=F, fill=(255, 80, 80))
        d.line([(x0, y0), (x0, y0 - 70)], fill=(80, 200, 80), width=4)
        d.text((x0 - 8, y0 - 98), "Y", font=F, fill=(80, 200, 80))
        d.text((x0 - 20, y0 + 16), label, font=FB, fill=TXT)
        yy = y0 + 48
        for line in note:
            d.text((x0 - 20, yy), line, font=FS, fill=DIM)
            yy += 22

    axes(bx + 40, by + 140, "Průběžné díly", ["podlaha, strop, portál, trubky, schody:", "začátek modulu, osa průřezu, z = 0,", "+X po směru chodby"])
    axes(bx + 480, by + 140, "Stěny, dveře, přepážky", ["roh dole na lícové rovině panelu,", "líc míří na +X, šířka po +Y (0..W)"])
    axes(bx + 900, by + 140, "Rohy", ["vnitřní roh průsečíku lícových rovin,", "líce míří na +X a +Y"])
    axes(bx + 1320, by + 140, "Výbava, konzole, světla", ["střed montážní plochy (na stěně / na", "podlaze pod zadní hranou), čelo na +X"])
    d.text((bx, by + 330), "Sockety: SOCKET_Snap_Start/End/Left/Right/Top/Bottom (na mřížce), SOCKET_Light_n (X = směr světla, parametry v manifestu),", font=FS, fill=DIM)
    d.text((bx, by + 354), "SOCKET_Decal_n (X = normála plochy, Y = nahoru decalu, tagy v manifestu), SOCKET_Mount_n (úchyt výbavy).", font=FS, fill=DIM)
    d.text((bx, by + 390), "Jména: SM_Kit_<Kategorie>_<Díl><velikost dm><průřez>_<Varianta>, např. SM_Kit_Wall_Grille06W_B; MI_Kit_<Výrobce>_<Role>; T_Kit_<Jméno>_<Mapa>.", font=FS, fill=DIM)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
