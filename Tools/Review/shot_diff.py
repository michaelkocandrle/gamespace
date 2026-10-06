"""Pixel difference of two shot sets with the same names (lesson P25: a kit material change must not change the ships).

    python Tools/Review/shot_diff.py <set A> <set B> [--out <dir>]

Per shot: mean absolute difference of luminance (0-255), the 99th percentile and the share of pixels changed by more
than 12 levels. Compare it with two runs of the same build (the render noise of TSR / MegaLights) before calling a
difference real. With --out also writes an amplified difference image per shot. Prints SHOTDIFF lines.
"""
import glob
import os
import sys

import numpy as np
from PIL import Image


def main():
    a_dir, b_dir = sys.argv[1], sys.argv[2]
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    if out:
        os.makedirs(out, exist_ok=True)
    for pa in sorted(glob.glob(os.path.join(a_dir, "*.png"))):
        name = os.path.basename(pa)
        pb = os.path.join(b_dir, name)
        if not os.path.exists(pb) or "warmup" in name:
            continue
        a = np.asarray(Image.open(pa).convert("L"), dtype=np.float32)
        b = np.asarray(Image.open(pb).convert("L"), dtype=np.float32)
        d = np.abs(a - b)
        print("SHOTDIFF %-28s mean %5.2f  p99 %5.1f  changed>12 %5.2f %%" % (name, d.mean(), np.percentile(d, 99),
                                                                           100.0 * (d > 12).mean()))
        if out:
            Image.fromarray(np.clip(d * 4, 0, 255).astype(np.uint8)).save(os.path.join(out, "diff_" + name))


if __name__ == "__main__":
    main()
