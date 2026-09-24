"""Large markings of the Wayfarer, readable from the chase camera and further: the name along the upper side,
the registration on the nose, the Halcyon Freightworks mark, big hazard zones at the exhausts and the ramp.

    python Tools/Assets/generate_big_decals.py

Writes ArtSource/Ships/Shared/Decals/D_Big_*.png (RGBA, white or tinted shapes on transparent; the colour
comes from DecalTint in <Ship>_setup.json, so one texture serves light and dark paint). The type is the
project's own fonts (Content/UI/Fonts). Projected as deferred decals (M_Ship_Decal) - the mesh-decal atlas
has a fixed 0.5 mm texel and would need metres of it for a 4 m name.
"""
import os

from PIL import Image, ImageDraw, ImageFont

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "ArtSource", "Ships", "Shared", "Decals")
FONTS = os.path.join(REPO, "Content", "UI", "Fonts")
W = (255, 255, 255, 255)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def text_image(text, fnt, height, pad=0.06, spacing=0):
    f = font(fnt, height)
    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    l, t, r, b = probe.textbbox((0, 0), text, font=f)
    w = int((r - l) * (1 + 2 * pad)) + spacing * len(text)
    h = int((b - t) * (1 + 4 * pad))
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = (w - (r - l) - spacing * (len(text) - 1)) // 2 - l
    for ch in text:
        d.text((x, (h - (b - t)) // 2 - t), ch, font=f, fill=W)
        cl, _, cr, _ = d.textbbox((0, 0), ch, font=f)
        x += (cr - cl) + spacing + int(f.getlength(ch) - (cr - cl))
    return im


def pow2(im):
    w, h = im.size
    tw = 1 << (w - 1).bit_length()
    th = 1 << (h - 1).bit_length()
    out = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    out.paste(im.resize((tw, th), Image.LANCZOS), (0, 0))
    return out


def logo():
    """Halcyon Freightworks: a half sun over a horizon bar (the halcyon days) and the name."""
    im = Image.new("RGBA", (2048, 1024), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy, r = 360, 560, 300
    d.pieslice((cx - r, cy - r, cx + r, cy + r), 180, 360, fill=W)
    d.pieslice((cx - r + 70, cy - r + 70, cx + r - 70, cy + r - 70), 180, 360, fill=(0, 0, 0, 0))
    d.pieslice((cx - 130, cy - 130, cx + 130, cy + 130), 180, 360, fill=W)
    for k in range(3):
        d.rectangle((cx - r - 20, cy + 30 + k * 70, cx + r + 20, cy + 70 + k * 70 - k * 8), fill=W)
    f1, f2 = font("Rajdhani-SemiBold.ttf", 300), font("Rajdhani-Medium.ttf", 150)
    d.text((760, 250), "HALCYON", font=f1, fill=W)
    d.text((770, 600), "FREIGHTWORKS", font=f2, fill=W)
    return im


def hazard(text):
    """Large hazard zone: diagonal bands with a text panel in the middle (colour from the tint)."""
    im = Image.new("RGBA", (2048, 512), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for k in range(-4, 40):
        x = k * 110
        d.polygon([(x, 512), (x + 55, 512), (x + 55 + 300, 0), (x + 300, 0)], fill=W)
    d.rectangle((620, 150, 1428, 362), fill=(0, 0, 0, 0))
    f = font("Rajdhani-SemiBold.ttf", 150)
    l, t, r, b = d.textbbox((0, 0), text, font=f)
    d.text((1024 - (r - l) // 2 - l, 256 - (b - t) // 2 - t), text, font=f, fill=W)
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    items = {
        "D_Big_Wayfarer": pow2(text_image("WAYFARER", "Rajdhani-SemiBold.ttf", 400, spacing=60)),
        "D_Big_Registration": pow2(text_image("HF-0417", "Rajdhani-SemiBold.ttf", 400, spacing=30)),
        "D_Big_Logo": logo(),
        "D_Big_Hazard_Exhaust": hazard("EXHAUST"),
        "D_Big_Hazard_Ramp": hazard("RAMP"),
    }
    for name, im in items.items():
        im.save(os.path.join(OUT, name + ".png"))
        print("BIGDECAL", name, im.size)


if __name__ == "__main__":
    main()
