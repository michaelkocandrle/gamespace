"""Catalog sheet of the interior kit (step 4/6 of the kit brief, 26. 9. 2026): every built part of a batch in the
same neutral studio light, 3/4 and front view, name, size (L x depth x height), triangles against the budget,
sockets. Reads ArtSource/Kit/Export/kit_manifest.json and the renders of Tools/Kit/kit_build.py.

    python Tools/Kit/kit_catalog.py [batch] [out.png]      (default batch 1 -> Docs/Kit/catalog_batch1.png)
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    batch = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "Docs", "Kit", "catalog_batch%d.png" % batch)
    parts = json.load(open(os.path.join(ROOT, "ArtSource", "Kit", "Export", "kit_manifest.json"), encoding="utf-8"))["parts"]
    rows = [(n, p) for n, p in sorted(parts.items(), key=lambda kv: (kv[1]["family"], kv[1]["variant"], -kv[1]["length_m"]))
            if p.get("batch") == batch and p.get("renders")]
    F = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 20)
    FS = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 17)
    FT = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 30)
    cw, ch = 380, 380
    cols = 4
    cell_w, cell_h = 2 * cw + 20, ch + 96
    n = len(rows)
    grid_rows = (n + cols - 1) // cols
    img = Image.new("RGB", (cols * cell_w + 20, grid_rows * cell_h + 90), (26, 27, 30))
    d = ImageDraw.Draw(img)
    titles = {1: "stěnové moduly (průřez W)", 2: "portály, strop, koncové stěny, rohy, přechod"}
    d.text((20, 18), "Interiérový kit – dávka %d: %s, %d dílů, stejné neutrální světlo, dva pohledy" % (batch, titles.get(batch, ""), n),
           font=FT, fill=(235, 235, 235))
    for i, (name, p) in enumerate(rows):
        x = 10 + (i % cols) * cell_w
        y = 70 + (i // cols) * cell_h
        for k, tag in enumerate(("34", "front")):
            path = os.path.join(ROOT, p["renders"][tag])
            if os.path.exists(path):
                im = Image.open(path).convert("RGB").resize((cw, ch))
                img.paste(im, (x + k * (cw + 4), y))
        dims = p["dims_m"]
        d.text((x + 4, y + ch + 6), name.replace("SM_Kit_", ""), font=F, fill=(255, 200, 110))
        d.text((x + 4, y + ch + 34), "%.2f × %.2f × %.2f m   |   %d tris / %d   |   decaly %d   |   světla %d" % (
            dims[0], dims[1], dims[2], p["tris"], p["tri_budget"], p.get("decals", 0),
            sum(1 for s in p["sockets"] if s.startswith("SOCKET_Light"))), font=FS, fill=(210, 210, 210))
        d.text((x + 4, y + ch + 58), "kolize %d UCX, sockety %d" % (p["collision_hulls"], len(p["sockets"])), font=FS, fill=(150, 150, 150))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out)
    print("CATALOG", out, n, "parts")


if __name__ == "__main__":
    main()
