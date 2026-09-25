"""Interior markings of the Wayfarer, as in the SC reference interiors (big section numbers, room names,
arrows, emergency and hazard signs, component labels, floor lanes): white shapes on transparent, tinted
per decal in <Ship>_setup.json "decals" (one texture serves several colours).

    python Tools/Assets/generate_interior_decals.py

Writes ArtSource/Ships/Shared/Decals/D_Int_*.png. Type: the project's own fonts (Content/UI/Fonts).
Projected as deferred decals like the exterior's big markings (generate_big_decals.py).
"""
import os

from PIL import Image, ImageDraw, ImageFont

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "ArtSource", "Ships", "Shared", "Decals")
FONTS = os.path.join(REPO, "Content", "UI", "Fonts")
W = (255, 255, 255, 255)
CLEAR = (0, 0, 0, 0)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def text_at(d, xy, text, f, anchor="la"):
    d.text(xy, text, font=f, fill=W, anchor=anchor)


def section(number):
    """A big section number with a small caption and a bar, as on SC portals (MISC "01")."""
    im = Image.new("RGBA", (512, 512), CLEAR)
    d = ImageDraw.Draw(im)
    text_at(d, (256, 250), number, font("Rajdhani-SemiBold.ttf", 330), "mm")
    d.rectangle((70, 420, 442, 436), fill=W)
    text_at(d, (256, 480), "SECTION  A-%s" % number, font("ShareTechMono-Regular.ttf", 44), "mm")
    return im


def label(title, sub=None, size=(2048, 512), arrow=None):
    """A room or direction sign: big name, a rule, a small line under it, optional arrow."""
    im = Image.new("RGBA", size, CLEAR)
    d = ImageDraw.Draw(im)
    w, h = size
    x = 60
    if arrow == "left":
        d.polygon([(40, h * 0.42), (220, h * 0.12), (220, h * 0.72)], fill=W)
        x = 280
    text_at(d, (x, h * 0.42), title, font("Rajdhani-SemiBold.ttf", int(h * 0.5)), "lm")
    d.rectangle((x, h * 0.74, w - 60 if arrow != "right" else w - 320, h * 0.76), fill=W)
    if sub:
        text_at(d, (x, h * 0.88), sub, font("ShareTechMono-Regular.ttf", int(h * 0.13)), "lm")
    if arrow == "right":
        for k in range(3):
            x0 = w - 300 + k * 90
            d.polygon([(x0, h * 0.14), (x0 + 60, h * 0.14), (x0 + 150, h * 0.42), (x0 + 60, h * 0.7), (x0, h * 0.7), (x0 + 90, h * 0.42)], fill=W)
    return im


def caution(line1, line2):
    """Warning triangle and two lines (tinted amber in the setup)."""
    im = Image.new("RGBA", (1024, 512), CLEAR)
    d = ImageDraw.Draw(im)
    d.polygon([(60, 440), (230, 70), (400, 440)], fill=W)
    d.polygon([(110, 410), (230, 150), (350, 410)], fill=CLEAR)
    d.rectangle((218, 230, 242, 340), fill=W)
    d.rectangle((218, 360, 242, 385), fill=W)
    text_at(d, (440, 190), line1, font("Rajdhani-SemiBold.ttf", 150), "lm")
    text_at(d, (444, 340), line2, font("ShareTechMono-Regular.ttf", 64), "lm")
    return im


def lane(length_px=4096, height_px=256):
    """A floor lane: two edge lines and chevrons pointing forward (+u)."""
    im = Image.new("RGBA", (length_px, height_px), CLEAR)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 8, length_px, 26), fill=W)
    d.rectangle((0, height_px - 26, length_px, height_px - 8), fill=W)
    for x in range(120, length_px - 120, 360):
        d.polygon([(x, 60), (x + 50, 60), (x + 120, height_px / 2), (x + 50, height_px - 60), (x, height_px - 60), (x + 70, height_px / 2)], fill=W)
    return im


def plate(title, lines):
    """A component label plate: frame, name, spec lines (control and service labels)."""
    im = Image.new("RGBA", (1024, 512), CLEAR)
    d = ImageDraw.Draw(im)
    d.rectangle((12, 12, 1011, 499), outline=W, width=10)
    d.rectangle((12, 12, 1011, 150), fill=W)
    text_at(d, (50, 84), title, font("Rajdhani-SemiBold.ttf", 110), "lm")
    d.text((50, 84), title, font=font("Rajdhani-SemiBold.ttf", 110), fill=CLEAR, anchor="lm")
    for k, line in enumerate(lines):
        text_at(d, (50, 220 + k * 90), line, font("ShareTechMono-Regular.ttf", 62), "lm")
    return im


def exit_sign():
    """Emergency exit: a running figure cut into a box and EXIT (tinted green)."""
    im = Image.new("RGBA", (1024, 512), CLEAR)
    d = ImageDraw.Draw(im)
    d.rectangle((20, 40, 400, 470), fill=W)
    # a simple running figure, cut out
    d.ellipse((230, 80, 300, 150), fill=CLEAR)
    d.polygon([(200, 170), (290, 170), (250, 300), (310, 420), (270, 430), (210, 320), (140, 420), (100, 400), (180, 290)], fill=CLEAR)
    d.polygon([(290, 180), (360, 250), (340, 270), (280, 215)], fill=CLEAR)
    d.polygon([(200, 175), (130, 240), (150, 258), (215, 205)], fill=CLEAR)
    text_at(d, (450, 230), "EXIT", font("Rajdhani-SemiBold.ttf", 230), "lm")
    text_at(d, (560, 420), "RAMP", font("ShareTechMono-Regular.ttf", 70), "lm")
    d.polygon([(455, 420), (515, 385), (515, 405), (545, 405), (545, 435), (515, 435), (515, 455)], fill=W)
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    items = {"D_Int_Section_%s" % n: section(n) for n in ("01", "02", "03", "04", "05")}
    items.update({
        "D_Int_Hold": label("CARGO HOLD", "DECK A  ·  8 SCU  ·  MAG-LOCK GRID"),
        "D_Int_Engineering": label("ENGINEERING", "AUTHORISED CREW ONLY", arrow="right"),
        "D_Int_Cockpit": label("COCKPIT", "CREW QUARTERS  ·  FLIGHT DECK", arrow="right"),
        "D_Int_Caution_Voltage": caution("CAUTION", "HIGH VOLTAGE 1.2kV"),
        "D_Int_Caution_Load": caution("CAUTION", "MOVING LOADS"),
        "D_Int_Lane": lane(),
        "D_Int_Exit": exit_sign(),
        "D_Int_Fire": plate("FIRE SUPPRESSION", ["EXTINGUISHER  CO2-4", "PULL · AIM · SQUEEZE"]),
        "D_Int_Reactor": plate("REACTOR  S1", ["POWER PLANT  ·  CLASS C", "ISOLATE BEFORE SERVICE"]),
        "D_Int_Shield": plate("SHIELD GEN  S1", ["FIELD EMITTER  ·  CLASS C", "HOT SWAP  ·  2 MIN"]),
        "D_Int_Cooler": plate("COOLER  S1", ["COOLANT LOOP A/B", "DO NOT OBSTRUCT VENTS"]),
        "D_Int_Grid": plate("CARGO GRID", ["8 SCU  ·  MAX 16 t", "LOCK BEFORE FLIGHT"]),
    })
    for name, im in items.items():
        im.save(os.path.join(OUT, name + ".png"))
        print("INTDECAL", name, im.size)


if __name__ == "__main__":
    main()
