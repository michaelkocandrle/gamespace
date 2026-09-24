"""Draws a ship's 2D design sheets to scale from its layout JSON: one plan per deck and a side cutaway.
A layout with an "exterior" block (generic format, e.g. Wayfarer) also gets the exterior general
arrangement (top / side / front), a data-driven cutaway and silhouette masks: see ship_sheets.py.

Every room is named and tinted by zone, every object gets a number that the legend explains with its
purpose, so the author can approve the design before any 3D is built (HANDOFF point 75).

    python Tools/Design/draw_ship_design.py ArtSource/Ships/Steadfast/Design/Steadfast_layout.json
"""
import io
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

PX = 62                      # pixels per metre
MARGIN = 90
LEGEND_W = 900
FONT_DIR = r"C:\Windows\Fonts"

BG = (13, 18, 26)
GRID = (24, 32, 44)
HULL = (150, 170, 190)
WALL = (205, 214, 224)
TEXT = (226, 232, 238)
DIM = (120, 136, 152)
ACCENT = (95, 200, 235)      # cool UI accent, like the in-game holograms
DOOR = (240, 180, 90)

# Zone tints, warm architecture / cool command, following the reference cutaways' colour coding.
ZONES = {
    "command": (46, 78, 104),
    "crew": (92, 72, 52),
    "service": (70, 80, 64),
    "cargo": (84, 74, 44),
    "engineering": (96, 52, 44),
}
ROOM_ZONE = {
    "cockpit": "command", "bridge": "command", "fore_lower": "command", "airlock": "service",
    "corridor": "service", "captain": "crew", "crew": "crew", "galley": "crew", "head": "crew",
    "medbay": "service", "armory": "service", "hold": "cargo", "engineering": "engineering",
    "engine_room": "engineering",
}
ZONE_NAMES = {"command": "řízení a avionika", "crew": "obytná část", "service": "služby a přechody",
              "cargo": "náklad", "engineering": "strojovna"}


def font(size, bold=False):
    name = "bahnschrift.ttf"
    f = ImageFont.truetype(os.path.join(FONT_DIR, name), size)
    if bold:
        try:
            f.set_variation_by_name("Bold")
        except Exception:
            pass
    return f


def lighter(c, k):
    return tuple(min(255, int(v + (255 - v) * k)) for v in c)


class Plan:
    """Top view: x forward goes right, +y (port) goes up."""

    def __init__(self, x0, x1, y0, y1):
        self.x0, self.y1 = x0, y1
        self.w = int((x1 - x0) * PX) + 2 * MARGIN
        self.h = int((y1 - y0) * PX) + 2 * MARGIN

    def p(self, x, y):
        return (MARGIN + (x - self.x0) * PX, MARGIN + (self.y1 - y) * PX)

    def rect(self, r):
        (ax, ay), (bx, by) = self.p(r[0], r[3]), self.p(r[1], r[2])
        return [ax, ay, bx, by]


def grid(draw, plan, x0, x1, y0, y1):
    for x in range(int(x0), int(x1) + 1):
        draw.line([plan.p(x, y0), plan.p(x, y1)], fill=GRID, width=1)
    for y in range(int(y0), int(y1) + 1):
        draw.line([plan.p(x0, y), plan.p(x1, y)], fill=GRID, width=1)


def centred(draw, xy, text, f, fill=TEXT):
    lines = text.split("\n")
    h = sum(f.getbbox(t)[3] + 2 for t in lines)
    y = xy[1] - h / 2
    for t in lines:
        w = f.getlength(t)
        draw.text((xy[0] - w / 2, y), t, font=f, fill=fill)
        y += f.getbbox(t)[3] + 2


def wrap(text, f, width):
    out, line = [], ""
    for word in text.split():
        test = (line + " " + word).strip()
        if f.getlength(test) > width and line:
            out.append(line)
            line = word
        else:
            line = test
    if line:
        out.append(line)
    return out


def scale_bar(draw, x, y):
    f = font(18)
    for i in range(5):
        c = WALL if i % 2 == 0 else DIM
        draw.rectangle([x + i * PX, y, x + (i + 1) * PX, y + 8], fill=c)
    draw.text((x, y + 12), "0", font=f, fill=DIM)
    draw.text((x + 5 * PX - 22, y + 12), "5 m", font=f, fill=DIM)


def legend(draw, x, y, items, title, width):
    draw.text((x, y), title, font=font(30, True), fill=ACCENT)
    y += 50
    fb, fn = font(21, True), font(19)
    for num, name, purpose in items:
        draw.ellipse([x, y, x + 30, y + 30], outline=ACCENT, width=2)
        centred(draw, (x + 15, y + 15), str(num), font(17, True), ACCENT)
        draw.text((x + 42, y + 2), name, font=fb, fill=TEXT)
        y += 30
        for line in wrap(purpose, fn, width - 42):
            draw.text((x + 42, y), line, font=fn, fill=DIM)
            y += 24
        y += 10
    return y


def zone_key(draw, x, y):
    f = font(19)
    for zone, c in ZONES.items():
        draw.rectangle([x, y, x + 26, y + 18], fill=c, outline=WALL)
        draw.text((x + 34, y - 2), ZONE_NAMES[zone], font=f, fill=TEXT)
        x += 60 + f.getlength(ZONE_NAMES[zone])


def zone_of(room_id, rooms):
    """Zone of a room: its own "zone" key (generic layouts) or the Steadfast table."""
    r = next((r for r in rooms if r["id"] == room_id), None)
    return ZONES[(r or {}).get("zone") or ROOM_ZONE[room_id]]


def draw_deck(layout, deck_id, title, out_path):
    deck = layout["decks"][deck_id]
    sheet = layout.get("sheet", {})
    x0, x1, y0, y1 = sheet.get("plan_extent", (-0.5, 30.5, -3.8, 3.8))
    all_rooms = layout["rooms"]
    plan = Plan(x0, x1, y0, y1)
    rooms = [r for r in layout["rooms"] if r["deck"] == deck_id]
    objects = [o for o in layout["objects"] if any(r["id"] == o["room"] for r in rooms)]
    head = 120
    img = Image.new("RGB", (plan.w + LEGEND_W, plan.h + head + 2400), BG)
    draw = ImageDraw.Draw(img)
    img_plan = Image.new("RGB", (plan.w, plan.h), BG)
    d = ImageDraw.Draw(img_plan)
    grid(d, plan, x0, x1, y0, y1)

    outline = [plan.p(*v) for v in deck["outline"]]
    for r in rooms:
        c = zone_of(r["id"], all_rooms)
        if "poly" in r:
            d.polygon([plan.p(*v) for v in r["poly"]], fill=c)
        else:
            d.rectangle(plan.rect(r["rect"]), fill=c)
    # Objects: lighter blocks with a number; overhead ones dashed only.
    numbered = []
    for o in objects:
        rr = plan.rect(o["rect"])
        base = zone_of(o["room"], all_rooms)
        if o.get("overhead") or o.get("below"):
            for k in range(int(rr[0]), int(rr[2]), 14):
                d.line([(k, rr[1]), (min(k + 7, rr[2]), rr[1])], fill=ACCENT, width=2)
                d.line([(k, rr[3]), (min(k + 7, rr[2]), rr[3])], fill=ACCENT, width=2)
            if o.get("below"):
                for k in range(int(rr[1]), int(rr[3]), 14):
                    d.line([(rr[0], k), (rr[0], min(k + 7, rr[3]))], fill=ACCENT, width=2)
                    d.line([(rr[2], k), (rr[2], min(k + 7, rr[3]))], fill=ACCENT, width=2)
        else:
            d.rectangle(rr, fill=lighter(base, 0.28), outline=lighter(base, 0.6), width=2)
        numbered.append((o, rr))
    # Walls: every room edge, then the hull outline thicker.
    for r in rooms:
        if "poly" in r:
            d.polygon([plan.p(*v) for v in r["poly"]], outline=WALL, width=3)
        else:
            d.rectangle(plan.rect(r["rect"]), outline=WALL, width=3)
    d.polygon(outline, outline=HULL, width=7)
    for dr in layout["doors"]:
        if dr["deck"] != deck_id:
            continue
        cx, cy = dr["at"]
        hw = dr["width"] / 2
        a, b = ((cx, cy - hw), (cx, cy + hw)) if dr["axis"] == "x" else ((cx - hw, cy), (cx + hw, cy))
        d.line([plan.p(*a), plan.p(*b)], fill=BG, width=9)
        d.line([plan.p(*a), plan.p(*b)], fill=DOOR, width=3)
    for r in rooms:
        rx = plan.rect(r["rect"])
        f = font(24 if (rx[2] - rx[0]) > 200 else 19, True)
        name = r["name"] if f.getlength(r["name"]) < (rx[2] - rx[0]) - 10 else r["name"].replace(" ", "\n", 1)
        # Room name where it covers no object: the first free spot of a few candidates.
        lines = name.splitlines()
        tw = max(f.getlength(t) for t in lines) + 8
        th = 30 * len(lines)
        rects = [rr for o, rr in numbered if o["room"] == r["id"] and not (o.get("overhead") or o.get("below"))]
        mx, my = (rx[0] + rx[2]) / 2, (rx[1] + rx[3]) / 2
        cands = [(mx, rx[1] + 22), (mx, rx[3] - 22), (mx, my), (rx[0] + tw / 2 + 8, rx[1] + 22),
                 (rx[2] - tw / 2 - 8, rx[1] + 22), (rx[0] + tw / 2 + 8, rx[3] - 22), (rx[2] - tw / 2 - 8, rx[3] - 22),
                 (rx[0] + tw / 2 + 8, my), (rx[2] - tw / 2 - 8, my)]
        def free(c):
            bx = [c[0] - tw / 2, c[1] - th / 2, c[0] + tw / 2, c[1] + th / 2]
            return not any(bx[0] < q[2] + 6 and bx[2] > q[0] - 6 and bx[1] < q[3] + 6 and bx[3] > q[1] - 6 for q in rects)
        qx, qy = (rx[2] - rx[0]) / 4, (rx[3] - rx[1]) / 4
        cands += [(rx[0] + i * qx, rx[1] + j * qy) for j in (1, 3, 2) for i in (3, 1, 2)]
        at = next((c for c in cands if free(c)), cands[0])
        if "label_at" in r:
            at = plan.p(*r["label_at"])
        centred(d, at, name, f, TEXT)
    items = []
    for i, (o, rr) in enumerate(numbered, 1):
        cx, cy = (rr[0] + rr[2]) / 2, (rr[1] + rr[3]) / 2
        d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=BG, outline=ACCENT, width=2)
        centred(d, (cx, cy), str(i), font(16, True), ACCENT)
        items.append((i, o["name"] + (" (pod podlahou)" if o.get("below") else ""), o["purpose"]))
    # Nose arrow and scale.
    ax, ay = plan.p(x1 - 0.3, 0)
    d.polygon([(ax, ay - 12), (ax + 22, ay), (ax, ay + 12)], fill=ACCENT)
    scale_bar(d, MARGIN, plan.h - 50)

    img.paste(img_plan, (0, head))
    draw.text((MARGIN, 26), title, font=font(44, True), fill=TEXT)
    draw.text((MARGIN, 80), "%s · měřítko 1 m = %d px · příď vpravo" % (
        sheet.get("subtitle", "Halcyon Freightworks Steadfast · návrh v2 ke schválení"), PX), font=font(20), fill=DIM)
    zone_key(draw, MARGIN, head + plan.h + 10)
    # Room purposes under the plan.
    y = head + plan.h + 60
    col_w = (plan.w - 2 * MARGIN) // 2
    cols = [MARGIN, MARGIN + col_w + 20]
    ys = [y, y]
    for k, r in enumerate(rooms):
        c = 0 if ys[0] <= ys[1] else 1
        yy = ys[c]
        draw.rectangle([cols[c], yy + 4, cols[c] + 16, yy + 20], fill=zone_of(r["id"], all_rooms))
        draw.text((cols[c] + 26, yy), r["name"], font=font(21, True), fill=TEXT)
        yy += 28
        for line in wrap(r["purpose"], font(19), col_w - 30):
            draw.text((cols[c] + 26, yy), line, font=font(19), fill=DIM)
            yy += 24
        ys[c] = yy + 12
    bottom = legend(draw, plan.w + 10, head, items, "Objekty a k čemu jsou", LEGEND_W - 60)
    full_h = max(bottom, max(ys)) + 40
    img = img.crop((0, 0, img.width, full_h))
    img.save(out_path)
    print("wrote", out_path, img.size)


def draw_cutaway(layout, out_path):
    """Side view from starboard: x forward right, z up."""
    x0, x1, z0, z1 = -0.5, 30.5, -2.4, 8.0
    w = int((x1 - x0) * PX) + 2 * MARGIN
    h = int((z1 - z0) * PX) + 2 * MARGIN
    head = 120
    img = Image.new("RGB", (w, h + head + 60), BG)
    draw = ImageDraw.Draw(img)

    def p(x, z):
        return (MARGIN + (x - x0) * PX, head + MARGIN + (z1 - z) * PX)

    for x in range(0, 31):
        draw.line([p(x, z0), p(x, z1)], fill=GRID)
    for z in range(-2, 9):
        draw.line([p(x0, z), p(x1, z)], fill=GRID)
    lo, up = layout["decks"]["lower"], layout["decks"]["upper"]
    zl0, zl1 = lo["floor_z"], lo["floor_z"] + lo["clear_height"]
    zu0, zu1 = up["floor_z"], up["floor_z"] + up["clear_height"]
    # Nacelle behind the hull (dashed look: drawn first, darker).
    for gx in (3.0, 16.0, 24.0):
        draw.rectangle([*p(gx - 0.2, -0.6), *p(gx + 0.2, -2.0)], fill=(60, 68, 80))
        draw.rectangle([*p(gx - 0.7, -2.0), *p(gx + 0.7, -2.2)], fill=(80, 90, 104))
    hull = [(0.5, -0.6), (26.0, -0.6), (28.2, 1.0), (29.8, 3.6), (29.9, 4.6), (27.0, 6.3), (22.0, 6.5),
            (2.5, 6.5), (0.5, 4.5)]
    draw.polygon([p(*v) for v in hull], fill=(22, 30, 40), outline=HULL, width=6)
    # Rooms by x span per deck, clipped to the hull so the nose and the aft slope cut them.
    before = img.copy()
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).polygon([p(*v) for v in hull], fill=255)
    for r in layout["rooms"]:
        za, zb = (zl0, zl1) if r["deck"] == "lower" else (zu0, zu1)
        xa, xb = r["rect"][0], r["rect"][1]
        if r["id"] in ("captain", "crew", "medbay", "corridor", "armory", "head"):
            continue  # beside the corridor; the cutaway shows the starboard rooms + galley instead
        c = ZONES[ROOM_ZONE[r["id"]]]
        draw.rectangle([*p(xa, zb), *p(xb, za)], fill=c, outline=WALL, width=3)
    # Upper deck, starboard side in the section: armoury, head, galley.
    for rid in ("armory", "head"):
        r = next(r for r in layout["rooms"] if r["id"] == rid)
        draw.rectangle([*p(r["rect"][0], zu1), *p(r["rect"][1], zu0)], fill=ZONES[ROOM_ZONE[rid]], outline=WALL, width=3)
    img.paste(Image.composite(img, before, mask))
    draw = ImageDraw.Draw(img)
    draw.polygon([p(*v) for v in hull], outline=HULL, width=6)
    # Reactor through both decks, stairs, ladder, ramp, crane, cargo stacks.
    draw.rounded_rectangle([*p(4.2, zu1 - 0.2), *p(6.3, zl0 + 0.1)], radius=18, fill=(150, 70, 50), outline=(240, 150, 110), width=3)
    centred(draw, ((p(4.2, 0)[0] + p(6.3, 0)[0]) / 2, p(0, 2.9)[1]), "REAKTOR", font(18, True), TEXT)
    draw.rectangle([*p(3.9, zu0 + 1.0), *p(6.6, zu0 + 0.95)], fill=WALL)  # walkway rail
    draw.line([p(23.4, zl0), p(20.6, zu0)], fill=DOOR, width=6)
    for k in range(9):
        t = k / 9
        sx, sz = 23.4 - 2.8 * t, zl0 + 3.3 * t
        draw.line([p(sx, sz), p(sx - 0.31, sz)], fill=DOOR, width=3)
    draw.line([p(4.5, zl0), p(4.5, zu0)], fill=DOOR, width=3)
    draw.line([p(4.9, zl0), p(4.9, zu0)], fill=DOOR, width=3)
    for k in range(1, 11):
        draw.line([p(4.5, k * 0.33), p(4.9, k * 0.33)], fill=DOOR, width=2)
    for i in range(7):
        for j in range(2):
            xa = 10.2 + i * 1.25
            draw.rectangle([*p(xa + 0.04, (j + 1) * 1.25), *p(xa + 1.21, j * 1.25 + 0.04)], fill=(128, 110, 64), outline=(190, 168, 110), width=2)
    draw.line([p(7.2, zl1 - 0.15), p(18.8, zl1 - 0.15)], fill=ACCENT, width=5)
    draw.rectangle([*p(12.0, zl1 - 0.1), *p(12.6, zl1 - 0.35)], fill=ACCENT)
    draw.line([p(7.2, -0.6), p(10.0, -1.9)], fill=DOOR, width=6)
    draw.rectangle([*p(19.0, zl1), *p(21.5, zl0)], outline=DOOR, width=3)
    # Seats in the cockpit, sensors station, glass.
    for sx in (25.8, 24.4):
        draw.rectangle([*p(sx - 0.3, zu0 + 1.1), *p(sx + 0.3, zu0 + 0.45)], fill=lighter(ZONES["command"], 0.4))
        draw.rectangle([*p(sx - 0.45, zu0 + 1.55), *p(sx - 0.3, zu0 + 0.45)], fill=lighter(ZONES["command"], 0.4))
    draw.polygon([p(27.0, 6.3), p(29.9, 4.6), p(29.8, 3.6), p(28.6, 3.9), p(27.0, 5.7)], fill=(60, 120, 150))
    draw.rectangle([*p(27.0, zu0 + 1.0), *p(28.6, zu0 + 0.6)], fill=lighter(ZONES["command"], 0.4))
    # Turret and grapple arms.
    draw.rounded_rectangle([*p(14.5, 7.2), *p(16.5, 6.5)], radius=10, fill=(60, 68, 80), outline=HULL, width=2)
    draw.line([p(15.5, 7.0), p(18.0, 7.1)], fill=HULL, width=4)
    draw.line([p(15.0, -0.6), p(16.5, -1.6), p(18.0, -1.4)], fill=HULL, width=5)

    labels = [
        ("kokpit (3 místa)", 26.6, zu1 - 0.3), ("předsíň", 22.0, zu1 - 0.3), ("kuchyňka / jídelna", 17.8, zu1 - 0.3),
        ("koupelna", 13.8, zu1 - 0.3), ("zbrojnice / EVA", 10.8, zu1 - 0.3), ("strojovna\nhorní patro", 7.7, zu1 - 0.5),
        ("nákladový prostor\n42 SCU", 8.6, 1.5), ("přední technická: avionika, štíty", 23.0, zl1 - 0.3),
        ("komora", 20.25, zl1 - 1.0), ("strojovna\ndolní patro", 2.0, zl1 - 0.5), ("rampa", 8.6, -1.6),
        ("drapáky", 16.6, -2.0), ("dálková věž 2× S2", 15.5, 7.6), ("jeřábová dráha", 8.6, zl1 - 0.4),
    ]
    for text, lx, lz in labels:
        centred(draw, p(lx, lz), text, font(19, True), TEXT)
    draw.text((MARGIN, 26), "Steadfast – boční řez (pohled ze pravoboku)", font=font(44, True), fill=TEXT)
    draw.text((MARGIN, 80), "dolní paluba: podlaha 0 m, strop %.1f m · horní paluba: podlaha %.1f m, strop %.1f m · výška lodi s podvozkem 9,5 m" % (zl1, zu0, zu1),
              font=font(20), fill=DIM)
    for z in (zl0, zl1, zu0, zu1):
        xx, yy = p(30.1, z)
        draw.text((xx, yy - 12), "%.1f m" % z, font=font(18), fill=DIM)
    zone_key(draw, MARGIN, h + head + 10)
    sx, sy = p(0, -2.3)
    img.save(out_path)
    print("wrote", out_path, img.size)


def main():
    path = sys.argv[1]
    layout = json.load(io.open(path, encoding="utf-8"))
    out = os.path.dirname(path)
    name = os.path.basename(path).split("_")[0]
    if "exterior" in layout:
        import ship_sheets
        ship_sheets.draw_all(layout, name, out)
        return
    draw_deck(layout, "upper", name + " – horní paluba (obytná)", os.path.join(out, name + "_deck_upper.png"))
    draw_deck(layout, "lower", name + " – dolní paluba (náklad a technika)", os.path.join(out, name + "_deck_lower.png"))
    draw_cutaway(layout, os.path.join(out, name + "_cutaway.png"))


if __name__ == "__main__":
    main()
