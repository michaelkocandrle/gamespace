"""Cuts through a ship's hull with the kit rooms' real parts inside (Wayfarer pilot corridor, 28. 9. 2026).

    blender -b ArtSource/Ships/<Ship>/<Ship>_HS_Game.blend --python Tools/Kit/hull_fit_kit_rooms.py -- <Ship> [x ...]
    python Tools/Kit/hull_fit_kit_rooms.py --draw Saved/HullFit/<Ship>_kit_rooms.json

hull_fit_sections.py checks the kit's section envelopes against the hull; this cuts the parts themselves, placed
as the game places them (check_ship_geometry.add_kit_rooms = Tools/Assets/kit_rooms.py), at stations across each kit
room (layout x; default: every 0.3 m), with the rest of the interior and the hull. Reports the smallest gap between a
kit part and the hull's inside per station (negative = a part pokes out, the silhouette would have to change) and
draws the tightest stations. The exterior is only measured.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

try:
    import bmesh
    import bpy
except ImportError:
    bpy = None


def _slice(bm, x):
    segs = []
    for f in bm.faces:
        vs = [v.co for v in f.verts]
        pts = []
        for a, b in zip(vs, vs[1:] + vs[:1]):
            da, db = a.x - x, b.x - x
            if (da <= 0 < db) or (db <= 0 < da):
                p = a.lerp(b, da / (da - db))
                pts.append((round(p.y, 4), round(p.z, 4)))
        if len(pts) >= 2:
            segs.append((pts[0], pts[1]))
    return segs


def _seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L < 1e-12 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def _inside(p, segs):
    n = 0
    for (ay, az), (by, bz) in segs:
        if (ay <= p[0] < by) or (by <= p[0] < ay):
            if az + (p[0] - ay) * (bz - az) / (by - ay) > p[1]:
                n += 1
    return n % 2 == 1


def measure():
    sys.path.insert(0, os.path.join(ROOT, "Tools", "Blender"))
    import check_ship_geometry as geo
    args = sys.argv[sys.argv.index("--") + 1:]
    ship = args[0]
    recipe = json.load(open(os.path.join(ROOT, "ArtSource", "Ships", ship, "HardSurface", "%s_hs.json" % ship), encoding="utf-8"))
    layout = json.load(open(os.path.join(ROOT, "ArtSource", "Ships", ship, "Design", "%s_layout.json" % ship), encoding="utf-8"))
    off = recipe["assemble"]["offset"]
    geo.add_kit_rooms(ship, recipe)
    mods = recipe["interior"]["kit_modules"]
    rooms = {r["id"]: r for r in layout["rooms"]}
    stations = [float(a) for a in args[1:]]
    if not stations:
        for rid in mods["rooms"]:
            x0, x1 = rooms[rid]["rect"][:2]
            x = x0 + 0.15
            while x < x1 - 0.05:
                stations.append(round(x, 3))
                x += 0.3
    kit = geo.world_bm(geo.obj(ship, "_InteriorKitMod"))
    hull = geo.world_bm(geo.obj(ship, ""))
    inter = geo.world_bm(geo.obj(ship, "_Interior"))
    cuts = []
    for x in stations:
        gx = x + off[0]                                    # layout -> the game blend
        hs, ks, isg = _slice(hull, gx), _slice(kit, gx), _slice(inter, gx)
        # the parts' outline points against the hull: distance to the hull's inside, negative when outside it
        worst = None
        for a, b in ks:
            for p in (a, b):
                d = min(_seg_dist(p, s[0], s[1]) for s in hs) if hs else 0.0
                d = d if _inside(p, hs) else -d
                if worst is None or d < worst[0]:
                    worst = (round(d, 3), [round(p[0], 3), round(p[1] - off[2], 3)])
        # back to layout (y as the design, z from the deck) for the drawing
        tl = lambda segs: [[[a[0], a[1] - off[2]], [b[0], b[1] - off[2]]] for a, b in segs]
        cuts.append({"x": x, "hull": tl(hs), "kit": tl(ks), "interior": tl(isg),
                     "min_gap_m": worst[0] if worst else None, "at": worst[1] if worst else None})
    report = {"ship": ship, "rooms": mods["rooms"], "stations": [(c["x"], c["min_gap_m"]) for c in cuts]}
    print("HULLFITKIT " + json.dumps(report))
    data = os.path.join(ROOT, "Saved", "HullFit", "%s_kit_rooms.json" % ship)
    os.makedirs(os.path.dirname(data), exist_ok=True)
    json.dump({"report": report, "cuts": cuts, "png": os.path.join(ROOT, "Docs", "Kit", "hull_fit_%s_kit_rooms.png" % ship.lower())},
              open(data, "w", encoding="utf-8"))
    print("HULLFITKIT data", data)


def draw(data_path):
    from PIL import Image, ImageDraw, ImageFont
    data = json.load(open(data_path, encoding="utf-8"))
    cuts = sorted(data["cuts"], key=lambda c: c["min_gap_m"])[:3]
    cuts.sort(key=lambda c: c["x"])
    F = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 18)
    FB = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 22)
    PX, cw, ch = 130, 640, 640
    img = Image.new("RGB", (cw * len(cuts) + 40, ch + 170), (24, 25, 28))
    d = ImageDraw.Draw(img)
    d.text((20, 12), "Řez trupem Wayfareru se skutečnými díly kitu technické chodby (bílá trup, oranžová díly kitu, šedá zbytek "
           "interiéru; souřadnice layoutu)", font=F, fill=(230, 230, 230))
    allx = ", ".join("x %.2f: %+.3f m" % (x, g) for x, g in data["report"]["stations"])
    d.text((20, 38), "Nejmenší mezera díl kitu – vnitřek trupu po stanicích: " + allx, font=F, fill=(170, 175, 185))
    for i, c in enumerate(cuts):
        ox, oy = 20 + i * cw + cw // 2, 130 + ch - 110
        P = lambda y, z: (ox + y * PX, oy - z * PX)
        for g in range(-8, 9):
            d.line([P(g * 0.25, -0.6), P(g * 0.25, 3.4)], fill=(38, 40, 46))
        for g in range(-2, 14):
            d.line([P(-2.0, g * 0.25), P(2.0, g * 0.25)], fill=(38, 40, 46))
        for a, b in c["interior"]:
            d.line([P(*a), P(*b)], fill=(95, 98, 106), width=1)
        for a, b in c["kit"]:
            d.line([P(*a), P(*b)], fill=(240, 140, 40), width=2)
        for a, b in c["hull"]:
            d.line([P(*a), P(*b)], fill=(240, 240, 240), width=3)
        ok = c["min_gap_m"] is not None and c["min_gap_m"] >= 0.0
        d.text((ox - cw // 2 + 10, 80), "Stanice x = %.2f m" % c["x"], font=FB, fill=(240, 240, 240))
        d.text((ox - cw // 2 + 10, 108), "nejmenší mezera kit – trup: %+.3f m" % c["min_gap_m"], font=F,
               fill=(120, 220, 140) if ok else (240, 90, 80))
        if c["at"]:
            px, py = P(*c["at"])
            d.ellipse([px - 6, py - 6, px + 6, py + 6], outline=(120, 220, 140) if ok else (240, 90, 80), width=2)
    img.save(data["png"])
    print("HULLFITKIT png", data["png"])


if __name__ == "__main__":
    if "--draw" in sys.argv:
        draw(sys.argv[sys.argv.index("--draw") + 1])
    elif bpy is not None:
        measure()
