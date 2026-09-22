"""Terrain textures from Poly Haven (polyhaven.com, CC0) into ArtSource/Textures/PolyHaven/<asset>/.

    python Tools/Assets/fetch_polyhaven.py [asset ...]
    python Tools/Assets/fetch_polyhaven.py --models [asset ...]

Downloads the 2K JPG diffuse, OpenGL normal and ARM (occlusion, roughness, metallic) maps through
the public API. Skips files that are already there, and writes each diffuse map's average colour
(linear) to means.json: the terrain material divides by it, so a texture adds detail without
changing the planet's colours. The terrain material imports them with build_space_scene.py
(TERRAIN_TEXTURES). Needs Pillow (pip install pillow).
"""

import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT = os.path.join(REPO, "ArtSource", "Textures", "PolyHaven")
ASSETS = ["rock_face_03", "gravelly_sand", "dry_riverbed_rock"]
MAPS = {"Diffuse": "diff", "nor_gl": "nor_gl", "arm": "arm"}
# The API refuses Python's default user agent (403); it asks callers to name themselves.
HEADERS = {"User-Agent": "gamespace-texture-fetch/1.0"}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS))


def fetch(asset):
    files = json.load(get("https://api.polyhaven.com/files/" + asset))
    folder = os.path.join(ROOT, asset)
    os.makedirs(folder, exist_ok=True)
    for key, short in MAPS.items():
        entry = files[key]["2k"]["jpg"]
        path = os.path.join(folder, "%s_%s_2k.jpg" % (asset, short))
        if not os.path.exists(path):
            with open(path, "wb") as out:
                out.write(get(entry["url"]).read())
        print("%s  %.1f MB" % (os.path.relpath(path, REPO), os.path.getsize(path) / 1e6))


MODELS = ["namaqualand_boulder_02", "namaqualand_boulder_03", "boulder_01", "rock_09"]
MODEL_ROOT = os.path.join(REPO, "ArtSource", "Models", "PolyHaven")


def fetch_model(asset):
    """The 2K glTF with its buffer and textures, laid out as the .gltf refers to them."""
    files = json.load(get("https://api.polyhaven.com/files/" + asset))
    entry = files["gltf"]["2k"]["gltf"]
    folder = os.path.join(MODEL_ROOT, asset)
    for relative, item in [(os.path.basename(entry["url"]), entry)] + list(entry.get("include", {}).items()):
        path = os.path.join(folder, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            with open(path, "wb") as out:
                out.write(get(item["url"]).read())
    total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(folder) for f in fs)
    print("%s  %.1f MB" % (os.path.relpath(folder, REPO), total / 1e6))


def mean_linear(path):
    from PIL import Image
    image = Image.open(path).convert("RGB").resize((256, 256))
    pixels = list(image.getdata())
    to_linear = lambda c: (c / 255.0) ** 2.2
    return [sum(to_linear(p[k]) for p in pixels) / len(pixels) for k in range(3)]


if sys.argv[1:2] == ["--models"]:
    for name in sys.argv[2:] or MODELS:
        fetch_model(name)
    sys.exit(0)

means_path = os.path.join(ROOT, "means.json")
means = json.load(open(means_path)) if os.path.exists(means_path) else {}
for name in sys.argv[1:] or ASSETS:
    fetch(name)
    means[name] = mean_linear(os.path.join(ROOT, name, "%s_diff_2k.jpg" % name))
    print("%s mean %s" % (name, ", ".join("%.3f" % c for c in means[name])))
json.dump(means, open(means_path, "w"), indent=2)
