"""Does a ship's cargo grid plus its aisle fit inside the hull with a thin hull liner? (Wayfarer, author 28. 9. 2026)

    blender -b ArtSource/Ships/<Ship>/<Ship>_HS_Game.blend --python Tools/Kit/hold_fit.py -- <Ship>
    python Tools/Kit/hold_fit.py --draw Saved/HullFit/<Ship>_hold.json

The kit's W walls (structure 0.2 m) leave the Wayfarer's hold 3.0 m wide at most (hull_fit_sections.py); the author
prefers a thin liner along the hull (exposed frames are fine). This measures what that liner really leaves - not at
the widest point of the cut but over the containers' height and, for the aisle, up to head height - at every 0.1 m of
the hold. The hull is measured from its skin inwards: LINER_GAP + LINER_DEPTH (the liner with its frames). Layout:
the grid against the starboard side (layout object "Nákladová mřížka", its x range), the aisle along port.
Prints HOLDFIT {...} and writes the data for --draw (the tightest stations with the containers and the aisle).
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCU = 1.25                  # container edge (m)
CARGO_CLEAR = 0.05          # over and beside the containers
AISLE = 1.25                # the design's aisle width (Wayfarer_Design.md: capsule 0.84 m)
HEAD = 2.0                  # clear height over the aisle (doors 2.05 m)
LINER_GAP, LINER_DEPTH = 0.05, 0.10
ROWS_ACROSS = 2             # 8 SCU = 4 x 2

try:
    import bmesh
    import bpy
except ImportError:
    bpy = None


def _crossings(segs, z):
    """y where the horizontal line at z crosses the cut's segments."""
    out = []
    for (ya, za), (yb, zb) in segs:
        if (za <= z < zb) or (zb <= z < za):
            out.append(ya + (z - za) * (yb - ya) / (zb - za))
    return out


def _inner(segs, z):
    """The hull's inside at height z: the crossings nearest the centre line on each side (port +y, starboard -y)."""
    ys = _crossings(segs, z)
    port = [y for y in ys if y > 0.0]
    stbd = [y for y in ys if y < 0.0]
    if not port or not stbd:
        return None
    return min(port), max(stbd)


def measure():
    sys.path.insert(0, os.path.join(ROOT, "Tools", "Blender"))
    sys.path.insert(0, HERE)
    import check_ship_geometry as geo
    import hull_fit_kit_rooms as hk
    ship = sys.argv[sys.argv.index("--") + 1:][0]
    recipe = json.load(open(os.path.join(ROOT, "ArtSource", "Ships", ship, "HardSurface", "%s_hs.json" % ship), encoding="utf-8"))
    layout = json.load(open(os.path.join(ROOT, "ArtSource", "Ships", ship, "Design", "%s_layout.json" % ship), encoding="utf-8"))
    off = recipe["assemble"]["offset"]
    hold = next(r for r in layout["rooms"] if r["id"] == "hold")
    grid = next(o for o in layout["objects"] if o.get("room") == "hold" and "mřížka" in o["name"])
    fz = hold.get("floor_z", 0.0)
    hull = geo.world_bm(geo.obj(ship, ""))
    inset = LINER_GAP + LINER_DEPTH
    stations = []
    x = hold["rect"][0] + 0.05
    while x < hold["rect"][1] - 0.04:
        segs = [((a[0], a[1] - off[2]), (b[0], b[1] - off[2])) for a, b in hk._slice(hull, x + off[0])]
        in_grid = grid["rect"][0] <= x <= grid["rect"][1]
        cargo_w, head_port, worst_z = 1e9, 1e9, None
        stbd_cargo = -1e9
        z = fz + 0.02
        while z <= fz + HEAD:
            r = _inner(segs, z)
            if r:
                port, stbd = r[0] - inset, r[1] + inset
                if z <= fz + SCU + CARGO_CLEAR:
                    if port - stbd < cargo_w:
                        cargo_w, worst_z = port - stbd, z
                    stbd_cargo = max(stbd_cargo, stbd)      # the grid stands against the tightest starboard point
                head_port = min(head_port, port)
            z += 0.05
        # the aisle starts where the containers end (grid against starboard); over the containers' height it
        # needs AISLE between them and the port liner, above them up to HEAD too
        grid_edge = stbd_cargo + ROWS_ACROSS * SCU + CARGO_CLEAR
        aisle = head_port - grid_edge
        stations.append({"x": round(x, 2), "in_grid": in_grid, "width_cargo_height": round(cargo_w, 3),
                         "worst_z": round(worst_z, 2) if worst_z else None, "stbd_liner": round(stbd_cargo, 3),
                         "port_liner_to_head": round(head_port, 3), "aisle_left": round(aisle, 3),
                         "segs": segs})
        x += 0.1
    need = ROWS_ACROSS * SCU + CARGO_CLEAR + AISLE
    g = [s for s in stations if s["in_grid"]]
    report = {"ship": ship, "liner_m": inset, "need_m": need,
              "grid_x": grid["rect"][:2],
              "min_width_cargo_height": min(s["width_cargo_height"] for s in g),
              "min_aisle_with_8scu": min(s["aisle_left"] for s in g),
              "fits_8scu_full_aisle": all(s["aisle_left"] >= AISLE for s in g),
              "aisle_rest_of_hold": min(s["port_liner_to_head"] - s["stbd_liner"] for s in stations if not s["in_grid"])}
    print("HOLDFIT " + json.dumps(report))
    data = os.path.join(ROOT, "Saved", "HullFit", "%s_hold.json" % ship)
    os.makedirs(os.path.dirname(data), exist_ok=True)
    json.dump({"report": report, "stations": stations,
               "png": os.path.join(ROOT, "Docs", "Kit", "hold_fit_%s.png" % ship.lower())}, open(data, "w", encoding="utf-8"))
    print("HOLDFIT data", data)


def draw(data_path):
    from PIL import Image, ImageDraw, ImageFont
    sys.path.insert(0, HERE)
    from hull_fit_kit_rooms import clip_y
    data = json.load(open(data_path, encoding="utf-8"))
    rep = data["report"]
    g = [s for s in data["stations"] if s["in_grid"]]
    picks = sorted(g, key=lambda s: s["aisle_left"])[:1]
    picks += [min(g, key=lambda s: abs(s["x"] - (rep["grid_x"][0] + rep["grid_x"][1]) / 2))]
    picks += [max(g, key=lambda s: s["x"])]
    picks = sorted({s["x"]: s for s in picks}.values(), key=lambda s: s["x"])
    F = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 18)
    FB = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 22)
    PX, cw, ch = 125, 640, 600
    img = Image.new("RGB", (cw * len(picks) + 40, ch + 200), (24, 25, 28))
    d = ImageDraw.Draw(img)
    verdict = "8 SCU + ulička %.2f m se vejde" % AISLE if rep["fits_8scu_full_aisle"] else \
        "8 SCU + ulička %.2f m se NEVEJDE (ulička nejvýš %.2f m)" % (AISLE, rep["min_aisle_with_8scu"])
    d.text((20, 12), "Nákladový prostor s tenkým obložením trupu (%.2f m: mezera %.2f + obložení se žebry %.2f): %s" % (
        rep["liner_m"], LINER_GAP, LINER_DEPTH, verdict), font=FB, fill=(235, 235, 235))
    d.text((20, 44), "Potřeba napříč: 2 × kontejner 1,25 m + %.2f m vůle + ulička %.2f m = %.2f m ve výšce kontejnerů; ulička "
           "volná do %.1f m. Nejmenší šířka ve výšce kontejnerů (x %.1f–%.1f): %.2f m." % (
               CARGO_CLEAR, AISLE, rep["need_m"], HEAD, rep["grid_x"][0], rep["grid_x"][1], rep["min_width_cargo_height"]),
           font=F, fill=(175, 180, 190))
    for i, s in enumerate(picks):
        ox, oy = 20 + i * cw + cw // 2, 110 + ch - 60
        P = lambda y, z: (ox - y * PX, oy - z * PX)          # port (+y) drawn on the left, looking forward
        for gy in range(-10, 11):
            d.line([P(gy * 0.25, -0.5), P(gy * 0.25, 3.3)], fill=(38, 40, 46))
        for gz in range(-2, 14):
            d.line([P(-2.4, gz * 0.25), P(2.4, gz * 0.25)], fill=(38, 40, 46))
        lim = (cw / 2 - 4) / PX
        for a, b in s["segs"]:
            c = clip_y(a, b, lim)
            if c:
                d.line([P(*c[0]), P(*c[1])], fill=(235, 235, 235), width=3)
        # liner lines (starboard at the grid's tightest point, port to head height)
        d.line([P(s["stbd_liner"], 0.0), P(s["stbd_liner"], SCU + CARGO_CLEAR)], fill=(150, 150, 160), width=2)
        d.line([P(s["port_liner_to_head"], 0.0), P(s["port_liner_to_head"], HEAD)], fill=(150, 150, 160), width=2)
        # containers against the starboard liner, the aisle after them
        y0 = s["stbd_liner"]
        for k in range(ROWS_ACROSS):
            a, b = y0 + k * SCU, y0 + (k + 1) * SCU
            d.rectangle([P(b, SCU)[0], P(b, SCU)[1], P(a, 0.0)[0], P(a, 0.0)[1]], outline=(240, 140, 40), width=3)
        ay0 = y0 + ROWS_ACROSS * SCU + CARGO_CLEAR
        ay1 = ay0 + AISLE
        ok = s["aisle_left"] >= AISLE
        col = (95, 200, 130) if ok else (235, 90, 80)
        d.rectangle([P(ay1, HEAD)[0], P(ay1, HEAD)[1], P(ay0, 0.0)[0], P(ay0, 0.0)[1]], outline=col, width=3)
        d.text((ox - cw // 2 + 10, 80), "x = %.1f m" % s["x"], font=FB, fill=(240, 240, 240))
        d.text((ox - cw // 2 + 10, 108), "šířka ve výšce kontejnerů %.2f m, ulička %.2f m" % (
            s["width_cargo_height"], s["aisle_left"]), font=F, fill=col)
    d.text((20, ch + 160), "Bílá trup, šedá líc tenkého obložení, oranžová kontejnery 1,25 m u pravoboku, zelená/červená ulička "
           "%.2f m × %.1f m u levoboku. Pohled dopředu: levobok vlevo." % (AISLE, HEAD), font=F, fill=(175, 180, 190))
    img.save(data["png"])
    print("HOLDFIT png", data["png"])


if __name__ == "__main__":
    if "--draw" in sys.argv:
        draw(sys.argv[sys.argv.index("--draw") + 1])
    elif bpy is not None:
        measure()
