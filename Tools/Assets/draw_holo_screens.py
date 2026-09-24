"""Draw the content of the Steadfast cockpit's holographic screens, Star Citizen style.

    python Tools/Assets/draw_holo_screens.py

Writes PNGs into ArtSource/Ships/Steadfast/Interior/Screens/. Black is "no light": the hologram
material adds the picture on top of the scene, so black is see-through and everything drawn glows.
The layouts follow the author's SC references (ArtSource/Reference/Mood/sc_cockpit_*.webp, Docs/UI):
power management with PWR/WPN/THR/SHLD/COOL, a ship self-status silhouette, a communications list,
a scanning panel, and a radar disc for the hologram above the console. Static for now; the live
cockpit displays (UCockpitDisplayComponent) take over once the Steadfast flies.
"""

import math
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "ArtSource", "Ships", "Steadfast", "Interior", "Screens")
FONTS = os.path.join(ROOT, "Content", "UI", "Fonts")

BLUE = (90, 170, 255)
PALE = (170, 215, 255)
DIM = (35, 70, 110)
AMBER = (255, 190, 60)
RED = (255, 90, 70)
W, H = 1024, 720


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


BOLD = lambda s: font("Rajdhani-SemiBold.ttf", s)
MONO = lambda s: font("ShareTechMono-Regular.ttf", s)


def frame(d, title, footer=None):
    """The panel's chrome: thin border with clipped corners, a title bar, a pager at the bottom."""
    c = 26
    pts = [(c, 8), (W - 8, 8), (W - 8, H - c), (W - c, H - 8), (8, H - 8), (8, c)]
    d.polygon(pts, outline=DIM, width=3)
    d.rectangle((24, 22, W - 24, 70), fill=(20, 45, 75))
    d.text((40, 26), title, font=BOLD(38), fill=PALE)
    d.text((W - 190, 32), "STEADFAST", font=MONO(24), fill=BLUE)
    if footer:
        d.rectangle((120, H - 64, W - 120, H - 28), fill=(25, 60, 100))
        d.text((W // 2 - len(footer) * 8, H - 62), footer, font=BOLD(30), fill=PALE)
        for x, ch in ((60, "<"), (W - 80, ">")):
            d.rectangle((x - 22, H - 64, x + 22, H - 28), outline=BLUE, width=2)
            d.text((x - 8, H - 64), ch, font=BOLD(30), fill=BLUE)


def power(d):
    frame(d, "POWER MANAGEMENT", "POWER MANAGEMENT")
    labels = ["PWR", "WPN", "THR", "SHLD", "COOL"]
    values = [0.8, 0.55, 0.9, 0.7, 0.45]
    for i, (label, v) in enumerate(zip(labels, values)):
        x = 90 + i * 175
        active = label == "WPN"
        colour = AMBER if active else BLUE
        d.rectangle((x - 45, 100, x + 75, 150), outline=colour, width=3, fill=(60, 45, 10) if active else None)
        d.text((x - 30, 104), label, font=BOLD(36), fill=colour)
        for k in range(10):                                   # the pip column
            y = 560 - k * 38
            on = k < round(v * 10)
            d.rectangle((x - 20, y, x + 50, y + 28), fill=colour if on else None, outline=colour if on else DIM, width=2)
        d.text((x - 10, 590), "%d%%" % round(v * 100), font=MONO(28), fill=PALE)
    d.text((40, 630), "OUTPUT 4/14", font=MONO(26), fill=BLUE)
    d.text((W - 300, 630), "BATTERY 100%", font=MONO(26), fill=BLUE)


def ship(d, cx, cy, s, colour):
    """A top-down silhouette of the Steadfast (a blunt freighter with two engine pods)."""
    body = [(0, -1.0), (0.22, -0.8), (0.3, -0.3), (0.32, 0.5), (0.2, 0.9), (-0.2, 0.9), (-0.32, 0.5), (-0.3, -0.3), (-0.22, -0.8)]
    d.polygon([(cx + x * s, cy + y * s) for x, y in body], outline=colour, width=4)
    for side in (-1, 1):
        pod = [(0.32, 0.1), (0.62, 0.2), (0.66, 0.85), (0.4, 0.95), (0.32, 0.75)]
        d.polygon([(cx + side * x * s, cy + y * s) for x, y in pod], outline=colour, width=4)
        d.ellipse((cx + side * 0.52 * s - 0.08 * s, cy + 0.88 * s - 0.05 * s, cx + side * 0.52 * s + 0.08 * s, cy + 0.88 * s + 0.08 * s),
                  outline=AMBER, width=3)
    d.line((cx, cy - 0.7 * s, cx, cy + 0.7 * s), fill=DIM, width=2)
    d.rectangle((cx - 0.12 * s, cy - 0.62 * s, cx + 0.12 * s, cy - 0.42 * s), outline=PALE, width=3)


def status(d):
    frame(d, "SELF STATUS", "SELF STATUS")
    ship(d, 300, 380, 250, BLUE)
    rows = [("HULL", "100%"), ("SHIELD F", "96%"), ("SHIELD A", "92%"), ("H-FUEL", "78%"), ("QT FUEL", "64%"), ("CARGO", "12/48 SCU")]
    for i, (k, v) in enumerate(rows):
        y = 130 + i * 72
        d.text((600, y), k, font=BOLD(34), fill=BLUE)
        d.text((820, y), v, font=MONO(32), fill=PALE)
        d.line((600, y + 48, W - 50, y + 48), fill=DIM, width=2)


def comms(d):
    frame(d, "COMMUNICATIONS", "COMMUNICATIONS")
    names = ["VEYRA LANDING SERVICES", "VEYRA ORBITAL TRAFFIC", "HALCYON FREIGHT DESK", "CARGO HAULER KESTREL", "STATION SECURITY", "MEDICAL RESPONSE"]
    for i, n in enumerate(names):
        y = 110 + i * 80
        d.text((50, y), ">", font=BOLD(34), fill=BLUE)
        d.text((85, y), n, font=BOLD(34), fill=PALE if i else AMBER)
        d.rectangle((W - 200, y + 2, W - 50, y + 46), outline=BLUE, width=2)
        d.text((W - 170, y + 4), "HAIL", font=BOLD(32), fill=BLUE)
        d.line((50, y + 60, W - 50, y + 60), fill=DIM, width=1)


def scan(d):
    frame(d, "SCANNING", "SCANNING")
    for i, (t, on) in enumerate((("INFO", True), ("PARTS", False), ("CARGO", False))):
        x = 60 + i * 200
        d.rectangle((x, 95, x + 180, 140), outline=BLUE, width=2, fill=(40, 90, 150) if on else None)
        d.text((x + 40, 98), t, font=BOLD(34), fill=PALE)
    d.text((60, 180), "HALCYON MULE", font=BOLD(46), fill=PALE)
    d.text((60, 232), "LIGHT FREIGHT", font=BOLD(40), fill=BLUE)
    for i, (k, v) in enumerate((("SIGNATURE", "55745.7"), ("MASS", "777061.75"), ("DISTANCE", "378.9 m"), ("SPEED", "0 m/s"))):
        y = 320 + i * 64
        d.text((60, y), "> %s:" % k, font=BOLD(36), fill=BLUE)
        d.text((420, y), v, font=MONO(36), fill=AMBER if k == "SIGNATURE" else PALE)
    ship(d, 830, 330, 110, DIM)


def dash(d, title, rows):
    frame(d, title)
    for i, (k, v, fill) in enumerate(rows):
        y = 110 + i * 95
        d.text((50, y), k, font=BOLD(40), fill=BLUE)
        d.rectangle((330, y + 12, 330 + 600, y + 44), outline=DIM, width=2)
        d.rectangle((330, y + 12, 330 + int(600 * fill), y + 44), fill=AMBER if fill < 0.3 else BLUE)
        d.text((330 + 610 - 140, y - 34), v, font=MONO(30), fill=PALE)


def radar(size=1024):
    """The disc for the hologram above the console: range rings, a sweep, contacts."""
    im = Image.new("RGB", (size, size), (0, 0, 0))
    d = ImageDraw.Draw(im)
    c = size // 2
    for k, r in enumerate((0.95, 0.72, 0.49, 0.26)):
        rr = int(r * c)
        d.ellipse((c - rr, c - rr, c + rr, c + rr), outline=BLUE if k == 0 else DIM, width=6 if k == 0 else 3)
    for a in range(0, 360, 30):
        x, y = c + math.cos(math.radians(a)) * 0.95 * c, c + math.sin(math.radians(a)) * 0.95 * c
        d.line((c, c, x, y), fill=DIM, width=2)
    for i in range(40):                                        # the sweep fading behind the beam
        a = math.radians(-60 - i * 1.5)
        x, y = c + math.cos(a) * 0.95 * c, c + math.sin(a) * 0.95 * c
        shade = int(160 * (1 - i / 40))
        d.line((c, c, x, y), fill=(shade // 3, int(shade / 1.6), shade), width=5)
    for (px, py, col) in ((0.3, -0.4, AMBER), (-0.5, 0.2, BLUE), (0.1, 0.6, RED), (-0.2, -0.7, BLUE)):
        x, y = c + px * c, c + py * c
        d.rectangle((x - 14, y - 14, x + 14, y + 14), outline=col, width=5)
    d.polygon([(c, c - 30), (c + 20, c + 20), (c - 20, c + 20)], outline=PALE, width=5)
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    pages = {
        "Holo_Power": power, "Holo_Status": status, "Holo_Comms": comms, "Holo_Scan": scan,
        "Holo_DashLeft": lambda d: dash(d, "FLIGHT", [("SCM", "210 m/s", 0.7), ("BOOST", "100%", 1.0), ("AFTERBURN", "86%", 0.86), ("G-SAFE", "ON", 1.0), ("COMSTAB", "ON", 1.0)]),
        "Holo_DashRight": lambda d: dash(d, "SYSTEMS", [("QUANTUM", "READY", 1.0), ("H-FUEL", "78%", 0.78), ("QT FUEL", "64%", 0.64), ("COOLER", "41%", 0.41), ("SHIELDS", "96%", 0.96)]),
    }
    for name, draw in pages.items():
        im = Image.new("RGB", (W, H), (0, 0, 0))
        draw(ImageDraw.Draw(im))
        im.save(os.path.join(OUT, name + ".png"))
    radar().save(os.path.join(OUT, "Holo_Radar.png"))
    print("draw_holo_screens: %d obrazovek -> %s" % (len(pages) + 1, OUT))


main()
