"""Generic 2D design sheets for a ship layout with an "exterior" block (called by draw_ship_design.py).

Writes next to the layout JSON:
  <Ship>_exterior.png       general arrangement: top, side (from starboard) and front, to scale, with
                            the overall length / beam / height and callouts
  <Ship>_deck_<id>.png      one plan per deck (draw_ship_design.draw_deck)
  <Ship>_cutaway.png        side section on the centre line: rooms, objects with a "z" range, lines
  guides/<Ship>_mask_<view>.png   white-on-black silhouettes (front, side, top) in the conventions of
                            Tools/Blender/silhouette_compare.py; they become the concept-image guides
                            (silhouette_compare.py guide --mask ...) and the reference for the 3D model.
Prints one JSON line SHIP_SHEETS with the measured overall dimensions, which must match <Ship>_spec.json.
"""
import json
import math
import os

from PIL import Image, ImageDraw

import draw_ship_design as dsd
from draw_ship_design import (ACCENT, BG, DIM, DOOR, GRID, HULL, MARGIN, PX, TEXT, WALL, ZONES,
                              centred, font, lighter, zone_key)

EPX = 48          # exterior sheet, pixels per metre
MASK_PX = 40      # silhouette masks, pixels per metre
KIND_FILL = {
    "hull": (40, 52, 66), "wing": (48, 60, 74), "engine": (58, 58, 64), "fin": (52, 64, 78),
    "glass": (58, 118, 150), "gear": (92, 98, 108), "weapon": (104, 106, 116), "nozzle": (200, 110, 60),
}
BEHIND = ("engine", "wing", "fin", "weapon", "gear", "nozzle")


def part_polys(part, view):
    """Polygons of one exterior part in view coordinates, mirrored copy included."""
    if "circle" in part:
        cx, cy, r = part["circle"]
        base = [[(cx + r * math.cos(t * math.pi / 24), cy + r * math.sin(t * math.pi / 24)) for t in range(48)]]
    else:
        base = [[tuple(v) for v in part["poly"]]]
    if part.get("mirror") and view in ("top", "front"):
        if view == "top":
            base.append([(x, -y) for x, y in base[0]])
        else:
            base.append([(-u, z) for u, z in base[0]])
    return base


def view_bounds(parts, view):
    pts = [v for p in parts for poly in part_polys(p, view) for v in poly]
    xs, ys = [v[0] for v in pts], [v[1] for v in pts]
    return min(xs), max(xs), min(ys), max(ys)


def overall_dims(ext):
    sx0, sx1, sz0, sz1 = view_bounds(ext["side"], "side")
    tx0, tx1, ty0, ty1 = view_bounds(ext["top"], "top")
    fu0, fu1, fz0, fz1 = view_bounds(ext["front"], "front")
    return {"length_m": round(max(sx1, tx1) - min(sx0, tx0), 2), "beam_m": round(max(ty1 - ty0, fu1 - fu0), 2),
            "height_m": round(max(sz1 - sz0, fz1 - fz0), 2),
            "per_view": {"side_LxH": [round(sx1 - sx0, 2), round(sz1 - sz0, 2)],
                         "top_LxB": [round(tx1 - tx0, 2), round(ty1 - ty0, 2)],
                         "front_BxH": [round(fu1 - fu0, 2), round(fz1 - fz0, 2)]}}


def dim_line(draw, a, b, text, vertical=False):
    draw.line([a, b], fill=DIM, width=2)
    for q in (a, b):
        if vertical:
            draw.line([(q[0] - 8, q[1]), (q[0] + 8, q[1])], fill=DIM, width=2)
        else:
            draw.line([(q[0], q[1] - 8), (q[0], q[1] + 8)], fill=DIM, width=2)
    f = font(20, True)
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    w = f.getlength(text)
    if vertical:
        draw.rectangle([mx - w / 2 - 6, my - 13, mx + w / 2 + 6, my + 13], fill=BG)
    else:
        draw.rectangle([mx - w / 2 - 6, my - 13, mx + w / 2 + 6, my + 13], fill=BG)
    centred(draw, (mx, my), text, f, TEXT)


def draw_parts(d, parts, view, to_px, outline_w=3):
    for part in parts:
        fill = KIND_FILL[part["kind"]]
        for poly in part_polys(part, view):
            d.polygon([to_px(*v) for v in poly], fill=fill, outline=lighter(fill, 0.55), width=outline_w)


def callouts(d, parts, view, to_px):
    f = font(18, True)
    for part in parts:
        if "label" not in part:
            continue
        poly = part_polys(part, view)[0]
        cx = sum(v[0] for v in poly) / len(poly)
        cy = sum(v[1] for v in poly) / len(poly)
        lx, ly = to_px(*part["label_at"])
        d.line([(lx, ly), to_px(cx, cy)], fill=ACCENT, width=1)
        d.ellipse([to_px(cx, cy)[0] - 3, to_px(cx, cy)[1] - 3, to_px(cx, cy)[0] + 3, to_px(cx, cy)[1] + 3], fill=ACCENT)
        w = f.getlength(part["label"])
        d.rectangle([lx - w / 2 - 5, ly - 12, lx + w / 2 + 5, ly + 12], fill=BG, outline=ACCENT)
        centred(d, (lx, ly), part["label"], f, TEXT)


def draw_exterior(layout, name, out_path):
    ext = layout["exterior"]
    dims = overall_dims(ext)
    tx0, tx1, ty0, ty1 = view_bounds(ext["top"], "top")
    sx0, sx1, sz0, sz1 = view_bounds(ext["side"], "side")
    fu0, fu1, fz0, fz1 = view_bounds(ext["front"], "front")
    x0, x1 = min(tx0, sx0) - 1.5, max(tx1, sx1) + 3.5
    ytop0, ytop1 = ty0 - 1.2, ty1 + 1.2
    z0, z1 = min(sz0, fz0) - 1.4, max(sz1, fz1) + 1.2
    u0, u1 = fu0 - 1.4, fu1 + 1.4
    head = 130
    top_h = (ytop1 - ytop0) * EPX
    side_h = (z1 - z0) * EPX
    left_w = (x1 - x0) * EPX
    front_w = (u1 - u0) * EPX
    W = int(MARGIN * 3 + left_w + front_w)
    H = int(head + MARGIN * 2 + top_h + side_h + 140)
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    oy_top = head + MARGIN
    oy_side = oy_top + top_h + 60
    ox_front = MARGIN * 2 + left_w

    def p_top(x, y):
        return (MARGIN + (x - x0) * EPX, oy_top + (ytop1 - y) * EPX)

    def p_side(x, z):
        return (MARGIN + (x - x0) * EPX, oy_side + (z1 - z) * EPX)

    def p_front(u, z):
        return (ox_front + (u - u0) * EPX, oy_side + (z1 - z) * EPX)

    for fn, a0, a1, b0, b1 in ((p_top, x0, x1, ytop0, ytop1), (p_side, x0, x1, z0, z1), (p_front, u0, u1, z0, z1)):
        for a in range(math.ceil(a0), math.floor(a1) + 1):
            d.line([fn(a, b0), fn(a, b1)], fill=GRID)
        for b in range(math.ceil(b0), math.floor(b1) + 1):
            d.line([fn(a0, b), fn(a1, b)], fill=GRID)
    gz = layout.get("sheet", {}).get("ground_z")
    if gz is not None:
        d.line([p_side(x0, gz), p_side(x1, gz)], fill=(90, 80, 60), width=3)
        d.line([p_front(u0, gz), p_front(u1, gz)], fill=(90, 80, 60), width=3)
    draw_parts(d, ext["top"], "top", p_top)
    draw_parts(d, ext["side"], "side", p_side)
    draw_parts(d, ext["front"], "front", p_front)
    callouts(d, ext["top"], "top", p_top)
    callouts(d, ext["side"], "side", p_side)
    callouts(d, ext["front"], "front", p_front)
    # Overall dimensions.
    dim_line(d, p_side(sx0, z0 + 0.5), p_side(sx1, z0 + 0.5), "délka %.1f m" % dims["length_m"])
    dim_line(d, p_top(tx1 + 2.7, ty0), p_top(tx1 + 2.7, ty1), "šířka %.1f m" % (ty1 - ty0), vertical=True)
    dim_line(d, p_front(u1 - 0.6, fz0), p_front(u1 - 0.6, fz1), "výška %.1f m" % (fz1 - fz0), vertical=True)
    ft = font(24, True)
    d.text((MARGIN, oy_top - 34), "POHLED SHORA (levobok nahoře)", font=ft, fill=ACCENT)
    d.text((MARGIN, oy_side - 34), "POHLED Z BOKU (ze pravoboku)", font=ft, fill=ACCENT)
    d.text((ox_front, oy_side - 34), "POHLED ZEPŘEDU", font=ft, fill=ACCENT)
    ax, ay = p_top(tx1 + 0.3, 0)
    d.polygon([(ax, ay - 12), (ax + 22, ay), (ax, ay + 12)], fill=ACCENT)
    d.text((MARGIN, 26), "%s – exteriér, celkové uspořádání" % name, font=font(44, True), fill=TEXT)
    d.text((MARGIN, 82), "%s · 1 m = %d px · s podvozkem venku · zem hnědá čára" % (
        layout.get("sheet", {}).get("subtitle", name), EPX), font=font(20), fill=DIM)
    # Kind key.
    x, y = MARGIN, H - 60
    names = {"hull": "trup", "glass": "sklo", "engine": "motor", "wing": "křídlo", "fin": "ploutev / kryt",
             "weapon": "zbraně", "gear": "podvozek", "nozzle": "tryska"}
    for k, c in KIND_FILL.items():
        d.rectangle([x, y, x + 26, y + 18], fill=c, outline=WALL)
        d.text((x + 34, y - 2), names[k], font=font(19), fill=TEXT)
        x += 60 + font(19).getlength(names[k])
    img.save(out_path)
    print("wrote", out_path, img.size)
    return dims


def write_masks(layout, name, out_dir):
    ext = layout["exterior"]
    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    for view in ("front", "side", "top"):
        a0, a1, b0, b1 = view_bounds(ext[view], view)
        pad = 1.0
        w = int((a1 - a0 + 2 * pad) * MASK_PX)
        h = int((b1 - b0 + 2 * pad) * MASK_PX)
        img = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(img)

        def px(a, b):
            return ((a - a0 + pad) * MASK_PX, (b1 - b + pad) * MASK_PX)

        for part in ext[view]:
            for poly in part_polys(part, view):
                d.polygon([px(*v) for v in poly], fill=255)
        paths[view] = os.path.join(out_dir, "%s_mask_%s.png" % (name, view))
        img.save(paths[view])
    return paths


def draw_cutaway(layout, name, out_path):
    sheet = layout.get("sheet", {})
    x0, x1, z0, z1 = sheet["cutaway_extent"]
    cut = layout.get("cutaway", {})
    ext = layout["exterior"]
    w = int((x1 - x0) * PX) + 2 * MARGIN
    h = int((z1 - z0) * PX) + 2 * MARGIN
    head = 120
    img = Image.new("RGB", (w, h + head + 60), BG)
    d = ImageDraw.Draw(img)

    def p(x, z):
        return (MARGIN + (x - x0) * PX, head + MARGIN + (z1 - z) * PX)

    for x in range(math.ceil(x0), math.floor(x1) + 1):
        d.line([p(x, z0), p(x, z1)], fill=GRID)
    for z in range(math.ceil(z0), math.floor(z1) + 1):
        d.line([p(x0, z), p(x1, z)], fill=GRID)
    if "ground_z" in sheet:
        d.line([p(x0, sheet["ground_z"]), p(x1, sheet["ground_z"])], fill=(90, 80, 60), width=3)
    # Everything outside the pressure hull, dimmed, then the hull.
    for part in ext["side"]:
        if part["kind"] in BEHIND:
            for poly in part_polys(part, "side"):
                c = lighter(BG, 0.12) if part["kind"] != "nozzle" else KIND_FILL["nozzle"]
                d.polygon([p(*v) for v in poly], fill=c, outline=lighter(BG, 0.3), width=2)
    hulls = [poly for part in ext["side"] if part["kind"] == "hull" for poly in part_polys(part, "side")]
    for poly in hulls:
        d.polygon([p(*v) for v in poly], fill=(22, 30, 40))
    before = img.copy()
    mask = Image.new("L", img.size, 0)
    for poly in hulls:
        ImageDraw.Draw(mask).polygon([p(*v) for v in poly], fill=255)
    rooms = layout["rooms"]
    for r in rooms:
        if not (r["rect"][2] <= 0.0 <= r["rect"][3]):
            continue
        deck = layout["decks"][r["deck"]]
        za = r.get("floor_z", deck["floor_z"])
        zb = deck["floor_z"] + deck["clear_height"]
        d.rectangle([*p(r["rect"][0], zb), *p(r["rect"][1], za)], fill=dsd.zone_of(r["id"], rooms), outline=WALL, width=3)
    # Objects with a height, numbered like the deck plans (per deck, list order).
    numbers = {}
    for deck_id in layout["decks"]:
        k = 0
        for o in layout["objects"]:
            if next(rr for rr in rooms if rr["id"] == o["room"])["deck"] == deck_id:
                k += 1
                numbers[id(o)] = k
    for o in layout["objects"]:
        if "z" not in o:
            continue
        base = dsd.zone_of(o["room"], rooms)
        box = [*p(o["rect"][0], o["z"][1]), *p(o["rect"][1], o["z"][0])]
        if o.get("below"):
            d.rectangle(box, outline=ACCENT, width=2)
        else:
            d.rectangle(box, fill=lighter(base, 0.28), outline=lighter(base, 0.6), width=2)
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=BG, outline=ACCENT, width=2)
        centred(d, (cx, cy), str(numbers[id(o)]), font(15, True), ACCENT)
    img.paste(Image.composite(img, before, mask))
    d = ImageDraw.Draw(img)
    for poly in hulls:
        d.polygon([p(*v) for v in poly], outline=HULL, width=6)
    for part in ext["side"]:
        if part["kind"] == "glass":
            for poly in part_polys(part, "side"):
                d.polygon([p(*v) for v in poly], outline=(120, 190, 220), width=4)
    for ln in cut.get("lines", []):
        c = DOOR if ln["kind"] == "door" else ACCENT
        d.line([p(*v) for v in ln["pts"]], fill=c, width=6)
        if "label" in ln:
            centred(d, p(*ln["label_at"]), ln["label"], font(18, True), c)
    for text, lx, lz in cut.get("labels", []):
        centred(d, p(lx, lz), text, font(19, True), TEXT)
    for deck in layout["decks"].values():
        for z in (deck["floor_z"], deck["floor_z"] + deck["clear_height"]):
            xx, yy = p(x1 - 0.4, z)
            d.text((xx, yy - 12), "%.1f m" % z, font=font(18), fill=DIM)
    d.text((MARGIN, 26), "%s – boční řez v ose lodi (pohled ze pravoboku)" % name, font=font(44, True), fill=TEXT)
    deck = next(iter(layout["decks"].values()))
    d.text((MARGIN, 80), "podlaha 0 m, strop %.1f m · zem s podvozkem %.1f m · čísla = objekty z půdorysu · čárkovaně = pod podlahou" % (
        deck["floor_z"] + deck["clear_height"], sheet.get("ground_z", 0)), font=font(20), fill=DIM)
    zone_key(d, MARGIN, h + head + 10)
    img.save(out_path)
    print("wrote", out_path, img.size)


def draw_all(layout, name, out):
    for deck_id, deck in layout["decks"].items():
        dsd.draw_deck(layout, deck_id, "%s – %s" % (name, deck.get("title", deck_id)),
                      os.path.join(out, "%s_deck_%s.png" % (name, deck_id)))
    dims = draw_exterior(layout, name, os.path.join(out, "%s_exterior.png" % name))
    draw_cutaway(layout, name, os.path.join(out, "%s_cutaway.png" % name))
    masks = write_masks(layout, name, os.path.join(out, "guides"))
    print("SHIP_SHEETS " + json.dumps({"dims": dims, "masks": masks}, ensure_ascii=False))
