"""2D mock of the holo MFD pages (author 8. 10. 2026: the speed and G figures read wrong - font, style, size; the
layout, the colours): two variants of the FLIGHT and STATUS pages at the picture's own size (880 x 490 px), drawn
with the game's fonts over the holo field's dark-blue tint, for the author to pick before the widget is rebuilt.

    python Tools/Design/mfd_layout_mock.py      -> ArtSource/Ships/Wayfarer/Concept/Cockpit/mfd_v5_mock.png
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONTS = os.path.join(ROOT, "Content", "UI", "Fonts")
OUT = os.path.join(ROOT, "ArtSource", "Ships", "Wayfarer", "Concept", "Cockpit", "mfd_v5_mock.png")
W, H = 880, 490

TEXT = (225, 240, 255)          # primary type: near white, a breath of blue
DIM = (120, 170, 210)           # labels, units
LINE = (90, 185, 255)           # vector lines, rings (the radar's cyan)
FAINT = (45, 95, 140)
AMBER = (245, 166, 35)          # flags and cautions only (SC #F5A623)
RED = (255, 84, 60)             # warnings only


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


SAIRA = lambda s: font("Saira-Medium.ttf", s)              # noqa: E731
SAIRA_SB = lambda s: font("Saira-SemiBold.ttf", s)         # noqa: E731
OX = lambda s: font("Oxanium-Medium.ttf", s)               # noqa: E731


def field(img):
    """The holo field: a dark-blue tint, brighter towards the emitter, its glowing edge and corner brackets."""
    d = ImageDraw.Draw(img)
    for y in range(H):
        k = y / H
        c = (int(6 + 10 * k * k), int(14 + 22 * k * k), int(28 + 40 * k * k))
        d.line([(0, y), (W, y)], fill=c)
    for y in range(0, H, 7):
        d.line([(0, y), (W, y)], fill=(10, 22, 40))
    d.rectangle([2, 2, W - 3, H - 3], outline=FAINT, width=1)
    arm = 34
    for (x, y, sx, sy) in ((6, 6, 1, 1), (W - 7, 6, -1, 1), (W - 7, H - 7, -1, -1), (6, H - 7, 1, -1)):
        d.line([(x + sx * arm, y), (x, y), (x, y + sy * arm)], fill=LINE, width=3)


def glow(img, layer):
    """Lines and type glow a little (bloom of the projection)."""
    g = layer.filter(ImageFilter.GaussianBlur(4))
    img.paste(Image.blend(img, Image.composite(g, img, g.convert("L").point(lambda v: min(255, v * 2))), 0.5))
    img.paste(layer, (0, 0), layer)


def text(d, xy, s, f, fill, anchor="la"):
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def tabs(d, names, active):
    x = 24
    for i, n in enumerate(names):
        f = SAIRA(19)
        w = d.textlength(n, font=f)
        col = TEXT if i == active else DIM
        text(d, (x, 22), n, f, col)
        if i == active:
            d.line([(x, 50), (x + w, 50)], fill=LINE, width=3)
        x += w + 30
    d.line([(20, 54), (W - 20, 54)], fill=FAINT, width=1)


def octa(d, box, label, on=False, flag=False, f=None):
    x0, y0, x1, y1 = box
    c = 7
    pts = [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]
    if flag:
        d.polygon(pts, fill=AMBER)
        text(d, ((x0 + x1) / 2, (y0 + y1) / 2), label, f or SAIRA_SB(18), (20, 14, 6), "mm")
    else:
        d.polygon(pts, outline=TEXT if on else FAINT, width=2)
        text(d, ((x0 + x1) / 2, (y0 + y1) / 2), label, f or SAIRA(18), TEXT if on else DIM, "mm")


def arc_gauge(d, c, r, frac, ticks=True, width=6, col=LINE):
    """A 270 deg ring like the radar's: faint track, lit value arc, ticks every 10 %."""
    a0, a1 = 135, 405
    box = [c[0] - r, c[1] - r, c[0] + r, c[1] + r]
    d.arc(box, a0, a1, fill=FAINT, width=2)
    d.arc(box, a0, a0 + (a1 - a0) * frac, fill=col, width=width)
    if ticks:
        for k in range(11):
            a = math.radians(a0 + (a1 - a0) * k / 10)
            r0, r1 = r + 6, r + (14 if k % 5 == 0 else 10)
            d.line([(c[0] + r0 * math.cos(a), c[1] + r0 * math.sin(a)), (c[0] + r1 * math.cos(a), c[1] + r1 * math.sin(a))],
                   fill=DIM, width=2)


def page_flight_a():
    img = Image.new("RGB", (W, H))
    field(img)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    tabs(d, ["FLIGHT", "THRUST", "NAV", "CONFIG"], 0)
    # the speed ring, the figure inside it
    c = (200, 270)
    arc_gauge(d, c, 140, 90 / 220)
    text(d, (c[0], c[1] - 6), "90", SAIRA(104), TEXT, "mm")
    text(d, (c[0], c[1] + 58), "m/s", SAIRA(22), DIM, "mm")
    text(d, (c[0], c[1] + 100), "LIMIT 220", SAIRA(19), DIM, "mm")
    # G: a small ring
    g = (470, 190)
    arc_gauge(d, g, 58, 4.5 / 9.0, ticks=False, width=5)
    text(d, (g[0], g[1] - 4), "4.5", SAIRA(44), TEXT, "mm")
    text(d, (g[0], g[1] + 32), "G", SAIRA(20), DIM, "mm")
    text(d, (g[0], g[1] + 82), "G MAX 7.0", SAIRA(18), DIM, "mm")
    # thrust budget: three thin bars
    for i, (lab, v, col) in enumerate((("SPD", 0.41, LINE), ("BST", 1.0, LINE), ("AB", 1.0, AMBER))):
        x = 420 + i * 46
        d.rectangle([x, 330, x + 10, 440], outline=FAINT, width=1)
        d.rectangle([x + 2, 438 - 106 * v, x + 8, 438], fill=col)
        text(d, (x + 5, 456), lab, SAIRA(16), DIM, "mm")
    # modes: SC's outlined chips, flags in amber
    text(d, (612, 78), "MODE", SAIRA(16), DIM)
    octa(d, (612, 100, 770, 146), "SCM", on=True, f=SAIRA(24))
    for i, (lab, on, flag) in enumerate((("CPLD", True, False), ("GSAF", True, False), ("CSTB", False, False),
                                         ("BOOST", False, False), ("PREC", False, False), ("VTOL", False, True))):
        x = 612 + (i % 2) * 124
        y = 168 + (i // 2) * 60
        octa(d, (x, y, x + 112, y + 44), lab, on=on, flag=flag)
    glow(img, lay)
    return img


def page_status_a():
    img = Image.new("RGB", (W, H))
    field(img)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    tabs(d, ["STATUS", "CONTACTS", "SELF"], 0)
    rows = (("GEAR", "UP", TEXT), ("QUANTUM", "OFF", DIM), ("R-ALT", "4 007 m", TEXT), ("VSI", "0 m/s", TEXT),
            ("ATMO", "0.25 atm", TEXT))
    for i, (k, v, col) in enumerate(rows):
        y = 92 + i * 66
        text(d, (40, y), k, SAIRA(22), DIM)
        text(d, (560, y), v, SAIRA(34), col, "ra")
        d.line([(40, y + 50), (560, y + 50)], fill=FAINT, width=1)
    # altitude: a vertical scale like the radar's rings, the ship's mark on it
    x = 690
    d.line([(x, 90), (x, 430)], fill=FAINT, width=2)
    for k in range(9):
        y = 90 + k * 42.5
        d.line([(x - (14 if k % 2 == 0 else 8), y), (x, y)], fill=DIM, width=2)
    d.polygon([(x + 6, 260), (x + 26, 250), (x + 26, 270)], fill=LINE)
    text(d, (x + 36, 260), "4.0 km", SAIRA(22), TEXT, "lm")
    text(d, (x, 452), "ALT", SAIRA(16), DIM, "mm")
    glow(img, lay)
    return img


def page_flight_b():
    """Variant B: SC 4.x's MFD - a button column, one big figure, white type, amber flags, cyan only for lines."""
    img = Image.new("RGB", (W, H))
    field(img)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i, (lab, on, flag) in enumerate((("SCM", True, False), ("CPLD", True, False), ("GSAF", True, False),
                                         ("CSTB", False, False), ("BOOST", False, False), ("VTOL", False, True))):
        octa(d, (22, 26 + i * 74, 152, 82 + i * 74), lab, on=on, flag=flag, f=SAIRA(22) if not flag else SAIRA_SB(22))
    d.line([(176, 30), (176, 460)], fill=FAINT, width=1)
    text(d, (210, 40), "SPEED", SAIRA(20), DIM)
    text(d, (520, 210), "90", SAIRA(150), TEXT, "rm")
    text(d, (530, 236), "m/s", SAIRA(26), DIM, "ls")
    d.line([(210, 300), (640, 300)], fill=FAINT, width=1)
    d.line([(210, 300), (210 + 430 * 90 / 220, 300)], fill=LINE, width=4)
    text(d, (210, 318), "LIMIT 220", SAIRA(18), DIM)
    text(d, (690, 40), "G", SAIRA(20), DIM)
    text(d, (850, 130), "4.5", SAIRA(72), TEXT, "rm")
    text(d, (850, 200), "MAX 7.0", SAIRA(18), DIM, "rm")
    for i, (lab, v, col) in enumerate((("SPD", 0.41, LINE), ("BST", 1.0, LINE), ("AB", 1.0, AMBER))):
        y = 372 + i * 34
        text(d, (210, y), lab, SAIRA(18), DIM, "lm")
        d.line([(270, y), (840, y)], fill=FAINT, width=2)
        d.line([(270, y), (270 + 570 * v, y)], fill=col, width=6)
    glow(img, lay)
    return img


def main():
    pages = [("A  kruhy radaru - FLIGHT", page_flight_a()), ("A  STATUS", page_status_a()), ("B  SC 4.x - FLIGHT", page_flight_b())]
    pad, head = 30, 50
    sheet = Image.new("RGB", (W * 2 + pad * 3, (H + head) * 2 + pad * 2), (20, 22, 26))
    d = ImageDraw.Draw(sheet)
    for i, (title, im) in enumerate(pages):
        x = pad + (i % 2) * (W + pad)
        y = pad + (i // 2) * (H + head + pad)
        d.text((x, y), title, font=SAIRA(26), fill=(230, 230, 230))
        sheet.paste(im, (x, y + head))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    sheet.save(OUT)
    print("MFDMOCK", OUT)


if __name__ == "__main__":
    main()
