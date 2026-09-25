"""The Quaternius Modular Sci-Fi MegaKit's trim textures (CC0) in the gamespace palette, for ship interiors.

    python Tools/Assets/tone_kit_textures.py

Reads the kit zip (ArtSource/ThirdParty/Quaternius/ModularSciFiMegaKit.zip, not in git - README there) and
writes ArtSource/Ships/Shared/Kit/T_Kit_<Set>_{BC,N,ORM}.png, one set per kit texture family:

    Trim01    panels with frames and light slots (the kit's red accents -> Halcyon orange)
    Trim02    long wall trims, greeble strips, hazard bars (red -> orange)
    Trim02B   the same sheet without the red (floors, the variation pieces)
    Trim03    plain painted metal with soft grunge
    Cables    the dark cable / conduit sheet
    Padded    upholstered wall padding (quilted, orange)
    PaddedGrey  the same padding in charcoal (cockpit)

Normal maps are OpenGL (glTF) - ship_materials.import_texture flips green for Unreal. ORM is glTF's
(R occlusion, G roughness, B metallic), which is what M_Ship_PBR reads. The grey of the panels stays
neutral; each material instance tints it (BaseColorTint in <Ship>_setup.json), so one set gives several
panel tones.
"""
import io
import os
import zipfile

import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ZIP = os.path.join(REPO, "ArtSource", "ThirdParty", "Quaternius", "ModularSciFiMegaKit.zip")
OUT = os.path.join(REPO, "ArtSource", "Ships", "Shared", "Kit")
TEX = "Modular SciFi MegaKit[Standard]/Textures/"
# Halcyon Freightworks orange (the exterior's accent 0.72, 0.17, 0.02 linear) in sRGB
ORANGE = np.array([0.87, 0.45, 0.08])

SETS = {
    "Trim01": ("T_Trim_01_BaseColor_Red.png", "T_Trim_01_Normal.png", "T_Trim_01_ORM.png"),
    "Trim02": ("T_Trim_02_BaseColor_Red.png", "T_Trim_02_Normal.png", "T_Trim_02_ORM.png"),
    "Trim02B": ("T_Trim_02_BaseColor.png", "T_Trim_02_Normal.png", "T_Trim_02_ORM.png"),
    "Trim03": ("T_Trim_03_BaseColor.png", "T_Trim_03_Normal.png", "T_Trim_03_ORM.png"),
    "Cables": ("T_Trim_03_Cables.png", "T_Trim_03_Normal.png", "T_Trim_03_ORM.png"),
    "Padded": ("T_PaddedWall_BaseColor.png", "T_PaddedWall_Normal.png", "T_PaddedWall_ORM.png"),
    "PaddedGrey": ("T_PaddedWall_BaseColor.png", "T_PaddedWall_Normal.png", "T_PaddedWall_ORM.png"),
}


def recolour(img):
    """The kit's red accents to orange, keeping their shading; everything else a touch warmer grey."""
    a = np.asarray(img.convert("RGB")).astype(np.float32) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    redness = np.clip((r - np.maximum(g, b) - 0.12) / 0.2, 0.0, 1.0)[..., None]
    lum = (0.3 * r + 0.59 * g + 0.11 * b)[..., None]
    orange = ORANGE * np.clip(lum / 0.3, 0.3, 1.4)
    grey = np.repeat(lum, 3, axis=2) * np.array([1.02, 1.0, 0.97])
    sat = a.max(axis=2, keepdims=True) - a.min(axis=2, keepdims=True)
    # keep coloured bits that are not red (the kit's small yellow lamps); neutral pixels go warm grey
    keep = np.clip((sat - 0.08) / 0.1, 0.0, 1.0) * (1.0 - redness)
    out = grey * (1.0 - keep) + a * keep
    out = out * (1.0 - redness) + orange * redness
    return Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))


def main():
    os.makedirs(OUT, exist_ok=True)
    with zipfile.ZipFile(ZIP) as z:
        for name, (bc, n, orm) in SETS.items():
            img = Image.open(io.BytesIO(z.read(TEX + bc)))
            if name == "Padded":
                base = img.convert("RGB")
            elif name == "PaddedGrey":
                # the quilted padding in charcoal (cockpit tub, seat surrounds): luminance only, a touch warm
                a = np.asarray(img.convert("RGB")).astype(np.float32) / 255.0
                lum = (0.3 * a[..., 0] + 0.59 * a[..., 1] + 0.11 * a[..., 2])[..., None]
                base = Image.fromarray((np.clip(np.repeat(lum, 3, 2) * np.array([0.62, 0.6, 0.58]), 0, 1) * 255 + 0.5).astype(np.uint8))
            else:
                base = recolour(img)
            base.save(os.path.join(OUT, "T_Kit_%s_BC.png" % name), optimize=True)
            for suffix, src in (("N", n), ("ORM", orm)):
                Image.open(io.BytesIO(z.read(TEX + src))).convert("RGB").save(os.path.join(OUT, "T_Kit_%s_%s.png" % (name, suffix)), optimize=True)
            print("KITTEX", name)


if __name__ == "__main__":
    main()
