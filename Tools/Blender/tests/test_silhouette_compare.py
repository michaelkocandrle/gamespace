"""Tests for Tools/Blender/silhouette_compare.py.

    python Tools/Blender/tests/test_silhouette_compare.py

Plain Python (numpy + Pillow). The last test renders Blender's default cube headless and is skipped
when Blender 5.2 is not installed.
"""
import json
import os
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import silhouette_compare as sc  # noqa: E402

FAILED = []


def check(name, cond, detail=""):
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))
    if not cond:
        FAILED.append(name)


def mask_from_shape(size, draw_fn):
    img = Image.new("L", size, 0)
    draw_fn(ImageDraw.Draw(img))
    return np.asarray(img) > 127


def concept(path, size, draw_fn, bg=(200, 200, 205), fg=(70, 80, 95)):
    img = Image.new("RGB", size, bg)
    draw_fn(ImageDraw.Draw(img), fg)
    img.save(path)


def test_identical_and_shifted():
    a = mask_from_shape((400, 300), lambda d: d.rectangle([50, 80, 300, 160], fill=255))
    # Same shape, other place and scale: normalisation must make it identical.
    b = mask_from_shape((900, 700), lambda d: d.rectangle([300, 100, 800, 260], fill=255))
    stats, _, _ = sc.compare_masks(a, a)
    check("identical IoU 1", stats["iou"] > 0.999, stats)
    stats, _, _ = sc.compare_masks(a, b)
    check("moved + scaled IoU ~1", stats["iou"] > 0.97, stats)
    check("aspect reported", abs(stats["aspect_model"] - stats["aspect_ref"]) < 0.05, stats)


def test_different_shape_scores_lower():
    rect = mask_from_shape((400, 400), lambda d: d.rectangle([50, 150, 350, 250], fill=255))
    tri = mask_from_shape((400, 400), lambda d: d.polygon([(50, 250), (350, 250), (50, 150)], fill=255))
    stats, m, r = sc.compare_masks(tri, rect)
    check("triangle vs rectangle IoU ~0.5", 0.4 < stats["iou"] < 0.6, stats)
    check("missing reported", stats["missing_pct"] > 30 and stats["extra_pct"] < 5, stats)


def test_mirror():
    nose_right = mask_from_shape((400, 200), lambda d: d.polygon([(20, 60), (380, 100), (20, 140)], fill=255))
    nose_left = nose_right[:, ::-1]
    stats, _, _ = sc.compare_masks(nose_right, nose_left)
    check("mirrored reference matched", stats["iou"] > 0.99 and stats["mirrored"], stats)
    stats, _, _ = sc.compare_masks(nose_right, nose_left, allow_mirror=False)
    check("no-mirror keeps it low", stats["iou"] < 0.8, stats)


def test_concept_extraction(tmp):
    path = os.path.join(tmp, "concept_side.png")

    def ship(d, fg):
        d.polygon([(60, 200), (520, 170), (600, 200), (520, 230)], fill=fg)
        d.rectangle([220, 194, 260, 206], fill=(240, 240, 240))    # a light window inside: a hole to fill
        d.point([(10, 10), (590, 20)], fill=fg)                      # specks
    concept(path, (640, 400), ship)
    mask = sc.extract_reference_mask(path)
    expected = mask_from_shape((640, 400), lambda d: d.polygon([(60, 200), (520, 170), (600, 200), (520, 230)], fill=255))
    stats, _, _ = sc.compare_masks(mask, expected, allow_mirror=False)
    check("concept silhouette cut from neutral background", stats["iou"] > 0.95, stats)
    check("specks removed", not mask[10, 10] and not mask[20, 590])


def test_compare_cli(tmp):
    for view in sc.VIEWS:
        Image.fromarray((mask_from_shape((256, 256), lambda d: d.ellipse([40, 90, 216, 166], fill=255)) * 255)
                        .astype("uint8")).save(os.path.join(tmp, "model_%s.png" % view))
        concept(os.path.join(tmp, "ref_%s.png" % view), (500, 300),
                lambda d, fg: d.ellipse([60, 68, 440, 232], fill=fg))  # same 2.3:1 as the model
    argv = ["compare", "--model", os.path.join(tmp, "model"), "--out", os.path.join(tmp, "out")]
    for view in sc.VIEWS:
        argv += ["--ref", "%s=%s" % (view, os.path.join(tmp, "ref_%s.png" % view))]
    report = sc.main_cli(argv)
    saved = json.load(open(os.path.join(tmp, "out", "silhouette.json"), encoding="utf-8"))
    check("json written with all views", set(saved["views"]) == set(sc.VIEWS), list(saved["views"]))
    check("ellipses of the same proportion match", report["mean_iou"] > 0.9, report["mean_iou"])
    check("diff images exist", all(os.path.exists(v["diff"]) for v in saved["views"].values())
          and os.path.exists(saved["diff_sheet"]))


def test_blender_render(tmp):
    if not os.path.exists(sc.BLENDER):
        print("SKIP blender render (no Blender 5.2)")
        return
    # Default cube (2 m): every view is a square.
    for view in sc.VIEWS:
        concept(os.path.join(tmp, "sq_%s.png" % view), (300, 300), lambda d, fg: d.rectangle([50, 50, 250, 250], fill=fg))
    argv = ["run", "--objects", "Cube", "--out", os.path.join(tmp, "cube")]
    for view in sc.VIEWS:
        argv += ["--ref", "%s=%s" % (view, os.path.join(tmp, "sq_%s.png" % view))]
    report = sc.main_cli(argv)
    check("blender cube renders match squares", report["mean_iou"] > 0.97, report["mean_iou"])
    info = json.load(open(os.path.join(tmp, "cube", "model_views.json"), encoding="utf-8"))
    check("bbox of the default cube", abs(info["bbox_max"][0] - 1) < 1e-4 and abs(info["bbox_min"][2] + 1) < 1e-4, info)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        test_identical_and_shifted()
        test_different_shape_scores_lower()
        test_mirror()
        test_concept_extraction(tmp)
        test_compare_cli(tmp)
        test_blender_render(tmp)
    print("FAILED: %s" % FAILED if FAILED else "ALL PASSED")
    sys.exit(1 if FAILED else 0)
