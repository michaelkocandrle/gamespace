"""The Wayfarer cabin from above and in section: as laid out now (procedural room 3.8 m) and as proposed from the
interior kit (author 29. 9. 2026: "fix the ship's material, walls, floor, ceiling ... then the furniture").

    python Tools/Kit/cabin_plan.py            -> Docs/Kit/cabin_plan_wayfarer.png

The kit's wall profile (vertical to 1.3 m, a 3:4 slope to 2.1 m, the cove to the 2.3 m ceiling, 0.2 m structure
behind the panel face) fits the hull over the cabin up to 3.0 m between the panel faces (hull_fit_sections.py: the
tightest station x 15.15 at the cockpit bulkhead). Layout metres (x forward, y to port); the furniture of the
approved layout (Wayfarer_layout.json) moves where the narrower room needs it: the bunk forward into an alcove under
the slope, the suit locker and the food dispenser into the wall as kit modules, the hygiene cell a box on the floor.
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "Docs", "Kit", "cabin_plan_wayfarer.png")
S = 120                                   # px per metre
RULES = json.load(open(os.path.join(ROOT, "ArtSource", "Kit", "kit_rules.json"), encoding="utf-8"))
W_SEC = RULES["sections"]["W"]
HALF = 1.5                                # proposal: 3.0 m between the panel faces
STRUCT = RULES["zones"]["structure_depth"]


def layout():
    L = json.load(open(os.path.join(ROOT, "ArtSource", "Ships", "Wayfarer", "Design", "Wayfarer_layout.json"), encoding="utf-8"))
    room = next(r for r in L["rooms"] if r["id"] == "cabin")
    objs = [o for o in L["objects"] if o.get("room") == "cabin"]
    doors = [d for d in L["doors"] if room["rect"][0] - 0.01 <= d["at"][0] <= room["rect"][1] + 0.01]
    return room, objs, doors


SHORT = {"Skříň na skafandr a zbraň": "skříň\nskafandr", "Hygienická buňka": "hygienická\nbuňka",
         "Výdejník jídla a vody": "výdejník\njídla", "Lůžko": "lůžko", "Podpora života S1": "podpora života\n(pod lůžkem)"}


def proposal(objs):
    """The kit room's furniture: (name, rect, kind) - kind 'wall' = a kit module in the wall (proud of the panel
    face), 'floor' = standing on the floor, 'below' = under the floor or the bunk."""
    y0 = -HALF
    return [
        ("Skříň na skafandr a zbraň", (10.64, 11.54, y0, y0 + 0.2), "wall"),
        ("Hygienická buňka", (11.84, 13.04, y0, y0 + 1.0), "floor"),
        ("Výdejník jídla a vody", (13.34, 14.54, y0, y0 + 0.2), "wall"),
        ("Lůžko", (13.14, 15.14, HALF - 0.85, HALF), "floor"),
        ("Podpora života S1", (13.3, 14.9, HALF - 0.75, HALF - 0.1), "below"),
    ]


def plan_panel(title, notes, half, furniture, doors, kit):
    x0, x1 = 10.0, 15.6
    Wd, Hd = int((x1 - x0) * S) + 260, int(4.4 * S) + 230
    img = Image.new("RGB", (Wd, Hd), (24, 25, 28))
    d = ImageDraw.Draw(img)
    F = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 26)
    FS = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 17)
    oy = 80 + int(2.2 * S)

    def P(x, y):
        return (30 + int((x - x0) * S), oy - int(y * S))

    def rect(xa, xb, ya, yb, **kw):
        a, b = P(xa, max(ya, yb)), P(xb, min(ya, yb))
        d.rectangle([a, b], **kw)

    d.text((20, 14), title, font=F, fill=(240, 240, 240))
    for i, n in enumerate(notes):
        d.text((20, Hd - 125 + i * 23), n, font=FS, fill=(205, 205, 205))
    # the room and (kit) the structure zone behind the panel faces
    if kit:
        for s in (1, -1):
            rect(10.34, 15.2, s * half, s * (half + STRUCT), fill=(55, 58, 66))
        # the slope's foot at 1.3 m and the ceiling's edge (the cove) in plan
        inset = 0.75 * W_SEC["slope_rise"]
        for s in (1, -1):
            a, b = P(10.34, s * (half - inset)), P(15.2, s * (half - inset))
            d.line([a, b], fill=(90, 110, 140), width=1)
        d.text(P(10.4, half - inset - 0.02), "okraj stropu (zkosení 1,3–2,1 m)", font=FS, fill=(110, 130, 160))
    rect(10.34, 15.2, -half, half, outline=(230, 230, 230), width=3)
    d.text(P(10.4, half + 0.32), "levobok", font=FS, fill=(160, 160, 160))
    d.text(P(10.4, -half - 0.06), "pravobok", font=FS, fill=(160, 160, 160))
    for name, (a, b, c, e), kind in furniture:
        if kind == "below":
            rect(a, b, c, e, outline=(110, 150, 190), width=2)
        elif kind == "wall":
            rect(a, b, c, e, fill=(150, 120, 70))
        else:
            rect(a, b, c, e, fill=(96, 96, 104), outline=(170, 170, 180), width=1)
        ty = (c + e) / 2 + 0.2 if kind != "below" else e - 0.05
        d.text(P(a + 0.05, ty), SHORT.get(name, name), font=FS, fill=(235, 235, 235) if kind != "below" else (120, 160, 200))
    for dr in doors:
        ax, (dx, dy), w = dr["axis"], dr["at"], dr["width"]
        if kit and ax == "y":
            # the cell's sliding door on its front, facing the aisle
            cell = next(f for f in furniture if f[0] == "Hygienická buňka")[1]
            dx, dy = (cell[0] + cell[1]) / 2, max(cell[2], cell[3])
        if ax == "x":
            a, b = P(dx - 0.06, dy + w / 2), P(dx + 0.06, dy - w / 2)
        else:
            a, b = P(dx - w / 2, dy + 0.06), P(dx + w / 2, dy - 0.06)
        d.rectangle([a, b], fill=(120, 200, 255))
    # the aisle where the bunk and the cell face each other
    cells = [f for f in furniture if f[0] == "Hygienická buňka"]
    bunks = [f for f in furniture if f[0] == "Lůžko"]
    if cells and bunks:
        c, bk = cells[0][1], bunks[0][1]
        ov = (max(c[0], bk[0]), min(c[1], bk[1]))
        free_y = (max(c[2], c[3]), min(bk[2], bk[3]))
        if ov[1] > ov[0]:
            a, b = P(ov[0], free_y[1]), P(ov[1], free_y[0])
            d.rectangle([a, b], outline=(120, 220, 140), width=2)
            d.text(P(ov[0] + 0.03, (free_y[0] + free_y[1]) / 2 + 0.1), "%.2f m" % (free_y[1] - free_y[0]), font=FS, fill=(140, 230, 150))
        else:
            d.text(P(12.2, 0.15), "ulička %.2f m (lůžko a buňka se nepřekrývají)" % (bk[2] - max(c[2], c[3])), font=FS, fill=(140, 230, 150))
    return img


def section_panel(half):
    """The cabin in section at x 13.5 (looking forward): the kit profile, the bunk and the cell, a 1.80 m walker."""
    Wd, Hd = int(4.2 * S) + 60, int(2.9 * S) + 120
    img = Image.new("RGB", (Wd, Hd), (24, 25, 28))
    d = ImageDraw.Draw(img)
    F = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 22)
    FS = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 16)
    ox, oy = Wd // 2, Hd - 50

    def P(y, z):                           # looking forward: port (+y) to the left
        return (ox - int(y * S), oy - int(z * S))

    d.text((14, 10), "Řez kajutou z kitu (x 13,5, pohled dopředu)", font=F, fill=(240, 240, 240))
    vt, rise, ceil = W_SEC["vertical_to"], W_SEC["slope_rise"], W_SEC["ceiling"]
    inset = 0.75 * rise
    for s in (1, -1):
        pts = [P(s * half, 0.1), P(s * half, vt), P(s * (half - inset), vt + rise), P(s * (half - inset), ceil)]
        d.line(pts, fill=(230, 230, 230), width=3)
        d.line([P(s * half, 0.0), P(s * (half - 0.1), 0.1)], fill=(230, 230, 230), width=2)
    d.line([P(half - inset, ceil), P(-(half - inset), ceil)], fill=(230, 230, 230), width=3)
    d.line([P(half + 0.2, 0), P(-half - 0.2, 0)], fill=(200, 200, 200), width=2)
    # bunk to port (0.85 deep, 0.7 high), the cell to starboard (1.0 deep, 2.3 high: up to the slope's foot it is
    # full depth, above it follows the slope)
    d.rectangle([P(half, 0.7), P(half - 0.85, 0.0)], fill=(96, 96, 104))
    d.text(P(half - 0.05, 0.62), "lůžko", font=FS, fill=(235, 235, 235))
    cell = [P(-half, 0.0), P(-half + 1.0, 0.0), P(-half + 1.0, 2.1), P(-(half - inset), 2.1), P(-half, vt)]
    d.polygon(cell, fill=(96, 96, 104))
    d.text(P(-half + 0.9, 1.2), "hygiena", font=FS, fill=(235, 235, 235))
    # headroom over the bunk under the slope, and the walker in the aisle
    d.text(P(half - 0.05, 1.55), "nad lůžkem 1,6 m\npod zkosením", font=FS, fill=(170, 190, 220))
    d.rounded_rectangle([P(0.28 - 0.1, 1.8), P(-0.28 - 0.1, 0.0)], radius=int(0.28 * S), outline=(120, 220, 140), width=2)
    d.text(P(0.2, 2.02), "chodec 1,80 m", font=FS, fill=(140, 230, 150))
    d.text(P(0.75, ceil + 0.2), "strop 2,3 m, šířka 1,8 m", font=FS, fill=(200, 200, 200))
    d.text(P(half + 0.15, -0.05), "3,0 m mezi líci panelů", font=FS, fill=(200, 200, 200))
    return img


def liner_section_panel(title, variant, half, cut, notes):
    """A section of the cabin (looking forward, port left) drawn into the real hull cut: variant 'W' (the kit's W walls,
    3.0 m) or 'liner' (a thin hull liner, the layout's 3.8 m room, a small chamfer at the ceiling)."""
    Wd, Hd = int(5.2 * S) + 40, int(3.6 * S) + 210
    img = Image.new("RGB", (Wd, Hd), (24, 25, 28))
    d = ImageDraw.Draw(img)
    F = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 22)
    FS = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 16)
    ox, oy = Wd // 2, Hd - 150

    def P(y, z):
        return (ox - int(y * S), oy - int(z * S))

    d.text((14, 10), title, font=F, fill=(240, 240, 240))
    for k, n in enumerate(notes):
        d.text((14, Hd - 70 + k * 21), n, font=FS, fill=(205, 205, 205))
    for a, b in cut:
        if abs(a[0]) < 2.6 and abs(b[0]) < 2.6:
            d.line([P(*a), P(*b)], fill=(235, 235, 235), width=3)
    ceil = 2.3
    if variant == "W":
        vt, rise = W_SEC["vertical_to"], W_SEC["slope_rise"]
        inset = 0.75 * rise
        for sgn in (1, -1):
            d.line([P(sgn * half, 0.1), P(sgn * half, vt), P(sgn * (half - inset), vt + rise), P(sgn * (half - inset), ceil)],
                   fill=(110, 170, 250), width=3)
            d.polygon([P(sgn * half, 0), P(sgn * (half + STRUCT), 0), P(sgn * (half + STRUCT), ceil + 0.1), P(sgn * (half - inset), ceil + 0.1),
                       P(sgn * (half - inset), vt + rise), P(sgn * half, vt)], outline=(80, 100, 140))
        d.line([P(half - inset, ceil), P(-(half - inset), ceil)], fill=(110, 170, 250), width=3)
        d.text(P(0.45, 0.35), "%.1f m mezi líci" % (2 * half), font=FS, fill=(140, 190, 255))
    else:
        ch = 0.22
        for sgn in (1, -1):
            d.line([P(sgn * half, 0.0), P(sgn * half, ceil - ch), P(sgn * (half - ch), ceil)], fill=(250, 170, 90), width=3)
            d.polygon([P(sgn * half, 0), P(sgn * (half + 0.15), 0), P(sgn * (half + 0.15), ceil + 0.1), P(sgn * (half - ch), ceil + 0.1),
                       P(sgn * (half - ch), ceil), P(sgn * half, ceil - ch)], outline=(140, 100, 60))
        d.line([P(half - ch, ceil), P(-(half - ch), ceil)], fill=(250, 170, 90), width=3)
        d.text(P(0.45, 0.35), "%.1f m mezi líci" % (2 * half), font=FS, fill=(255, 190, 120))
        d.text(P(0.9, ceil + 0.45), "nad stropem místo pro rozvody", font=FS, fill=(170, 170, 170))
    d.line([P(2.4, 0), P(-2.4, 0)], fill=(200, 200, 200), width=2)
    d.rounded_rectangle([P(0.28, 1.8), P(-0.28, 0.0)], radius=int(0.28 * S), outline=(120, 220, 140), width=2)
    return img


def main():
    import json as _json
    room, objs, doors = layout()
    now_f = [(o["name"], tuple(o["rect"]), "below" if o.get("below") else "floor") for o in objs]
    fit = _json.load(open(os.path.join(ROOT, "Saved", "HullFit", "Wayfarer_cabin.json"), encoding="utf-8"))
    cut = fit["cuts"]["12.5"]
    min_waist = min(s[1] for s in fit["stations"])
    min_head = min(s[2] for s in fit["stations"])
    planA = plan_panel("A: stěny W, kajuta 3,0 m",
                       ["Průřez kitu W (svisle do 1,3 m, zkosení 35°) i s konstrukcí 0,2 m",
                        "pojme nad kajutou nejvýš 3,0 m. Skříň a výdejník do stěny,",
                        "lůžko o 0,45 m dopředu pod zkosení, buňka stojí na podlaze."],
                       HALF, proposal(objs), doors, True)
    planB = plan_panel("B (doporučuji): obložení trupu, 3,8 m jako dnes",
                       ["Tenké obložení (0,1 m + mezera 0,05 m) podél trupu: kajuta zůstane",
                        "3,8 m a nábytek podle schváleného layoutu. Trup tu dovolí s obložením",
                        "%.2f m v pase a %.2f m ve výšce hlavy po celé délce kajuty." % (min_waist, min_head)],
                       1.9, now_f, doors, False)
    secA = liner_section_panel("Řez A (x 12,5)", "W", HALF, cut, ["Modrá: líc panelů W, čárkovaně konstrukce 0,2 m."])
    secB = liner_section_panel("Řez B (x 12,5)", "liner", 1.9, cut,
                               ["Oranžová: líc obložení, malé zkosení 0,22 m u stropu (jazyk kitu),",
                                "nad stropem 2,3 m zbývá ~0,8 m trupu pro rozvody a svítidla."])
    top_w = planA.width + planB.width + 20
    bot_w = secA.width + secB.width + 20
    Wt = max(top_w, bot_w)
    Ht = max(planA.height, planB.height) + max(secA.height, secB.height) + 20
    out = Image.new("RGB", (Wt, Ht), (24, 25, 28))
    out.paste(planA, (0, 0))
    out.paste(planB, (planA.width + 20, 0))
    y2 = max(planA.height, planB.height) + 20
    out.paste(secA, (0, y2))
    out.paste(secB, (secA.width + 20, y2))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out.save(OUT)
    print("CABINPLAN", OUT)


if __name__ == "__main__":
    main()
