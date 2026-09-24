"""Clean paint for an AI ship: replaces the blotchy AI base colour with flat paint zones.

    blender -b ArtSource/Ships/<Ship>/<Ship>_AI.blend --python Tools/Blender/repaint_ship.py -- ArtSource/Ships/<Ship>/<Ship>_ai_build.json

Why: an AI (Meshy / Higgsfield) texture is a mosaic of thousands of tiny UV islands at 2K; on a 20 m ship
that is ~3 cm per pixel, the colours bleed into dark smudges along the island edges, and lighting is
baked in as purple / dark patches. Re-baking it to 4K keeps all of that (Wayfarer, 24. 9. 2026: "looks
broken, dirty, low quality").

What it does, driven by the recipe's "repaint" block:
  1. every face of the built meshes gets the colour of the baked base colour under it (4 samples);
  2. it is classified into paint zones (light paint, dark paint, accent, glass, engine metal) by lightness,
     saturation and hue, with region boxes that force a zone (canopy -> glass, nozzles -> engine);
  3. the zones are smoothed over the mesh (majority of the edge neighbours, a few passes), so single
     faces of the wrong colour and ragged borders disappear; the accent keeps thin stripes (weight);
  4. each zone gets ONE clean colour (the zone's median in the AI texture, or the recipe's colour),
     roughness and metallic, rasterised onto the existing UV atlas: new base colour and ORM textures
     (the ORM keeps R = 1, the emissive mask of the screens). Normal and AO maps stay as they are:
     the panel lines and recesses are geometry and still show.
Reads the recipe's rebake base_color (the AI colours re-baked by build_ai_ship.py, e.g. T_Ship_<Ship>_BC_AI.png),
writes repaint.out_base_color / out_orm (the maps the game uses) and prints REPAINT {...}. Run it after every
build (like bake_ship_ao.py).
"""
import json
import os
import sys

import bpy
import numpy as np

def _borrow(module):
    """Blender ships no Pillow or SciPy, but its Python is the system's version (3.13): borrow the system's
    site-packages for them."""
    try:
        __import__(module)
    except ImportError:
        import subprocess
        site = subprocess.run(["python", "-c", "import %s, os; print(os.path.dirname(os.path.dirname(%s.__file__)))" % (module, module)],
                              capture_output=True, text=True).stdout.strip()
        if site and site not in sys.path:
            sys.path.append(site)


_borrow("PIL")
_borrow("scipy")
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ZONES = ("paint", "dark", "accent", "glass", "engine")


def path(p):
    return p if os.path.isabs(p) else os.path.join(REPO, p)


def in_box(pts, box):
    ok = np.ones(len(pts), bool)
    for i, k in enumerate("xyz"):
        if k in box:
            ok &= (pts[:, i] >= box[k][0]) & (pts[:, i] <= box[k][1])
    return ok


def face_data(ob):
    me = ob.data
    me.calc_loop_triangles()
    n = len(me.polygons)
    uv = np.empty(len(me.loops) * 2, np.float32)
    me.uv_layers.active.data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)
    start = np.empty(n, np.int32); me.polygons.foreach_get("loop_start", start)
    total = np.empty(n, np.int32); me.polygons.foreach_get("loop_total", total)
    centre = np.empty(n * 3, np.float32); me.polygons.foreach_get("center", centre)
    normal = np.empty(n * 3, np.float32); me.polygons.foreach_get("normal", normal)
    mat = np.empty(n, np.int32); me.polygons.foreach_get("material_index", mat)
    loop_edges = np.empty(len(me.loops), np.int32); me.loops.foreach_get("edge_index", loop_edges)
    return dict(uv=uv, start=start, total=total, centre=centre.reshape(-1, 3), normal=normal.reshape(-1, 3),
                mat=mat, loop_edges=loop_edges)


def neighbours(fd):
    """Pairs of edge-adjacent faces (i, j), both directions."""
    face_of_loop = np.repeat(np.arange(len(fd["start"])), fd["total"])
    edges = fd["loop_edges"]
    order = np.argsort(edges, kind="stable")
    e, f = edges[order], face_of_loop[order]
    same = e[1:] == e[:-1]
    a, b = f[:-1][same], f[1:][same]
    return np.concatenate([a, b]), np.concatenate([b, a])


def sample_colours(fd, tex):
    h, w, _ = tex.shape
    cols = np.zeros((len(fd["start"]), 3), np.float32)
    cnt = np.zeros(len(fd["start"]), np.float32)
    for k in range(3):   # the first three corners (all faces are triangles after the export triangulation; quads fine)
        idx = fd["start"] + np.minimum(k, fd["total"] - 1)
        uv = fd["uv"][idx]
        x = np.clip((uv[:, 0] % 1.0) * w, 0, w - 1).astype(int)
        y = np.clip((1.0 - uv[:, 1] % 1.0) * h, 0, h - 1).astype(int)
        cols += tex[y, x]
        cnt += 1
    # the centroid too, weighted double: corners sit on island edges where the colours bleed
    cu = np.zeros((len(fd["start"]), 2), np.float32)
    for k in range(3):
        cu += fd["uv"][fd["start"] + np.minimum(k, fd["total"] - 1)]
    cu /= 3.0
    x = np.clip((cu[:, 0] % 1.0) * w, 0, w - 1).astype(int)
    y = np.clip((1.0 - cu[:, 1] % 1.0) * h, 0, h - 1).astype(int)
    cols += 2 * tex[y, x]
    return cols / (cnt + 2)[:, None]


def classify(cols, fd, cfg):
    r, g, b = cols[:, 0], cols[:, 1], cols[:, 2]
    mx, mn = cols.max(1), cols.min(1)
    light = (mx + mn) / 2
    sat = np.where(mx > 1e-4, (mx - mn) / np.maximum(mx, 1e-4), 0)
    zone = np.where(light >= cfg.get("light_min", 0.5), 0, 1)                      # paint / dark
    orange = (r > 0.45) & (r - b > 0.25) & (g > b) & (r >= g) & (sat > 0.45)
    zone[orange] = 2                                                               # accent
    zone[(sat > 0.35) & (b > r)] = 1                                               # baked blue/purple light -> dark
    for box in cfg.get("glass_boxes", []):
        sel = in_box(fd["centre"], box) & (light < cfg.get("glass_light_max", 0.35))
        zone[sel] = 3
    for box in cfg.get("engine_boxes", []):
        zone[in_box(fd["centre"], box) & (zone != 2)] = 4
    return zone


def smooth(zone, pairs, passes, accent_weight, fixed):
    a, b = pairs
    n = len(zone)
    for _ in range(passes):
        votes = np.zeros((n, len(ZONES)), np.float32)
        np.add.at(votes, (a, zone[b]), 1.0)
        votes[:, 2] *= accent_weight
        votes[np.arange(n), zone] += 1.0            # a face counts itself once
        new = votes.argmax(1)
        new[fixed] = zone[fixed]
        zone = new
    return zone


def face_areas(ob):
    a = np.empty(len(ob.data.polygons), np.float32)
    ob.data.polygons.foreach_get("area", a)
    return a


def drop_specks(zone, pairs, areas, min_area, keep=(2,)):
    """Connected patches of one zone smaller than min_area m2 take the zone most of their border faces have.
    The accent (thin stripes) is kept. Needs scipy (borrowed from the system Python like Pillow)."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    a, b = pairs
    same = zone[a] == zone[b]
    n = len(zone)
    graph = coo_matrix((np.ones(same.sum()), (a[same], b[same])), shape=(n, n))
    count, comp = connected_components(graph, directed=False)
    comp_area = np.bincount(comp, weights=areas, minlength=count)
    small = (comp_area[comp] < min_area) & ~np.isin(zone, keep)
    # border votes per component: the zones of the neighbours across its edge
    border = ~same & small[a]
    votes = np.zeros((count, len(ZONES)), np.float32)
    np.add.at(votes, (comp[a[border]], zone[b[border]]), 1.0)
    best = votes.argmax(1)
    has = votes.sum(1) > 0
    change = small & has[comp]
    zone = zone.copy()
    zone[change] = best[comp[change]]
    return zone, int(change.sum())


def texel_pass(clean, zone_img, ai, cfg, looks, excluded=None):
    """Per texel, on top of the flat zones:
    - the accent stripes are cut from the AI colours themselves (orange texels, median-filtered and
      thresholded, only where the face zone is paint or accent): crisp shapes that follow the AI's painted
      stripes instead of whole triangles (which gave ragged "flames", author 24. 9. 2026);
    - a little of the AI's lightness, normalised per zone (texel / zone median), so panels and seams keep
      their tone without the AI's dirty tint: detail_strength 0 = flat paint, 1 = the AI's full variation."""
    lum = ai @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    out = clean.copy()
    k = cfg.get("detail_strength", 0.3)
    for i, z in enumerate(ZONES):
        sel = zone_img == i
        if not sel.any() or z in ("glass",):
            continue
        med = max(float(np.median(lum[sel])), 1e-3)
        ratio = np.clip(lum[sel] / med, 0.55, 1.35)
        out[sel] = clean[sel] * (1.0 + k * (ratio - 1.0))[:, None]
    r, g, b = ai[..., 0], ai[..., 1], ai[..., 2]
    mx, mn = ai.max(-1), ai.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-4)
    orange = ((r > 0.45) & (r - b > 0.22) & (g > b) & (r >= g) & (sat > 0.4)).astype(np.uint8) * 255
    orange = np.asarray(Image.fromarray(orange).filter(ImageFilter.MedianFilter(5))) > 127
    allowed = (zone_img == ZONES.index("paint")) | (zone_img == ZONES.index("accent"))
    if excluded is not None:
        allowed &= ~excluded
    stripe = orange & allowed
    acc = np.array(looks["accent"]["colour"], np.float32)
    out[stripe] = acc
    # accent faces the texel test did not confirm fall back to the paint
    lost = (zone_img == ZONES.index("accent")) & ~stripe
    out[lost] = np.array(looks["paint"]["colour"], np.float32)
    return out


def rasterise(fd, values, size, empty):
    """values: (faces, 3) floats 0..1 -> RGB image on the UV atlas, dilated 8 px into the gutters."""
    img = Image.new("RGB", (size, size), empty)
    mask = Image.new("L", (size, size), 0)
    d, dm = ImageDraw.Draw(img), ImageDraw.Draw(mask)
    uv = fd["uv"]
    for i in range(len(fd["start"])):
        s, t = fd["start"][i], fd["total"][i]
        pts = [(float(uv[s + k, 0] * size), float((1.0 - uv[s + k, 1]) * size)) for k in range(t)]
        c = tuple(int(round(v * 255)) for v in values[i])
        d.polygon(pts, fill=c, outline=c)
        dm.polygon(pts, fill=255, outline=255)
    arr = np.asarray(img).copy()
    m = np.asarray(mask) > 0
    for _ in range(8):   # dilate the painted texels into the empty gutter so mips and bilinear filtering do not bleed
        grown = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 0
        new = grown & ~m
        if not new.any():
            break
        src = Image.fromarray(arr).filter(ImageFilter.MaxFilter(3))
        arr[new] = np.asarray(src)[new]
        m = grown
    return Image.fromarray(arr)


def main(argv):
    recipe = json.load(open(path(argv[0]), encoding="utf-8"))
    cfg = recipe["repaint"]
    ship = recipe["ship"]
    bake = recipe["rebake"]
    tex = np.asarray(Image.open(path(bake["base_color"])).convert("RGB")).astype(np.float32) / 255.0
    obs = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("SM_Ship_%s" % ship)]
    datas, zones, colours = [], [], []
    for ob in obs:
        fd = face_data(ob)
        cols = sample_colours(fd, tex)
        zone = classify(cols, fd, cfg)
        emissive = np.array([s.name.endswith("_Emissive") if s else False for s in ob.data.materials])
        fixed = emissive[fd["mat"]] if len(emissive) else np.zeros(len(zone), bool)
        pairs = neighbours(fd)
        zone = smooth(zone, pairs, cfg.get("smooth_passes", 4), cfg.get("accent_weight", 1.6), fixed)
        for _ in range(2):
            zone, changed = drop_specks(zone, pairs, face_areas(ob), cfg.get("speck_area_m2", 0.2))
            print("REPAINT %s: %d speck faces recoloured" % (ob.name, changed))
        datas.append(fd); zones.append(zone); colours.append(cols)
    allz, allc = np.concatenate(zones), np.concatenate(colours)
    looks = {}
    for i, z in enumerate(ZONES):
        spec = cfg["zones"][z]
        median = np.median(allc[allz == i], axis=0).tolist() if (allz == i).any() else [0.5, 0.5, 0.5]
        looks[z] = dict(colour=spec.get("colour", median), roughness=spec["roughness"], metallic=spec["metallic"],
                        faces=int((allz == i).sum()), ai_median=[round(v, 3) for v in median])
    size, orm_size = bake.get("size", 4096), bake.get("orm_size", 2048)
    bc_vals = np.concatenate([np.array([looks[ZONES[z]]["colour"] for z in zone]) for zone in zones])
    orm_vals = np.concatenate([np.array([[1.0, looks[ZONES[z]]["roughness"], looks[ZONES[z]]["metallic"]] for z in zone]) for zone in zones])
    fd_all = dict(uv=np.concatenate([d["uv"] for d in datas]),
                  start=np.concatenate([d["start"] + sum(len(x["uv"]) for x in datas[:k]) for k, d in enumerate(datas)]),
                  total=np.concatenate([d["total"] for d in datas]))
    clean = np.asarray(rasterise(fd_all, bc_vals, size, (128, 128, 128))).astype(np.float32) / 255.0
    zone_vals = np.concatenate([np.repeat((zone[:, None] + 1) / 8.0, 3, axis=1) for zone in zones])
    zone_img = np.round(np.asarray(rasterise(fd_all, zone_vals, size, (0, 0, 0)))[..., 0] / 255.0 * 8.0).astype(int) - 1
    # accent_exclude_boxes: no orange there (the AI's orange nozzle rims came out as saw-tooth rings)
    excl_vals = np.concatenate([np.repeat(np.any([in_box(d["centre"], b) for b in cfg.get("accent_exclude_boxes", [])] or
                                                 [np.zeros(len(d["start"]), bool)], axis=0)[:, None].astype(np.float32), 3, axis=1)
                                for d in datas])
    excluded = np.asarray(rasterise(fd_all, excl_vals, size, (0, 0, 0)))[..., 0] > 127
    out = texel_pass(clean, zone_img, tex if tex.shape[0] == size else
                     np.asarray(Image.fromarray((tex * 255).astype(np.uint8)).resize((size, size), Image.BILINEAR)).astype(np.float32) / 255.0,
                     cfg, looks, excluded)
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(path(cfg["out_base_color"]))
    rasterise(fd_all, orm_vals, orm_size, (255, 128, 0)).save(path(cfg["out_orm"]))
    for img in bpy.data.images:   # the .blend's preview material shows the new maps next time
        if img.filepath and os.path.normcase(bpy.path.abspath(img.filepath)) in (os.path.normcase(path(cfg["out_base_color"])), os.path.normcase(path(cfg["out_orm"]))):
            img.reload()
    print("REPAINT " + json.dumps({"zones": looks, "base_color": cfg["out_base_color"], "orm": cfg["out_orm"]}))


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:])
