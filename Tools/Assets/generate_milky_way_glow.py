"""Generates the diffuse Milky Way glow as an equirectangular (long-lat) Radiance .hdr.

Runs with the system Python (numpy), NOT inside Unreal:

    python Tools/Assets/generate_milky_way_glow.py Intermediate/GeneratedAssets/milky_way_glow.hdr

Only the soft glow lives in this texture. The stars themselves are computed per pixel in
M_Starfield_Sky, so they stay sharp at any resolution; a star texture cannot, because a cubemap
texel covers more than a screen pixel and bilinear filtering turns points into smudges.

Unreal imports a 2:1 long-lat .hdr as a TextureCube; build_space_scene.py does that import.
The output is deterministic (fixed seed).
"""

import math
import sys

import numpy as np

# Low resolution is fine: the glow has no detail finer than a few degrees.
WIDTH, HEIGHT = 2048, 1024
SEED = 20260916

# Same plane as the star density band in M_Starfield_Sky (tilt 62 degrees about X).
BAND_TILT_DEG = 62.0
BAND_SIGMA_DEG = 9.0


def milky_way_glow(rng):
    """Glow along the band, broken up by low-frequency noise. Peak roughly 1."""
    lat = (0.5 - (np.arange(HEIGHT) + 0.5) / HEIGHT) * math.pi
    lon = ((np.arange(WIDTH) + 0.5) / WIDTH - 0.5) * 2.0 * math.pi
    lon_g, lat_g = np.meshgrid(lon, lat)
    d = np.stack([np.cos(lat_g) * np.cos(lon_g), np.cos(lat_g) * np.sin(lon_g), np.sin(lat_g)], axis=-1)

    t = math.radians(BAND_TILT_DEG)
    normal = np.array([0.0, -math.sin(t), math.cos(t)])
    band_lat = np.degrees(np.arcsin(np.clip(d @ normal, -1.0, 1.0)))
    core = np.exp(-0.5 * (band_lat / BAND_SIGMA_DEG) ** 2)
    halo = 0.25 * np.exp(-0.5 * (band_lat / (BAND_SIGMA_DEG * 2.5)) ** 2)

    # Patchiness: a sum of random plane waves over the sphere is smooth, seamless and cheap.
    patchy = np.zeros(core.shape)
    for octave in range(3):
        for _ in range(5):
            k = rng.normal(0.0, 2.5 * (2 ** octave), 3)
            patchy += np.sin(d @ k + rng.uniform(0, 2 * math.pi)) / (2 ** octave)
    patchy = np.clip(0.6 + 0.12 * patchy, 0.05, None)

    glow = (core + halo) * patchy
    glow /= glow.max()
    # Faintly blue-white, a little warmer in the densest parts.
    tint = np.stack([0.80 + 0.15 * core, 0.84 + 0.08 * core, 1.0 - 0.05 * core], axis=-1)
    return glow[..., None] * tint


def to_flat_rgbe(image):
    """Float RGB -> flat (uncompressed) RGBE bytes, safe for Unreal's HDR reader."""
    peak = image.max(axis=2)
    mantissa, exponent = np.frexp(peak)
    scale = np.where(peak > 1e-32, mantissa * 256.0 / np.maximum(peak, 1e-32), 0.0)
    rgbe = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
    rgbe[..., :3] = np.clip(image * scale[..., None], 0, 255).astype(np.uint8)
    rgbe[..., 3] = np.where(peak > 1e-32, exponent + 128, 0).astype(np.uint8)

    # Byte patterns the reader treats as run-length markers rather than pixels:
    #  (1,1,1,n) repeats the previous pixel; a scanline starting (2,2,b<128,...) switches to
    #  new-style RLE. Nudge the first to (2,2,2,n) and blank the first column.
    marker = (rgbe[..., 0] == 1) & (rgbe[..., 1] == 1) & (rgbe[..., 2] == 1)
    rgbe[marker, :3] = 2
    rgbe[:, 0, :] = 0
    return rgbe


def main(out_path):
    image = milky_way_glow(np.random.default_rng(SEED))
    header = ("#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n-Y %d +X %d\n" % (HEIGHT, WIDTH)).encode("ascii")
    with open(out_path, "wb") as f:
        f.write(header)
        f.write(to_flat_rgbe(image).tobytes())
    print("wrote %s  (%dx%d, peak %.2f, mean %.4f)" % (out_path, WIDTH, HEIGHT, image.max(), image.mean()))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "milky_way_glow.hdr")
