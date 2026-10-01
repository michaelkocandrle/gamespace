"""Crops of a drawing sheet for the critic of technical drawings (the exterior and interior sheets, dossier body 3-6):
the whole sheet scaled down and regions in paper millimetres at full resolution (at most 2000 px a side).

    python Tools/Review/sheet_crops.py <sheet.png> <out_dir> name=x0,y0,x1,y1 ... [--paper 1189x841]

Regions are paper millimetres from the sheet's bottom left corner (A0 landscape by default). Writes
00_celkovy_pohled.png and <nn>_<name>.png; prints each file with its size.
"""
import argparse
import os

from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet")
    ap.add_argument("out")
    ap.add_argument("regions", nargs="+")
    ap.add_argument("--paper", default="1189x841")
    a = ap.parse_args(argv)
    pw, ph = (float(v) for v in a.paper.split("x"))
    os.makedirs(a.out, exist_ok=True)
    im = Image.open(a.sheet).convert("RGB")
    k = im.width / pw
    whole = im.copy()
    whole.thumbnail((2400, 2400), Image.LANCZOS)
    p = os.path.join(a.out, "00_celkovy_pohled.png")
    whole.save(p)
    print("CROPS", p, whole.size)
    for i, spec in enumerate(a.regions, 1):
        name, box = spec.split("=")
        x0, y0, x1, y1 = (float(v) for v in box.split(","))
        c = im.crop((int(x0 * k), int((ph - y1) * k), int(x1 * k), int((ph - y0) * k)))
        if max(c.size) > 2000:
            c.thumbnail((2000, 2000), Image.LANCZOS)
        p = os.path.join(a.out, "%02d_%s.png" % (i, name))
        c.save(p)
        print("CROPS", p, c.size)


if __name__ == "__main__":
    main()
