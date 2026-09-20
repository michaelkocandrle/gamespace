"""The markings a ship carries: stencils, hazard stripes and service hatches, as RGBA decals.

    python Tools/Assets/generate_decals.py

Writes ArtSource/Ships/Shared/Decals/D_*.png. The game projects them onto the hull as deferred
decals (M_Ship_Decal, placed from the "decals" list in <Ship>_setup.json), so they do not need a
place in the ship's UV atlas and stay sharp from any distance.

Why generated and not painted: the same reason the detail textures are (generate_detail_textures.py)
- they are deterministic, they cost no repository space to regenerate, and a ship's registration
changes by editing one string here. Nothing imitates a real manufacturer; the marks are this game's.

The type is the project's own fonts (Content/UI/Fonts), the same ones the cockpit displays use.
"""

import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "ArtSource", "Ships", "Shared", "Decals")
FONTS = os.path.join(REPO, "Content", "UI", "Fonts")

WHITE = (216, 220, 226)
DARK = (26, 29, 34)
HAZARD = (198, 150, 40)


def font(name, size):
    path = os.path.join(FONTS, name)
    return ImageFont.truetype(path, size) if os.path.exists(path) else ImageFont.load_default(size)


def new(width, height):
    return Image.new("RGBA", (width, height), (0, 0, 0, 0))


def centred(draw, box, text, f, fill):
    left, top, right, bottom = draw.textbbox((0, 0), text, font=f)
    draw.text(((box[0] + box[2] - right - left) / 2, (box[1] + box[3] - bottom - top) / 2), text, font=f, fill=fill)


def weather(image, amount=0.25, seed=7):
    """Paint is never perfectly even: eat into the alpha with soft noise, so an edge is not a razor."""
    rng = np.random.default_rng(seed)
    a = np.asarray(image, dtype=np.float32)
    noise = rng.random(a.shape[:2]).astype(np.float32)
    noise = np.asarray(Image.fromarray((noise * 255).astype(np.uint8)).resize(
        (max(a.shape[1] // 12, 1), max(a.shape[0] // 12, 1))).resize(
        (a.shape[1], a.shape[0]), Image.BICUBIC), dtype=np.float32) / 255.0
    a[..., 3] *= 1.0 - amount * noise
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def registration(text="VNG-014", maker="CROSSFIELD DYNAMICS"):
    """The ship's number, big, with the yard that built it underneath in small type."""
    image = new(1024, 256)
    draw = ImageDraw.Draw(image)
    centred(draw, (0, 10, 1024, 170), text, font("Rajdhani-SemiBold.ttf", 150), WHITE + (255,))
    centred(draw, (0, 180, 1024, 240), maker, font("ShareTechMono-Regular.ttf", 44), WHITE + (190,))
    return weather(image, 0.3, 1)


def hazard_stripes(width=1024, height=256, pitch=110, angle=1.0):
    """Diagonal stripes for the edge of an intake or a thruster: keep clear of this."""
    image = new(width, height)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, height), fill=DARK + (235,))
    for x in range(-height * 2, width + height * 2, pitch):
        draw.polygon([(x, height), (x + pitch // 2, height), (x + pitch // 2 + int(height * angle), 0),
                      (x + int(height * angle), 0)], fill=HAZARD + (255,))
    draw.rectangle((0, 0, width - 1, height - 1), outline=DARK + (255,), width=6)
    return weather(image, 0.35, 2)


def caution(text="CAUTION  THRUST"):
    """A band of warning type, for beside a nozzle."""
    image = new(1024, 192)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1024, 192), fill=DARK + (215,))
    draw.rectangle((8, 8, 1015, 183), outline=HAZARD + (255,), width=7)
    centred(draw, (0, 0, 1024, 192), text, font("ShareTechMono-Regular.ttf", 92), HAZARD + (255,))
    return weather(image, 0.3, 3)


def hatch(label="ACCESS  A4"):
    """A service hatch: a panel outline with bolts in the corners and a label along the top."""
    image = new(512, 512)
    draw = ImageDraw.Draw(image)
    draw.rectangle((24, 24, 487, 487), outline=DARK + (240,), width=9)
    draw.rectangle((40, 40, 471, 471), outline=WHITE + (70,), width=3)
    for x, y in ((64, 64), (447, 64), (64, 447), (447, 447)):
        draw.ellipse((x - 13, y - 13, x + 13, y + 13), fill=DARK + (235,))
        draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=WHITE + (150,))
    centred(draw, (0, 90, 512, 160), label, font("ShareTechMono-Regular.ttf", 48), WHITE + (205,))
    return weather(image, 0.28, 4)


def step_mark(text="NO STEP"):
    image = new(512, 128)
    draw = ImageDraw.Draw(image)
    centred(draw, (0, 0, 512, 128), text, font("Rajdhani-SemiBold.ttf", 84), WHITE + (235,))
    return weather(image, 0.35, 5)


DECALS = {
    "D_Registration": registration,
    "D_Hazard_Stripes": hazard_stripes,
    "D_Caution_Thrust": caution,
    "D_Hatch_Access": hatch,
    "D_No_Step": step_mark,
}


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, make in sorted(DECALS.items()):
        image = make()
        path = os.path.join(OUT, name + ".png")
        image.save(path)
        alpha = np.asarray(image, dtype=np.float32)[..., 3] / 255.0
        print("%-20s %dx%d, %.0f %% of it is paint -> %s" % (
            name, image.width, image.height, 100.0 * (alpha > 0.1).mean(), os.path.relpath(path, REPO)))


if __name__ == "__main__":
    main()
