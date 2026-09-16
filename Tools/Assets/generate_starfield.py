"""Generates a procedural star field as an equirectangular (long-lat) Radiance .hdr.

Runs with the system Python (numpy), NOT inside Unreal:

    python Tools/Assets/generate_starfield.py <out.hdr>

Unreal imports a 2:1 long-lat .hdr as a TextureCube. build_space_scene.py does that import;
the .hdr itself is a build intermediate and is not committed.

The output is deterministic (fixed seed), so regenerating gives the same sky.
"""

import math
import sys

import numpy as np

WIDTH, HEIGHT = 4096, 2048
SEED = 20260916

# Star counts. The band stars cluster around a tilted great circle for a Milky Way-like streak.
FIELD_STARS = 24000
BAND_STARS = 30000
BAND_TILT_DEG = 62.0
BAND_SIGMA_DEG = 7.0


def random_directions(rng, count):
    """Uniform on the unit sphere (Z up, matching Unreal)."""
    z = rng.uniform(-1.0, 1.0, count)
    phi = rng.uniform(0.0, 2.0 * math.pi, count)
    r = np.sqrt(1.0 - z * z)
    return np.stack([r * np.cos(phi), r * np.sin(phi), z], axis=1)


def band_directions(rng, count):
    """Clustered around a great circle, then tilted out of the XY plane."""
    lon = rng.uniform(0.0, 2.0 * math.pi, count)
    lat = np.radians(rng.normal(0.0, BAND_SIGMA_DEG, count))
    d = np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], axis=1)
    t = math.radians(BAND_TILT_DEG)
    rot = np.array([[1, 0, 0], [0, math.cos(t), -math.sin(t)], [0, math.sin(t), math.cos(t)]])
    return d @ rot.T


def star_fluxes(rng, count):
    """Few bright, many faint: a magnitude-like distribution mapped to linear flux."""
    magnitude = np.clip(7.0 - rng.exponential(1.25, count), -0.5, 7.0)
    return 10.0 ** (-0.4 * (magnitude - 6.0))  # magnitude 6 -> 1.0, magnitude 1 -> 100


def star_colors(rng, count):
    """Blend orange -> white -> blue-white, weighted towards white."""
    t = np.clip(rng.normal(0.5, 0.22, count), 0.0, 1.0)[:, None]
    warm = np.array([1.0, 0.72, 0.45])
    white = np.array([1.0, 0.97, 0.93])
    cool = np.array([0.72, 0.83, 1.0])
    lo = warm + (white - warm) * np.clip(t * 2.0, 0.0, 1.0)
    return lo + (cool - white) * np.clip(t * 2.0 - 1.0, 0.0, 1.0)


def splat(image, directions, fluxes, colors):
    """Draws each star as a small Gaussian, widened horizontally by 1/cos(latitude) so it stays
    round on the sphere after the long-lat projection."""
    x, y, z = directions.T
    lon = np.arctan2(y, x)
    lat = np.arcsin(np.clip(z, -1.0, 1.0))
    px = (lon / (2.0 * math.pi) + 0.5) * WIDTH
    py = (0.5 - lat / math.pi) * HEIGHT

    # Bright stars are drawn larger; flux is conserved by normalising the kernel.
    sigma_y = np.clip(0.45 + 0.18 * np.log10(np.maximum(fluxes, 1e-3) + 1.0), 0.45, 1.2)
    sigma_x = sigma_y / np.maximum(np.cos(lat), 0.08)

    radius_y = 3
    for i in range(len(fluxes)):
        rx = int(min(math.ceil(sigma_x[i] * 3.0), 24))
        xs = np.arange(int(px[i]) - rx, int(px[i]) + rx + 1)
        ys = np.arange(int(py[i]) - radius_y, int(py[i]) + radius_y + 1)
        ys = ys[(ys >= 0) & (ys < HEIGHT)]
        gx = np.exp(-0.5 * ((xs + 0.5 - px[i]) / sigma_x[i]) ** 2)
        gy = np.exp(-0.5 * ((ys + 0.5 - py[i]) / sigma_y[i]) ** 2)
        kernel = np.outer(gy, gx)
        kernel /= kernel.sum()
        # Horizontal wrap across the seam at +/-180 degrees longitude.
        image[np.ix_(ys, xs % WIDTH)] += kernel[:, :, None] * (fluxes[i] * colors[i])[None, None, :]


def milky_way_glow(rng):
    """Very faint diffuse light along the band, broken up by low-frequency noise."""
    lat = (0.5 - (np.arange(HEIGHT) + 0.5) / HEIGHT) * math.pi
    lon = ((np.arange(WIDTH) + 0.5) / WIDTH - 0.5) * 2.0 * math.pi
    lon_g, lat_g = np.meshgrid(lon, lat)
    d = np.stack([np.cos(lat_g) * np.cos(lon_g), np.cos(lat_g) * np.sin(lon_g), np.sin(lat_g)], axis=-1)
    t = math.radians(BAND_TILT_DEG)
    # Distance from the band plane = component along the band's tilted normal.
    normal = np.array([0.0, -math.sin(t), math.cos(t)])
    band_lat = np.degrees(np.arcsin(np.clip(d @ normal, -1.0, 1.0)))
    glow = np.exp(-0.5 * (band_lat / (BAND_SIGMA_DEG * 1.3)) ** 2)

    patchy = np.ones_like(glow)
    for _ in range(6):
        k = rng.normal(0.0, 3.0, 3)
        patchy += 0.35 * np.sin(d @ k + rng.uniform(0, 2 * math.pi))
    glow *= np.clip(patchy, 0.0, None) * 0.012
    return glow[:, :, None] * np.array([0.85, 0.88, 1.0])[None, None, :]


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
    rng = np.random.default_rng(SEED)
    image = np.zeros((HEIGHT, WIDTH, 3), dtype=np.float64)

    image += milky_way_glow(rng)
    for directions in (random_directions(rng, FIELD_STARS), band_directions(rng, BAND_STARS)):
        count = len(directions)
        splat(image, directions, star_fluxes(rng, count), star_colors(rng, count))

    header = ("#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n-Y %d +X %d\n" % (HEIGHT, WIDTH)).encode("ascii")
    with open(out_path, "wb") as f:
        f.write(header)
        f.write(to_flat_rgbe(image).tobytes())
    print("wrote %s  (%dx%d, peak %.1f, mean %.5f)" % (out_path, WIDTH, HEIGHT, image.max(), image.mean()))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "starfield.hdr")
