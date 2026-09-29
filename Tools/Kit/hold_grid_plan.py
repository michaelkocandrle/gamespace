"""The Wayfarer hold from above: the cargo grid, the aisle and the door into the technical corridor, as laid out now
and as proposed with the thin hull liner (author's question, 28. 9. 2026: the door opens only 0.35 m onto the aisle,
the rest faces the grid's end 0.3 m away).

    python Tools/Kit/hold_grid_plan.py            -> Docs/Kit/hold_grid_plan_wayfarer.png

Layout metres (x forward, y to port); the numbers come from Wayfarer_layout.json (now) and hold_fit.py (the liner).
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "Docs", "Kit", "hold_grid_plan_wayfarer.png")
S = 110                                   # px per metre
SCU = 1.25


def layout():
    L = json.load(open(os.path.join(ROOT, "ArtSource", "Ships", "Wayfarer", "Design", "Wayfarer_layout.json"), encoding="utf-8"))
    room = next(r for r in L["rooms"] if r["id"] == "hold")
    grid = next(o for o in L["objects"] if o.get("room") == "hold" and "mřížka" in o["name"].lower())
    door = next(d for d in L["doors"] if abs(d["at"][0] - room["rect"][1]) < 0.01)
    below = [o for o in L["objects"] if o.get("room") == "hold" and o.get("below")]
    fixed = [o for o in L["objects"] if o.get("room") == "hold" and not o.get("below") and o is not grid]
    return room, grid, door, below, fixed


def panel(title, notes, room_y, grid, aisle, door, below, fixed, landing=None):
    x0, x1 = 0.2, 10.4
    W, H = int((x1 - x0) * S) + 40, int(4.6 * S) + 200
    img = Image.new("RGB", (W, H), (24, 25, 28))
    d = ImageDraw.Draw(img)
    F = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 26)
    FS = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 18)
    oy = 90 + int(2.3 * S)

    def P(x, y):                           # port (+y) up in the picture
        return (20 + int((x - x0) * S), oy - int(y * S))

    def rect(xa, xb, ya, yb, **kw):
        a, b = P(xa, yb), P(xb, ya)
        d.rectangle([a, b], **kw)

    d.text((20, 14), title, font=F, fill=(240, 240, 240))
    for i, n in enumerate(notes):
        d.text((20, H - 100 + i * 24), n, font=FS, fill=(205, 205, 205))
    # the room: walls (or the liner at container height), the bulkhead to the corridor, the ramp opening aft
    ry0, ry1 = room_y
    # the aisle first, then what is under the floor (outlines) and the fixed kit over it
    ay0, ay1 = aisle
    rect(1.0, 8.2, ay0, ay1, fill=(38, 52, 40))
    d.text(P(3.0, (ay0 + ay1) / 2 + 0.12), "ulička %.2f m" % (ay1 - ay0), font=FS, fill=(150, 210, 150))
    rect(1.0, 8.2, ry0, ry1, outline=(230, 230, 230), width=3)
    d.text(P(0.25, 0.3), "zadní\nrampa", font=FS, fill=(170, 170, 170))
    d.text(P(8.3, ry1 + 0.28), "přepážka k technické chodbě", font=FS, fill=(170, 170, 170))
    short = {"Kvantový pohon S1": "kvantový\npohon", "Nádrž kvantového paliva": "nádrž paliva"}
    for o in below:
        (a, b, c, e) = o["rect"]
        rect(a, b, c, e, outline=(110, 150, 190), width=2)
        d.text(P(a + 0.05, c + 0.45), short.get(o["name"], o["name"]) + "\n(pod podlahou)", font=FS, fill=(120, 160, 200))
    for o in fixed:
        (a, b, c, e) = o["rect"]
        rect(a, b, c, e, fill=(90, 90, 96))
    # the grid: 4 x 2 positions of 1.25 m
    gx0, gx1, gy0, gy1 = grid
    for i in range(4):
        for j in range(2):
            rect(gx0 + i * SCU + 0.02, gx0 + (i + 1) * SCU - 0.02, gy0 + j * SCU + 0.02, gy0 + (j + 1) * SCU - 0.02,
                 outline=(235, 140, 40), width=2)
    d.text(P(gx0 + 0.1, gy0 + 0.3), "mřížka 8 SCU  x %.2f–%.2f" % (gx0, gx1), font=FS, fill=(240, 160, 70))
    # the landing in front of the door
    if landing:
        rect(landing[0], landing[1], ry0 + 0.02, ry1 - 0.02, outline=(120, 200, 255), width=2)
        d.text(P(landing[0] + 0.03, ry0 + 0.75), "volno\n%.1f m" % (landing[1] - landing[0]), font=FS, fill=(140, 210, 255))
    # the door
    dy0, dy1 = door
    a, b = P(8.14, dy1), P(8.26, dy0)
    d.rectangle([a, b], fill=(120, 200, 255))
    d.text(P(8.28, dy1), "dveře\n%.2f–%.2f" % (dy0, dy1), font=FS, fill=(140, 210, 255))
    # the door's width projected into the room: which part meets the aisle, which the grid end
    gap = 8.2 - gx1
    overlap = max(0.0, min(dy1, ay1) - max(dy0, ay0))
    d.text(P(4.4, ry0 - 0.1), "od dveří: %.2f m do uličky, konec mřížky %.2f m před přepážkou" % (overlap, gap), font=FS, fill=(230, 230, 230))
    return img


def main():
    room, grid, door, below, fixed = layout()
    x0, x1, y0, y1 = room["rect"]
    g = grid["rect"]
    dy0, dy1 = door["at"][1] - door["width"] / 2, door["at"][1] + door["width"] / 2
    now = panel("Nyní (layout, stěny W)",
                ["Dveře do technické chodby (y %.2f–%.2f) ústí do uličky jen z %.2f m;" % (dy0, dy1, max(0, min(dy1, y1) - max(dy0, g[3]))),
                 "zbytek šířky dveří míří na konec mřížky %.2f m před přepážkou – plná mřížka zúží průchod na 0,3 m." % (x1 - g[1])],
                (y0, y1), (g[0], g[1], g[2], g[3]), (g[3], y1), (dy0, dy1), below, fixed)
    # the proposal: the thin liner widens the hold to 4.10 m at container height (hold_fit.py), the grid 0.3 m aft
    ly0, ly1 = -2.05, 2.05
    pg = (2.6, 7.6, ly0 + 0.05, ly0 + 0.05 + 2 * SCU)
    prop = panel("Návrh: tenké obložení (4,10 m ve výšce kontejnerů), mřížka o 0,3 m k rampě",
                 ["Před dveřmi 0,6 m volné podlahy přes celou šířku dveří: vyjdeš z chodby na volno, i když je mřížka plná;",
                  "ulička 1,55 m. Poklop kvantového pohonu (x 1,4–2,6) zůstává volný, mřížka začíná na jeho hraně."],
                 (ly0, ly1), pg, (pg[3], ly1), (dy0, dy1), below, fixed, landing=(7.6, 8.2))
    W = now.width + prop.width + 20
    out = Image.new("RGB", (W, max(now.height, prop.height)), (24, 25, 28))
    out.paste(now, (0, 0))
    out.paste(prop, (now.width + 20, 0))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out.save(OUT)
    print("HOLDPLAN", OUT)


if __name__ == "__main__":
    main()
