"""Do the kit's standard sections fit inside a ship's hull? (step 2 of the kit brief, author 26. 9. 2026)

    blender -b ArtSource/Ships/<Ship>/<Ship>_HS_Game.blend --python Tools/Kit/hull_fit_sections.py -- <Ship> [out.png]
    python Tools/Kit/hull_fit_sections.py --draw Saved/HullFit/<Ship>.json

Slices the hull (the exterior parts, not the interior) across the ship every 0.1 m along the decks' rooms and
checks each kit section's envelope against it: the panel faces plus the structure behind them (walls
structure_depth, floor structure under the floor plate, ceiling structure above the ceiling), centred on the
ship's centre line, at the deck's floor height. The envelope must stay liner_gap (5 cm) inside the hull
surface. The exterior is never changed - only measured. Prints HULLFIT {...} and draws the cut at the tightest
station of each room with the room's rectangle, section N and section W (layout coordinates: x from the aft
end, z from the main deck; the game blend is offset by (10.25, 0, 1.2)).
"""
import json
import math
import os
import sys

try:
    import bmesh
    import bpy
    from mathutils import Vector
except ImportError:          # drawing half, plain Python with PIL (Blender's Python has no PIL)
    bpy = None

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RULES = json.load(open(os.path.join(ROOT, "ArtSource", "Kit", "kit_rules.json"), encoding="utf-8"))
OFF = (10.25, 0.0, 1.2)                  # layout = game + OFF (hs_assemble_ship)
LINER_GAP = 0.05


def hull_bmesh(ship):
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    for ob in bpy.data.objects:
        n = ob.name
        if ob.type != "MESH" or not n.startswith("SM_Ship_%s" % ship) or "_Int" in n or "Interior" in n \
                or n.startswith(("UCX_", "SOCKET_")) or "Decals" in n or "Screens" in n or "Hologram" in n or "Gear" in n:
            continue
        # only the fuselage: pods, wings, fins, guns sit outside the cabin's width anyway and would hide it
        if not any(k in n for k in ("_Hull", "_Canopy")) and n != "SM_Ship_%s" % ship:
            continue
        me = ob.evaluated_get(dg).to_mesh()
        tmp = bmesh.new()
        tmp.from_mesh(me)
        tmp.transform(ob.matrix_world)
        m2 = bpy.data.meshes.new("_t")
        tmp.to_mesh(m2)
        tmp.free()
        bm.from_mesh(m2)
        bpy.data.meshes.remove(m2)
        ob.evaluated_get(dg).to_mesh_clear()
    bm.transform(__import__("mathutils").Matrix.Translation(Vector(OFF)))
    return bm


def slice_at(bm, x):
    """Segments (y, z) where the plane x cuts the hull triangles."""
    segs = []
    for f in bm.faces:
        vs = [v.co for v in f.verts]
        pts = []
        for a, b in zip(vs, vs[1:] + vs[:1]):
            da, db = a.x - x, b.x - x
            if (da <= 0 < db) or (db <= 0 < da):
                t = da / (da - db)
                p = a.lerp(b, t)
                pts.append((p.y, p.z))
        if len(pts) >= 2:
            segs.append((pts[0], pts[1]))
    return segs


def envelope(sec, width, floor_z):
    """Outer envelope polygon (y, z) of a section: faces + structure, closed."""
    z = RULES["zones"]
    sd, fs, cs = z["structure_depth"], z["floor_plate_thickness"] + z["floor_structure_depth"], z["ceiling_structure_depth"]
    w2 = width / 2
    inset = 0.75 * sec["slope_rise"]
    top = sec["vertical_to"] + sec["slope_rise"]
    right = [(w2 + sd, floor_z - fs), (w2 + sd, floor_z + sec["vertical_to"]), (w2 - inset + sd, floor_z + top),
             (w2 - inset + sd, floor_z + sec["ceiling"] + cs)]
    return right + [(-y, zz) for y, zz in reversed(right)]


def seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L < 1e-12 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def inside_hull(p, segs):
    """Ray to +z: odd crossings = inside."""
    px, py = p
    n = 0
    for (ay, az), (by, bz) in segs:
        if (ay <= px < by) or (by <= px < ay):
            zz = az + (px - ay) * (bz - az) / (by - ay)
            if zz > py:
                n += 1
    return n % 2 == 1


def clearance(poly, segs):
    """Smallest distance from the envelope's outline (sampled) to the hull; negative when it pokes outside."""
    worst = 1e9
    for a, b in zip(poly, poly[1:] + poly[:1]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(2, int(L / 0.02))
        for k in range(n + 1):
            p = (a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n)
            d = min(seg_dist(p, s[0], s[1]) for s in segs) if segs else 0.0
            worst = min(worst, d if inside_hull(p, segs) else -d)
    return worst


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    ship = args[0]
    out_png = args[1] if len(args) > 1 else os.path.join(ROOT, "Docs", "Kit", "hull_fit_%s.png" % ship.lower())
    layout = json.load(open(os.path.join(ROOT, "ArtSource", "Ships", ship, "Design", "%s_layout.json" % ship), encoding="utf-8"))
    bm = hull_bmesh(ship)
    secs = RULES["sections"]
    report = {}
    cuts = []
    for room in layout["rooms"]:
        x0, x1, y0, y1 = room["rect"]
        fz = room.get("floor_z", layout["decks"][room.get("deck", "main")]["floor_z"])
        room_w = y1 - y0
        # the cockpit tapers into the nose and gets its own dash and canopy frame; the kit's walls only run
        # behind the dash (kit_rules sections do not apply ahead of it)
        x_end = min(x1, room.get("kit_until_x", x1)) if room["id"] != "cockpit" else min(x1, 17.5)
        best = {}
        x = x0 + 0.05
        while x < x_end - 0.04:
            segs = slice_at(bm, x)
            if segs:
                row = {}
                for key in ("N", "W"):
                    row[key] = clearance(envelope(secs[key], secs[key]["width"], fz), segs) - LINER_GAP
                # the room itself with the W profile at its own width
                row["room"] = clearance(envelope(secs["W"], room_w, fz), segs) - LINER_GAP
                for k, v in row.items():
                    if k not in best or v < best[k][0]:
                        best[k] = (v, round(x, 2))
            x += 0.1
        report[room["id"]] = {k: {"margin_m": round(v[0], 3), "at_x": v[1]} for k, v in best.items()}
        # the widest W-profile room on the 0.3 m grid that fits at every station
        g = RULES["grid"]["plan"]
        w = math.floor(room_w / g + 1e-6) * g
        stations = []
        x = x0 + 0.05
        while x < x_end - 0.04:
            stations.append(slice_at(bm, x))
            x += 0.1
        while w >= 0.9 and stations:
            if all(not sg or clearance(envelope(secs["W"], w, fz), sg) - LINER_GAP >= 0 for sg in stations):
                break
            w -= g
        report[room["id"]]["max_width_on_grid"] = round(w, 2) if w >= 0.9 else None
        if best:
            worst_x = min(best.values())[1]
            cuts.append({"room": room, "floor_z": fz, "x": worst_x, "segs": slice_at(bm, worst_x)})
    print("HULLFIT " + json.dumps(report, ensure_ascii=False))
    data = os.path.join(ROOT, "Saved", "HullFit", "%s.json" % ship)
    os.makedirs(os.path.dirname(data), exist_ok=True)
    json.dump({"report": report, "cuts": cuts, "png": out_png}, open(data, "w", encoding="utf-8"), ensure_ascii=False)
    print("HULLFIT data", data, "- draw it: python Tools/Kit/hull_fit_sections.py --draw", data)


def draw(data_path):
    from PIL import Image, ImageDraw, ImageFont
    data = json.load(open(data_path, encoding="utf-8"))
    cuts, report, out_png, secs = data["cuts"], data["report"], data["png"], RULES["sections"]
    PX = 110
    F = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 18)
    FB = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 22)
    cw, ch = 620, 640
    img = Image.new("RGB", (cw * len(cuts) + 40, ch + 150), (24, 25, 28))
    d = ImageDraw.Draw(img)
    d.text((20, 12), "Řez trupem s průřezy kitu (bílá trup, šedá místnost z layoutu, oranžová N, modrá W; plná čára líc panelů, "
           "čárkovaně obálka s konstrukcí)", font=F, fill=(230, 230, 230))
    for i, cut in enumerate(cuts):
        room, fz, x, segs = cut["room"], cut["floor_z"], cut["x"], cut["segs"]
        ox, oy = 20 + i * cw + cw // 2, 110 + ch - 90
        def P(y, z):
            return (ox + y * PX, oy - z * PX)
        # grid 0.5 m
        for g in range(-6, 7):
            d.line([P(g * 0.5, -1.2), P(g * 0.5, 4.3)], fill=(40, 42, 48))
        for g in range(-2, 9):
            d.line([P(-3, g * 0.5), P(3, g * 0.5)], fill=(40, 42, 48))
        for a, b in segs:
            d.line([P(*a), P(*b)], fill=(235, 235, 235), width=3)
        x0, x1, y0, y1 = room["rect"]
        d.rectangle([P(y0, fz + 2.3)[0], P(y0, fz + 2.3)[1], P(y1, fz)[0], P(y1, fz)[1]], outline=(120, 124, 132), width=2)
        for key, col in (("N", (235, 120, 40)), ("W", (90, 170, 255))):
            sec = secs[key]
            w2 = sec["width"] / 2
            inset = 0.75 * sec["slope_rise"]
            top = sec["vertical_to"] + sec["slope_rise"]
            face = [(w2, fz), (w2, fz + sec["vertical_to"]), (w2 - inset, fz + top), (w2 - inset, fz + sec["ceiling"])]
            face = face + [(-y, z) for y, z in reversed(face)]
            d.line([P(*p) for p in face] + [P(*face[0])], fill=col, width=3)
            env = envelope(sec, sec["width"], fz)
            pts = [P(*p) for p in env] + [P(*env[0])]
            for a, b in zip(pts, pts[1:]):
                for k in range(0, 10, 2):
                    d.line([(a[0] + (b[0] - a[0]) * k / 10, a[1] + (b[1] - a[1]) * k / 10),
                            (a[0] + (b[0] - a[0]) * (k + 1) / 10, a[1] + (b[1] - a[1]) * (k + 1) / 10)], fill=col, width=2)
        r = report[room["id"]]
        d.text((ox - cw // 2 + 10, 60), "%s (x = %.1f m, podlaha %.2f)" % (room["name"], x, fz), font=FB, fill=(240, 240, 240))
        yy = oy + 20
        mw = r.get("max_width_on_grid")
        d.text((ox - cw // 2 + 10, 88), "největší šířka místnosti na mřížce: %s" % ("%.1f m" % mw if mw else "průřezy kitu se nevejdou"),
               font=F, fill=(230, 200, 120))
        for k, label in (("N", "N 1,2 m"), ("W", "W 2,4 m"), ("room", "místnost %.1f m" % (y1 - y0))):
            v = r.get(k)
            if v:
                ok = v["margin_m"] >= 0
                d.text((ox - cw // 2 + 10, yy), "%s: rezerva %+.2f m (nejhorší x = %.1f)" % (label, v["margin_m"], v["at_x"]), font=F,
                       fill=(140, 220, 140) if ok else (255, 110, 90))
                yy += 24
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    img.save(out_png)
    print("HULLFIT png", out_png)


if __name__ == "__main__":
    if bpy is None:
        draw(sys.argv[sys.argv.index("--draw") + 1])
    else:
        main()
