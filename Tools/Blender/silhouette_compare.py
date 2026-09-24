"""Measurable silhouette match between a model and its reference views (front, side, top).

The number to optimise while modelling: IoU of the model's silhouette against the reference's, per
view, after both are normalised to their bounding box. Also the proportions (bbox aspect) and a diff
image: grey = both, red = the model has extra, cyan = the model is missing.

Three stages, in one file so the conventions stay together:

1. render (inside Blender, headless): orthographic Workbench masks, white model on black.
       MSYS_NO_PATHCONV=1 blender -b Ship.blend --python Tools/Blender/silhouette_compare.py -- \\
           render --objects SM_Ship_<Ship> --out Saved/Silhouette/<ship> --prefix model \\
           [--crop-box xmin,ymin,zmin,xmax,ymax,zmax] [--res 1024]
   Without a .blend (--factory-startup) the default Cube renders, which the test uses.
2. compare (plain Python, needs numpy + Pillow):
       python Tools/Blender/silhouette_compare.py compare --model Saved/Silhouette/<ship>/model \\
           --ref front=concept_front.png --ref side=concept_side.png --ref top=concept_top.png \\
           --out Saved/Silhouette/<ship>
   A reference can be a concept image (the silhouette is cut from its neutral background, or taken
   from alpha) or another render prefix: --ref-model Saved/Silhouette/meshy/model. Two renders are
   compared in world space (--align world, the default): a volume reference in the same
   coordinates. Concept images are always normalised to their bounding box.
3. run: both in one go (calls Blender, then compares); prints the JSON.
       python Tools/Blender/silhouette_compare.py run --blend Ship.blend --objects A,B --ref ... --out DIR
4. views: are concept views of one ship consistent with each other (no model needed, the check
   before any 3D)? Each view shows two of length/beam/height, so side+top predict the front
   proportion; also left-right symmetry of front and top, and optionally the spec's dimensions.
       python Tools/Blender/silhouette_compare.py views --ref front=f.png --ref side=s.png            --ref top=t.png [--dims 14,11.4,6.2] --out DIR
5. guide: silhouette guide images for an image model (dark silhouette on light grey, 16:9), from
   render masks (--model DIR/model) or any white-on-black / concept image (--mask view=img). Passed
   to the generator as a second reference with "match this silhouette exactly".
       python Tools/Blender/silhouette_compare.py guide --model Saved/Silhouette/x/model --out DIR

Views (Blender: nose +X, up +Z, port +Y), always drawn the same way so references must match:
  front = looking at the nose (from +X), port side on the right;
  side  = from starboard (-Y), nose to the right;
  top   = from above (+Z), nose to the right, port up.
A reference that faces the other way is matched mirrored automatically (reported as "mirrored").

Output: <out>/silhouette.json with per-view iou, aspect_model, aspect_ref, extra_pct, missing_pct,
mirrored and the diff image path, plus mean_iou; <out>/diff_<view>.png and <out>/diff_sheet.png.
"""
import argparse
import json
import os
import subprocess
import sys

VIEWS = ("front", "side", "top")
NORM = 512          # normalised canvas: the bbox's longer side becomes NORM px
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"


# --------------------------------------------------------------------------------------------
# 1. Render (Blender)
# --------------------------------------------------------------------------------------------

def _crop_copy(bpy, bmesh, ob, box, cylinder=None):
    """A temporary copy of ob's evaluated mesh without the faces whose centre lies outside box
    (and, with cylinder = (yc, zc, r), farther than r from an X-parallel axis: a nacelle without
    the pylon that holds it)."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), depsgraph=dg)
    me.transform(ob.matrix_world)
    bm = bmesh.new()
    bm.from_mesh(me)
    lo, hi = box[:3], box[3:]
    def inside(c):
        if not all(lo[i] <= c[i] <= hi[i] for i in range(3)):
            return False
        return cylinder is None or (c[1] - cylinder[0]) ** 2 + (c[2] - cylinder[1]) ** 2 <= cylinder[2] ** 2
    outside = [f for f in bm.faces if not inside(f.calc_center_median())]
    bmesh.ops.delete(bm, geom=outside, context="FACES")
    bm.to_mesh(me)
    bm.free()
    copy = bpy.data.objects.new(ob.name + "_SILCROP", me)
    bpy.context.scene.collection.objects.link(copy)
    return copy


def render_masks(argv):
    import bmesh
    import bpy
    from mathutils import Euler, Vector

    ap = argparse.ArgumentParser(prog="silhouette_compare.py render")
    ap.add_argument("--collection", default="", help="all meshes in this collection (recursive)")
    ap.add_argument("--objects", default="", help="comma list; empty = all visible meshes")
    ap.add_argument("--out", required=True)
    ap.add_argument("--prefix", default="model")
    ap.add_argument("--res", type=int, default=1024)
    ap.add_argument("--crop-box", default="", help="xmin,ymin,zmin,xmax,ymax,zmax in metres")
    ap.add_argument("--crop-cylinder", default="", help="yc,zc,r: also drop faces farther than r from an X axis")
    a = ap.parse_args(argv)
    a.out = os.path.abspath(a.out)   # Blender resolves a relative render path against the .blend
    os.makedirs(a.out, exist_ok=True)

    scene = bpy.context.scene
    names = [n for n in a.objects.split(",") if n]
    if a.collection:
        names += [o.name for o in bpy.data.collections[a.collection].all_objects if o.type == "MESH"]
    meshes = [o for o in scene.objects if o.type == "MESH" and
              ((o.name in names) if names else (not o.hide_render and not o.name.startswith("UCX_")))]
    missing = set(names) - {o.name for o in meshes}
    if missing:
        raise SystemExit("silhouette_compare: objects not found: %s" % ", ".join(sorted(missing)))
    if a.crop_box:
        box = [float(v) for v in a.crop_box.split(",")]
        cyl = [float(v) for v in a.crop_cylinder.split(",")] if a.crop_cylinder else None
        meshes = [_crop_copy(bpy, bmesh, o, box, cyl) for o in meshes]
    keep = set(meshes)
    # Only what the view layer shows: excluded library collections (the HS_Kit greebles) must keep
    # rendering through their instances.
    for o in bpy.context.view_layer.objects:
        o.hide_render = o not in keep

    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    centre, size = (lo + hi) / 2, hi - lo

    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    shading.light = "FLAT"
    shading.color_type = "SINGLE"
    shading.single_color = (1, 1, 1)
    shading.background_type = "VIEWPORT"
    shading.background_color = (0, 0, 0)
    shading.show_cavity = shading.show_shadows = shading.show_object_outline = False
    shading.show_specular_highlight = False
    scene.display.render_aa = "OFF"          # hard mask edges, no threshold guessing
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x = scene.render.resolution_y = a.res
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "BW"

    cam_data = bpy.data.cameras.new("SIL_CAM")
    cam_data.type = "ORTHO"
    cam = bpy.data.objects.new("SIL_CAM", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    far = size.length * 2 + 1
    cam_data.clip_start, cam_data.clip_end = 0.01, far * 2
    # (location offset, rotation, the two extents seen by this view)
    rigs = {
        "front": (Vector((far, 0, 0)), Euler((1.5708, 0, 1.5708)), (size.y, size.z)),
        "side": (Vector((0, -far, 0)), Euler((1.5708, 0, 0)), (size.x, size.z)),
        "top": (Vector((0, 0, far)), Euler((0, 0, 0)), (size.x, size.y)),
    }
    info = {"bbox_min": list(lo), "bbox_max": list(hi), "views": {}, "frames": {}}
    for view, (offset, rot, extents) in rigs.items():
        cam.location = centre + offset
        cam.rotation_euler = rot
        cam_data.ortho_scale = max(extents) * 1.08
        path = os.path.join(a.out, "%s_%s.png" % (a.prefix, view))
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        info["views"][view] = path
        # World square the image covers: [u centre, v centre, side] in metres.
        u, v = {"front": (centre.y, centre.z), "side": (centre.x, centre.z), "top": (centre.x, centre.y)}[view]
        info["frames"][view] = [u, v, cam_data.ortho_scale]
    with open(os.path.join(a.out, "%s_views.json" % a.prefix), "w", encoding="utf-8") as fh:
        json.dump(info, fh, indent=1)
    print("SILHOUETTE_RENDER", json.dumps(info))


# --------------------------------------------------------------------------------------------
# 2. Compare (plain Python)
# --------------------------------------------------------------------------------------------

def load_render_mask(path):
    import numpy as np
    from PIL import Image
    return np.asarray(Image.open(path).convert("L")) > 127


MAX_REF_PX = 1400   # concept images are downscaled to this (AI output is 2-4K; only proportions matter)


def extract_reference_mask(path, threshold=30):
    """Silhouette from a concept image: alpha if it has one, else everything that differs from the
    neutral background (median of the border pixels), holes filled, specks and detached blobs
    smaller than 2 % of the largest removed (bleed from a neighbouring cell of a turnaround sheet)."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    img = Image.open(path)
    if max(img.size) > MAX_REF_PX:
        k = MAX_REF_PX / max(img.size)
        img = img.resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)
    if img.mode in ("RGBA", "LA") or "transparency" in img.info:
        alpha = np.asarray(img.convert("RGBA"))[..., 3]
        if alpha.min() < 128 <= alpha.max():
            mask = alpha > 127
            return _fill_holes(mask)
    rgb = np.asarray(img.convert("RGB")).astype(np.int16)
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    bg = np.median(border, axis=0)
    mask = np.abs(rgb - bg).max(axis=2) > threshold
    # Specks (noise, grain, stray text pixels) die in a 3 px opening; the silhouette's thin parts
    # (nose tips, antennas) are then grown back inside the original mask (reconstruction), so only
    # blobs that vanished completely are removed.
    m = Image.fromarray((mask * 255).astype("uint8"))
    seed = np.asarray(m.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))) > 127
    for _ in range(64):
        grown = np.asarray(Image.fromarray((seed * 255).astype("uint8")).filter(ImageFilter.MaxFilter(3))) > 127
        grown &= mask
        if (grown == seed).all():
            break
        seed = grown
    return _drop_small_blobs(_fill_holes(seed))


def _drop_small_blobs(mask, keep_frac=0.02):
    try:
        from scipy import ndimage
    except ImportError:
        return mask
    import numpy as np
    labels, n = ndimage.label(mask)
    if n <= 1:
        return mask
    sizes = np.bincount(labels.ravel())[1:]
    keep = np.nonzero(sizes >= keep_frac * sizes.max())[0] + 1
    return np.isin(labels, keep)


def _fill_holes(mask):
    """Everything not reachable from the image border through background is object."""
    import numpy as np
    from PIL import Image, ImageDraw
    h, w = mask.shape
    pad = Image.new("L", (w + 2, h + 2), 0)
    pad.paste(Image.fromarray((mask * 255).astype("uint8")), (1, 1))
    ImageDraw.floodfill(pad, (0, 0), 128)
    arr = np.asarray(pad)[1:-1, 1:-1]
    return arr != 128


def normalise(mask, size=NORM):
    """Crop to the bbox, scale its longer side to size (aspect kept), centre on a size² canvas."""
    import numpy as np
    from PIL import Image
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        raise ValueError("empty silhouette")
    crop = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = crop.shape
    k = size / max(w, h)
    nw, nh = max(1, round(w * k)), max(1, round(h * k))
    img = Image.fromarray((crop * 255).astype("uint8")).resize((nw, nh), Image.BILINEAR)
    canvas = Image.new("L", (size, size), 0)
    canvas.paste(img, ((size - nw) // 2, (size - nh) // 2))
    return np.asarray(canvas) > 127, w / h


def compare_masks(model, ref, allow_mirror=True):
    import numpy as np
    m, aspect_m = normalise(model)
    r, aspect_r = normalise(ref)
    best = None
    for mirrored in ((False, True) if allow_mirror else (False,)):
        rr = r[:, ::-1] if mirrored else r
        union = np.logical_or(m, rr).sum()
        iou = float(np.logical_and(m, rr).sum() / union) if union else 0.0
        if best is None or iou > best[0]:
            best = (iou, mirrored, rr)
    iou, mirrored, rr = best
    area = max(1, int(rr.sum()))
    return {
        "iou": round(iou, 4),
        "mirrored": mirrored,
        "aspect_model": round(aspect_m, 3),
        "aspect_ref": round(aspect_r, 3),
        "extra_pct": round(100.0 * float( np.logical_and(m, ~rr).sum()) / area, 2),
        "missing_pct": round(100.0 * float( np.logical_and(~m, rr).sum()) / area, 2),
    }, m, rr


def world_masks(model_mask, model_frame, ref_mask, ref_frame, size=NORM):
    """Both renders resampled onto one world-space canvas, without normalisation: when modelling
    against a volume reference in the same coordinates, a stray bit in one mask must not rescale
    the other."""
    import numpy as np
    from PIL import Image
    rects = [(f[0] - f[2] / 2, f[1] - f[2] / 2, f[0] + f[2] / 2, f[1] + f[2] / 2) for f in (model_frame, ref_frame)]
    u0, v0 = min(r[0] for r in rects), min(r[1] for r in rects)
    u1, v1 = max(r[2] for r in rects), max(r[3] for r in rects)
    k = size / max(u1 - u0, v1 - v0)
    out = []
    for mask, (ru0, rv0, ru1, rv1) in zip((model_mask, ref_mask), rects):
        side = max(1, round((ru1 - ru0) * k))
        img = Image.fromarray((mask * 255).astype("uint8")).resize((side, side), Image.NEAREST)
        canvas = Image.new("L", (round((u1 - u0) * k), round((v1 - v0) * k)), 0)
        canvas.paste(img, (round((ru0 - u0) * k), round((v1 - rv1) * k)))
        out.append(np.asarray(canvas) > 127)
    return out


def world_stats(m, r):
    import numpy as np
    union = np.logical_or(m, r).sum()
    area = max(1, int(r.sum()))
    ys, xs = np.nonzero(m)
    yr, xr = np.nonzero(r)
    return {
        "iou": round(float(np.logical_and(m, r).sum() / union) if union else 0.0, 4),
        "mirrored": False,
        "aspect_model": round(float(np.ptp(xs) + 1) / float(np.ptp(ys) + 1), 3),
        "aspect_ref": round(float(np.ptp(xr) + 1) / float(np.ptp(yr) + 1), 3),
        "extra_pct": round(100.0 * float(np.logical_and(m, ~r).sum()) / area, 2),
        "missing_pct": round(100.0 * float(np.logical_and(~m, r).sum()) / area, 2),
    }


def diff_image(m, r):
    import numpy as np
    from PIL import Image
    out = np.zeros(m.shape + (3,), dtype=np.uint8)
    out[:] = (18, 22, 30)
    out[m & r] = (150, 150, 150)
    out[m & ~r] = (235, 70, 60)       # the model has extra
    out[~m & r] = (60, 200, 235)      # the model is missing
    return Image.fromarray(out)


def _frames(prefix):
    path = "%s_views.json" % prefix
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh).get("frames")


def compare(args):
    from PIL import Image, ImageDraw
    os.makedirs(args.out, exist_ok=True)
    refs = dict(r.split("=", 1) for r in (args.ref or []))
    report = {"model": args.model, "views": {}}
    tiles = []
    for view in VIEWS:
        model_path = "%s_%s.png" % (args.model, view)
        if args.ref_model:
            ref_path = "%s_%s.png" % (args.ref_model, view)
            ref = load_render_mask(ref_path) if os.path.exists(ref_path) else None
        else:
            ref_path = refs.get(view)
            ref = extract_reference_mask(ref_path, args.threshold) if ref_path else None
        if ref is None or not os.path.exists(model_path):
            continue
        frames = _frames(args.model), (_frames(args.ref_model) if args.ref_model else None)
        if args.align == "world" and frames[0] and frames[1]:
            m, r = world_masks(load_render_mask(model_path), frames[0][view], ref, frames[1][view])
            stats = world_stats(m, r)
            stats["align"] = "world"
        else:
            stats, m, r = compare_masks(load_render_mask(model_path), ref, not args.no_mirror)
            stats["align"] = "bbox"
        diff_path = os.path.join(args.out, "diff_%s.png" % view)
        img = diff_image(m, r)
        img.save(diff_path)
        stats.update(reference=ref_path, diff=diff_path)
        report["views"][view] = stats
        tiles.append((view, stats, img))
    if not tiles:
        raise SystemExit("silhouette_compare: no view had both a model render and a reference")
    report["mean_iou"] = round(sum(v["iou"] for v in report["views"].values()) / len(tiles), 4)
    sheet = Image.new("RGB", (NORM * len(tiles), NORM + 40), (18, 22, 30))
    d = ImageDraw.Draw(sheet)
    for i, (view, stats, img) in enumerate(tiles):
        sheet.paste(img, (i * NORM, 40))
        d.text((i * NORM + 10, 10), "%s  IoU %.3f  extra %.1f %%  missing %.1f %%%s" % (
            view, stats["iou"], stats["extra_pct"], stats["missing_pct"],
            "  (mirrored)" if stats["mirrored"] else ""), fill=(230, 230, 230))
    sheet_path = os.path.join(args.out, "diff_sheet.png")
    sheet.save(sheet_path)
    report["diff_sheet"] = sheet_path
    with open(os.path.join(args.out, "silhouette.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    print(json.dumps(report, indent=1))
    return report


def _bbox_px(mask):
    import numpy as np
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        raise ValueError("empty silhouette")
    return float(xs.max() - xs.min() + 1), float(ys.max() - ys.min() + 1)


def _symmetry(mask, axis):
    """IoU of the bbox-normalised silhouette with its own mirror (axis 1 = left-right)."""
    import numpy as np
    m, _ = normalise(mask)
    f = m[:, ::-1] if axis == 1 else m[::-1, :]
    union = np.logical_or(m, f).sum()
    return round(float(np.logical_and(m, f).sum() / union), 4) if union else 0.0


def view_consistency(masks, dims=None):
    """masks: {view: bool array} for front/side/top drawn by the VIEWS convention.
    side = L x H, top = L x W, front = W x H (px, each view its own unknown scale)."""
    L_s, H_s = _bbox_px(masks["side"])
    L_t, W_t = _bbox_px(masks["top"])
    W_f, H_f = _bbox_px(masks["front"])
    # Common scale: length from side, beam from top (scaled to the side's length), height from side.
    L = 1.0
    W = W_t / L_t
    H = H_s / L_s
    predicted_front = W / H
    measured_front = W_f / H_f
    rep = {
        "proportions_L_W_H": [1.0, round(W, 4), round(H, 4)],
        "front_aspect_measured": round(measured_front, 4),
        "front_aspect_from_side_top": round(predicted_front, 4),
        "closure_error_pct": round(100.0 * abs(measured_front / predicted_front - 1.0), 2),
        "symmetry_front": _symmetry(masks["front"], 1),
        "symmetry_top": _symmetry(masks["top"], 0),
    }
    if dims:
        dl, dw, dh = dims
        rep["spec_L_W_H_m"] = list(dims)
        rep["concept_W_H_m_at_spec_length"] = [round(W * dl, 2), round(H * dl, 2)]
        rep["beam_error_pct"] = round(100.0 * abs(W * dl / dw - 1.0), 2)
        rep["height_error_pct"] = round(100.0 * abs(H * dl / dh - 1.0), 2)
    return rep


def views(args):
    from PIL import Image, ImageDraw
    os.makedirs(args.out, exist_ok=True)
    refs = dict(r.split("=", 1) for r in (args.ref or []))
    missing = [v for v in VIEWS if v not in refs]
    if missing:
        raise SystemExit("silhouette_compare views: need --ref for %s" % ", ".join(missing))
    masks = {v: extract_reference_mask(refs[v], args.threshold) for v in VIEWS}
    dims = [float(x) for x in args.dims.split(",")] if args.dims else None
    rep = view_consistency(masks, dims)
    rep["references"] = refs
    sheet = Image.new("RGB", (NORM * 3, NORM + 40), (18, 22, 30))
    d = ImageDraw.Draw(sheet)
    for i, v in enumerate(VIEWS):
        m, _ = normalise(masks[v])
        sheet.paste(Image.fromarray((m * 255).astype("uint8")).convert("RGB"), (i * NORM, 40))
        d.text((i * NORM + 10, 10), v, fill=(230, 230, 230))
    d.text((10, 26), "closure %.1f %%  sym front %.3f  sym top %.3f" % (
        rep["closure_error_pct"], rep["symmetry_front"], rep["symmetry_top"]), fill=(230, 200, 120))
    rep["mask_sheet"] = os.path.join(args.out, "views_masks.png")
    sheet.save(rep["mask_sheet"])
    with open(os.path.join(args.out, "views.json"), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1)
    print(json.dumps(rep, indent=1))
    return rep


def make_guide(mask, size=(1920, 1080), fill=0.8):
    import numpy as np
    from PIL import Image
    ys, xs = np.nonzero(mask)
    c = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = c.shape
    k = min(size[0] * fill / w, size[1] * fill * 0.875 / h)
    sil = Image.fromarray((c * 255).astype("uint8")).resize((max(1, int(w * k)), max(1, int(h * k))), Image.LANCZOS)
    out = Image.new("RGB", size, (208, 208, 208))
    out.paste(Image.new("RGB", sil.size, (40, 44, 52)), ((size[0] - sil.width) // 2, (size[1] - sil.height) // 2), sil)
    return out


def guides(args):
    os.makedirs(args.out, exist_ok=True)
    srcs = dict(m.split("=", 1) for m in (args.mask or []))
    written = {}
    for view in VIEWS:
        if args.model and os.path.exists("%s_%s.png" % (args.model, view)):
            mask = load_render_mask("%s_%s.png" % (args.model, view))
        elif view in srcs:
            mask = extract_reference_mask(srcs[view], args.threshold)
        else:
            continue
        written[view] = os.path.join(args.out, "guide_%s.png" % view)
        make_guide(mask).save(written[view])
    print(json.dumps(written, indent=1))
    return written


def run(args, rest):
    cmd = [BLENDER, "-b"] + ([args.blend] if args.blend else ["--factory-startup"]) + [
        "--python", os.path.abspath(__file__), "--", "render", "--out", args.out, "--prefix", "model"]
    if args.objects:
        cmd += ["--objects", args.objects]
    if args.collection:
        cmd += ["--collection", args.collection]
    if args.crop_box:
        cmd += ["--crop-box=" + args.crop_box]
    if args.crop_cylinder:
        cmd += ["--crop-cylinder=" + args.crop_cylinder]
    proc = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if "SILHOUETTE_RENDER" not in proc.stdout:
        raise SystemExit("Blender render failed:\n" + proc.stdout[-3000:] + proc.stderr[-2000:])
    args.model = os.path.join(args.out, "model")
    return compare(args)


def main_cli(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("compare", "run"):
        p = sub.add_parser(name)
        p.add_argument("--out", required=True)
        p.add_argument("--ref", action="append", help="view=image (front, side, top)")
        p.add_argument("--ref-model", help="another render prefix to compare against")
        p.add_argument("--threshold", type=int, default=30, help="background distance for concept images")
        p.add_argument("--no-mirror", action="store_true")
        p.add_argument("--align", choices=("world", "bbox"), default="world",
                       help="world: two renders in the same coordinates stay put (used when both have "
                            "_views.json); bbox: both normalised to their bounding box (concept images)")
        if name == "compare":
            p.add_argument("--model", required=True, help="render prefix, e.g. DIR/model")
        else:
            p.add_argument("--blend", default="")
            p.add_argument("--objects", default="")
            p.add_argument("--collection", default="")
            p.add_argument("--crop-box", default="")
            p.add_argument("--crop-cylinder", default="")
    p = sub.add_parser("views")
    p.add_argument("--out", required=True)
    p.add_argument("--ref", action="append", help="view=image (front, side, top), all three")
    p.add_argument("--threshold", type=int, default=30)
    p.add_argument("--dims", default="", help="spec length,beam,height in metres")
    p = sub.add_parser("guide")
    p.add_argument("--out", required=True)
    p.add_argument("--model", default="", help="render prefix (white-on-black masks)")
    p.add_argument("--mask", action="append", help="view=image, silhouette cut like a concept")
    p.add_argument("--threshold", type=int, default=30)
    args = ap.parse_args(argv)
    if args.cmd == "views":
        return views(args)
    if args.cmd == "guide":
        return guides(args)
    return compare(args) if args.cmd == "compare" else run(args, argv)


if __name__ == "__main__":
    try:
        import bpy  # noqa: F401
        IN_BLENDER = True
    except ImportError:
        IN_BLENDER = False
    if IN_BLENDER:
        argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
        if not argv or argv[0] != "render":
            raise SystemExit("inside Blender only 'render' is available")
        render_masks(argv[1:])
    else:
        main_cli(sys.argv[1:])
