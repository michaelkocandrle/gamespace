"""Tonal numbers of shots against the Star Citizen references (HANDOFF point 64/65).

    python Tools/Shots/measure_look.py <shots folder>

Mean and percentiles of luminance, saturation, B/R (warm < 1 < cool) and fine detail (mean gradient),
the same measures as in the comparison of 23. 9. 2026. Reference ranges for interiors (SC corridor,
seats, Constellation cockpit): mean 0.13-0.23, p50 0.08-0.18, p90 0.32-0.53, p99 0.56-0.88,
B/R 0.72-1.05, detail 0.024-0.035.
"""
import glob
import os
import sys

import numpy as np
from PIL import Image


def stats(path):
    im = Image.open(path).convert("RGB")
    im = im.resize((960, int(960 * im.size[1] / im.size[0])))
    a = np.asarray(im).astype(float) / 255
    a[:30, 780:] = a[30:60, 780:]                 # the FPS counter
    l = a @ [0.2126, 0.7152, 0.0722]
    mx, mn = a.max(2), a.min(2)
    sat = ((mx - mn) / np.maximum(mx, 1e-3))[l > 0.05].mean()
    detail = np.abs(np.diff(l, axis=1)).mean() + np.abs(np.diff(l, axis=0)).mean()
    m = a[(l > 0.05) & (l < 0.9)]
    r, g, b = m.mean(0)
    p10, p50, p90, p99 = np.percentile(l, [10, 50, 90, 99])
    return "mean %.2f p10 %.2f p50 %.2f p90 %.2f p99 %.2f | sat %.2f B/R %.2f | detail %.4f" % (
        l.mean(), p10, p50, p90, p99, sat, b / r, detail)


for f in sorted(glob.glob(os.path.join(sys.argv[1], "*.png")))[1:]:
    print("LOOK %-24s %s" % (os.path.basename(f)[:-4], stats(f)))
