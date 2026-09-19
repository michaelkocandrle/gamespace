"""Tiling micro-detail textures for ship hulls (the close-up crispness Star Citizen gets from layered
materials, not from a bigger paint texture).

    python Tools/Assets/generate_detail_textures.py

Writes (1024 x 1024, seamless, overwritten every run - they are generated, not hand-made):

    ArtSource/Ships/Shared/Textures/T_Ship_Detail_N.png       normal map: rolled-metal grain and scratches
    ArtSource/Ships/Shared/Textures/T_Ship_Detail_Grunge.png  grey blotches: roughness breakup, 1 m across

The ship master M_Ship_PBR projects them on the hull in the ship's own space (triplanar, ~30 cm across),
so the detail holds up from any distance and does not swim when the ship moves. An AI model's own paint
is one 4K texture over a 14 m hull (~3 mm per pixel), which is why it goes soft as soon as the camera
comes close; this layer adds the missing surface under it.

Plain numpy and PIL, no Unreal. Tools/Assets/ship_materials.py imports the PNGs into the game.
"""

import os

import numpy as np
from PIL import Image

SIZE = 1024
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "ArtSource", "Ships", "Shared", "Textures")


def tiling_noise(size, cells, rng, octaves=1, gain=0.5):
    """Seamless value noise: a random lattice of `cells` wrapped around, smoothly interpolated."""
    total = np.zeros((size, size), dtype=np.float64)
    amplitude = 1.0
    weight = 0.0
    for octave in range(octaves):
        count = max(2, int(cells * 2 ** octave))
        lattice = rng.random((count, count))
        # Wrap by repeating the first row and column, then sample with a smoothstep between cells.
        wrapped = np.pad(lattice, ((0, 1), (0, 1)), mode="wrap")
        coordinates = np.linspace(0.0, count, size, endpoint=False)
        index = np.floor(coordinates).astype(int)
        fraction = coordinates - index
        smooth = fraction * fraction * (3.0 - 2.0 * fraction)
        x0, x1 = wrapped[index][:, index], wrapped[index][:, index + 1]
        top = x0 * (1.0 - smooth)[None, :] + x1 * smooth[None, :]
        x0, x1 = wrapped[index + 1][:, index], wrapped[index + 1][:, index + 1]
        bottom = x0 * (1.0 - smooth)[None, :] + x1 * smooth[None, :]
        total += amplitude * (top * (1.0 - smooth)[:, None] + bottom * smooth[:, None])
        weight += amplitude
        amplitude *= gain
    return total / weight


def scratches(size, count, rng):
    """Fine straight grooves, wrapped at the edges: what a hull picks up in service."""
    marks = np.zeros((size, size), dtype=np.float64)
    for _ in range(count):
        angle = rng.random() * np.pi
        length = rng.integers(size // 20, size // 7)
        x, y = rng.integers(0, size), rng.integers(0, size)
        depth = 0.10 + 0.45 * rng.random() ** 2
        steps = np.arange(length)
        xs = (x + np.cos(angle) * steps).astype(int) % size
        ys = (y + np.sin(angle) * steps).astype(int) % size
        # Fade the ends, so a scratch does not start and stop abruptly.
        fade = np.minimum(1.0, np.minimum(steps, length - steps) / (length * 0.25 + 1.0))
        np.maximum.at(marks, (ys, xs), depth * fade)
    return marks


def blur(image, radius=1):
    out = image.copy()
    for shift in range(1, radius + 1):
        out += np.roll(image, shift, 0) + np.roll(image, -shift, 0) + np.roll(image, shift, 1) + np.roll(image, -shift, 1)
    return out / (1.0 + 4.0 * radius)


def normal_map(height, strength):
    """Tangent-space normal from a height field, wrapped (OpenGL: +Y up, as Blender bakes them)."""
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * strength
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * strength
    normal = np.stack([-dx, -dy, np.ones_like(height)], axis=-1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    return normal


def main():
    rng = np.random.default_rng(20260920)
    os.makedirs(OUT, exist_ok=True)

    # The surface: fine grain (rolled metal), a slower waviness (panels never lie perfectly flat), scratches.
    grain = tiling_noise(SIZE, 64, rng, octaves=3, gain=0.55)
    waves = tiling_noise(SIZE, 8, rng, octaves=2, gain=0.5)
    marks = blur(scratches(SIZE, 260, rng), 1)
    height = 0.55 * grain + 0.6 * waves - 0.5 * marks
    height = blur(height, 1)
    normal = normal_map(height, strength=7.0)
    image = ((normal * 0.5 + 0.5) * 255.0).clip(0, 255).astype(np.uint8)
    normal_path = os.path.join(OUT, "T_Ship_Detail_N.png")
    Image.fromarray(image, "RGB").save(normal_path)

    # Grunge: large blotches for the roughness, so the paint is not uniformly polished.
    grunge = tiling_noise(SIZE, 3, rng, octaves=4, gain=0.55)
    grunge = (grunge - grunge.min()) / (grunge.max() - grunge.min())
    # Keep it gentle: the middle of the range is the paint as baked.
    grunge = 0.5 + 0.9 * (grunge - 0.5)
    grunge_path = os.path.join(OUT, "T_Ship_Detail_Grunge.png")
    Image.fromarray((grunge * 255.0).clip(0, 255).astype(np.uint8), "L").save(grunge_path)

    print("detail textures: %s, %s" % (normal_path, grunge_path))


if __name__ == "__main__":
    main()
