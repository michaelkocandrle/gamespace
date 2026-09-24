"""Mesh-decal and trim-sheet library: small hard-surface details modelled once, captured into texture atlases.

    MSYS_NO_PATHCONV=1 blender -b --factory-startup --python Tools/Blender/decal_library.py -- ArtSource/Ships/Shared/Decals/decal_library.json

How Star Citizen ships get their density (Argo MOLE taken apart): most small detail - grilles, slots,
panel seams, bolts, labels - is not in the hull mesh but in mesh decals, quads floating a hair above the
hull that carry alpha, normal, height, AO and colour. This script is the library behind that:

  - every item of the recipe is built as real geometry (boxes, cylinders, recesses cut into a footprint
    plate, bevelled) in its own cell of a grid on the ground plane;
  - an orthographic camera above the grid renders the passes as emission-only material overrides, float
    EXR, so the values are exact (no lighting, no view transform):
        normal  tangent-space normal, +X right, +Y up (OpenGL; Unreal flips green on import)
        height  0.5 at the hull surface, +- height_range_m
        ao      ambient occlusion within ao_distance_m
        color   the part's colour darkened by its AO; alpha = where the colour replaces the hull's: labels
                and stripes ("paint_color") and parts with their own colour (recess floors, dark slats,
                metal bolts, pass "own"); everything else keeps the hull's paint
        rm      R = roughness, G = metallic of the part
        alpha   footprint of the item (where the decal's normal / AO apply)
  - the passes are written as 8-bit PNGs next to the recipe and a JSON index with every item's UV rect,
    its size in metres and its purpose, so the ship builder can place it by name.

Item types ("type"), because a DBuffer decal has one opacity for everything it writes:
  structural  seams, slots, rivets, bolts, recessed panels, grilles, hatches: normal, roughness and AO only,
              no colour of their own (BC alpha 0) - the hull's paint shows through, the AO darkens it
              through a separate colour-only quad (M_Ship_MeshDecalAO)
  info        stencils, labels, numbers, arrows, hazard stripes, handles: their own colour (BC alpha = where)
  wear        scratches, edge scuffs, drips below grilles: procedural colour with soft alpha, used sparingly
Items are packed onto one sheet at a fixed texel density ("px_per_m", 2048 = 0.5 mm per texel), so every
decal is equally sharp; parts can be boxes, cylinders, hex bolts, domed rivets, rings, extruded outlines
("poly": arrows) and text in the project's fonts (Content/UI/Fonts: Rajdhani, Share Tech Mono).

The same script builds the trim sheet (recipe key "trim"): horizontal strips that tile along U, for
long edges and bands. Both are regenerated from the recipe; to add a detail, add an item.
Prints DECALLIB {...}.
"""
import json
import math
import os
import subprocess
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def path(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


def borrow(module):
    """Blender ships no Pillow, but its Python is the system's version: borrow the system site-packages."""
    try:
        __import__(module)
    except ImportError:
        site = subprocess.run(["python", "-c", "import %s, os; print(os.path.dirname(os.path.dirname(%s.__file__)))" % (module, module)],
                              capture_output=True, text=True).stdout.strip()
        if site and site not in sys.path:
            sys.path.append(site)


# ----------------------------------------------------------------------------------- geometry

def add_box(bm, c, s):
    res = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=s, verts=res["verts"])
    bmesh.ops.translate(bm, vec=c, verts=res["verts"])
    return res["verts"]


def add_cyl(bm, c, r, h, seg=24, axis="Z", r2=None):
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h)
    if axis == "X":
        bmesh.ops.rotate(bm, verts=res["verts"], cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))
    elif axis == "Y":
        bmesh.ops.rotate(bm, verts=res["verts"], cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"))
    bmesh.ops.translate(bm, vec=c, verts=res["verts"])
    return res["verts"]


def add_hex(bm, c, r, h):
    return add_cyl(bm, c, r, h, seg=6)


def add_poly(bm, pts, z0, h):
    """A flat outline (list of [x, y]) extruded from z0 to z0 + h (arrows, chevrons)."""
    verts = [bm.verts.new((x, y, z0)) for x, y in pts]
    face = bm.faces.new(verts)
    res = bmesh.ops.extrude_face_region(bm, geom=[face])
    top = [e for e in res["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, 0, h), verts=top)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


FONTS = {"rajdhani": "Content/UI/Fonts/Rajdhani-SemiBold.ttf", "rajdhani_medium": "Content/UI/Fonts/Rajdhani-Medium.ttf",
         "mono": "Content/UI/Fonts/ShareTechMono-Regular.ttf"}


def add_text(bm, body, font, size, c, z0, h, rot_deg=0.0, align="CENTER"):
    """Text in one of the project's fonts, as raised geometry: size = the font's em in metres."""
    cu = bpy.data.curves.new("txt", "FONT")
    cu.body = body
    cu.font = bpy.data.fonts.load(path(FONTS[font]), check_existing=True)
    cu.size = size
    cu.align_x = align
    cu.align_y = "CENTER"
    cu.extrude = h / 2
    ob = bpy.data.objects.new("txt", cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.rotation_euler = (0, 0, math.radians(rot_deg))
    ob.location = (c[0], c[1], z0 + h / 2)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    me.transform(ob.matrix_world)
    bm.from_mesh(me)
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    bpy.data.meshes.remove(me)


def new_object(name, bm, coll, color, rough, metal, bevel=0.0015):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ob.color = (*color, 1.0)
    ob["rough"], ob["metal"] = rough, metal
    if bevel > 0:
        m = ob.modifiers.new("Bevel", "BEVEL")
        m.width, m.segments, m.limit_method = bevel, 2, "ANGLE"
        m.angle_limit = math.radians(30)
    for p in me.polygons:
        p.use_smooth = False
    return ob


def build_item(item, origin, coll, defaults):
    """One library item: a footprint plate at z=0 (the decal's alpha region, flat) with recesses cut into
    it and parts on top. Units: metres, origin = the item's centre on the ground plane."""
    ox, oy = origin
    fw, fh = item["footprint"]
    paint = tuple(item.get("color", defaults["color"]))
    made = []
    # footprint plate, recesses cut by boolean
    bm = bmesh.new()
    add_box(bm, (ox, oy, -0.002), (fw, fh, 0.004))
    plate = new_object(item["name"] + "_plate", bm, coll, paint, defaults["rough"], 0.0, bevel=0.0)
    plate["footprint"] = True
    for r in item.get("recesses", []):
        bm = bmesh.new()
        d = r["depth"]
        if r.get("round"):
            add_cyl(bm, (ox + r["at"][0], oy + r["at"][1], -d / 2 + 0.0005), r["r"], d + 0.004, seg=32)
        else:
            add_box(bm, (ox + r["at"][0], oy + r["at"][1], -d / 2 + 0.0005), (r["size"][0], r["size"][1], d + 0.004))
        cutter = new_object(item["name"] + "_cut", bm, coll, paint, 0.5, 0.0, bevel=0.0)
        mod = plate.modifiers.new("cut", "BOOLEAN")
        mod.operation, mod.solver, mod.object = "DIFFERENCE", "EXACT", cutter
        bpy.context.view_layer.objects.active = plate
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cutter)
        # recess floor: a thin plate at the bottom, darker, catches the AO
        bm = bmesh.new()
        if r.get("round"):
            add_cyl(bm, (ox + r["at"][0], oy + r["at"][1], -d - 0.001), r["r"], 0.002, seg=32)
        else:
            add_box(bm, (ox + r["at"][0], oy + r["at"][1], -d - 0.001), (r["size"][0], r["size"][1], 0.002))
        floor = new_object(item["name"] + "_floor", bm, coll, tuple(r.get("color", defaults["dark"])), 0.6, 0.0, bevel=0.0)
        floor["own"] = 1.0 if item_type(item) == "info" else 0.0
        made.append(floor)
    made.append(plate)
    parts = list(item.get("parts", []))
    if item.get("corner_screws"):
        # a screw in each corner, inset: the small detail that makes a panel read as fastened
        cs = item["corner_screws"]
        ix, iy = fw / 2 - cs.get("inset", 0.015), fh / 2 - cs.get("inset", 0.015)
        for sx in (-ix, ix):
            for sy in (-iy, iy):
                parts.append({"kind": "hex", "at": [sx, sy], "r": cs.get("r", 0.006), "h": 0.004, "z": cs.get("z", 0.0),
                              "rough": 0.35})
    for i, p in enumerate(parts):
        bm = bmesh.new()
        n = p.get("repeat", 1)
        step = p.get("step", [0, 0])
        for k in range(n):
            at = (ox + p["at"][0] + step[0] * k, oy + p["at"][1] + step[1] * k)
            h = p.get("h", 0.004)
            z = p.get("z", 0.0) + h / 2
            kind = p["kind"]
            if kind == "box":
                add_box(bm, (at[0], at[1], z), (p["size"][0], p["size"][1], h))
            elif kind == "cyl":
                add_cyl(bm, (at[0], at[1], z), p["r"], h, seg=p.get("seg", 24))
            elif kind == "hex":
                add_hex(bm, (at[0], at[1], z), p["r"], h)
            elif kind == "bar":      # a round bar lying along X (handle grip, pipe)
                add_cyl(bm, (at[0], at[1], p.get("z", 0.0) + p["r"]), p["r"], p["size"][0], seg=16, axis="X")
            elif kind == "bar_y":
                add_cyl(bm, (at[0], at[1], p.get("z", 0.0) + p["r"]), p["r"], p["size"][1], seg=16, axis="Y")
            elif kind == "rivet":    # domed rivet head
                add_cyl(bm, (at[0], at[1], p.get("z", 0.0) + h / 2), p["r"], h, seg=16, r2=p["r"] * 0.55)
            elif kind == "ring":
                add_cyl(bm, (at[0], at[1], z), p["r"], h, seg=p.get("seg", 32))
                add_cyl(bm, (at[0], at[1], z + h * 0.6), p["r"] * p.get("inner", 0.6), h * 0.6, seg=p.get("seg", 32))
            elif kind == "poly":
                add_poly(bm, [(at[0] + x, at[1] + y) for x, y in p["points"]], p.get("z", 0.0), h)
            elif kind == "text":
                add_text(bm, p["body"], p.get("font", "rajdhani"), p["size"], at, p.get("z", 0.0), h,
                         p.get("rot", 0.0), p.get("align", "CENTER"))
        ob = new_object("%s_p%d" % (item["name"], i), bm, coll, tuple(p.get("color", paint)),
                        p.get("rough", defaults["rough"]), p.get("metal", 0.0), bevel=p.get("bevel", 0.0012))
        # only info items carry colour; a structural item takes the hull's paint (its AO darkens it)
        ob["own"] = 1.0 if item_type(item) == "info" and not p.get("no_color") else 0.0
        made.append(ob)
    return made


# ----------------------------------------------------------------------------------- passes

def emission_override(name, build):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    build(nt, em)
    return m


def pass_materials(cfg):
    def normal(nt, em):
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        ma = nt.nodes.new("ShaderNodeVectorMath"); ma.operation = "MULTIPLY_ADD"
        ma.inputs[1].default_value = (0.5, 0.5, 0.5); ma.inputs[2].default_value = (0.5, 0.5, 0.5)
        nt.links.new(geo.outputs["Normal"], ma.inputs[0])
        nt.links.new(ma.outputs[0], em.inputs["Color"])

    def height(nt, em):
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        mp = nt.nodes.new("ShaderNodeMapRange")
        mp.inputs["From Min"].default_value = -cfg["height_range_m"]
        mp.inputs["From Max"].default_value = cfg["height_range_m"]
        nt.links.new(geo.outputs["Position"], sep.inputs[0])
        nt.links.new(sep.outputs["Z"], mp.inputs["Value"])
        nt.links.new(mp.outputs["Result"], em.inputs["Color"])

    def ao(nt, em):
        a = nt.nodes.new("ShaderNodeAmbientOcclusion")
        a.inputs["Distance"].default_value = cfg["ao_distance_m"]
        a.samples = 16
        nt.links.new(a.outputs["AO"], em.inputs["Color"])

    def color(nt, em):
        oi = nt.nodes.new("ShaderNodeObjectInfo")
        nt.links.new(oi.outputs["Color"], em.inputs["Color"])

    def rm(nt, em):
        r = nt.nodes.new("ShaderNodeAttribute"); r.attribute_type = "OBJECT"; r.attribute_name = "rough"
        g = nt.nodes.new("ShaderNodeAttribute"); g.attribute_type = "OBJECT"; g.attribute_name = "metal"
        comb = nt.nodes.new("ShaderNodeCombineXYZ")
        nt.links.new(r.outputs["Fac"], comb.inputs["X"])
        nt.links.new(g.outputs["Fac"], comb.inputs["Y"])
        nt.links.new(comb.outputs[0], em.inputs["Color"])

    def own(nt, em):
        a = nt.nodes.new("ShaderNodeAttribute"); a.attribute_type = "OBJECT"; a.attribute_name = "own"
        nt.links.new(a.outputs["Fac"], em.inputs["Color"])

    return {k: emission_override("PASS_" + k, f) for k, f in
            (("normal", normal), ("height", height), ("ao", ao), ("color", color), ("rm", rm), ("own", own))}


def render_passes(scene, mats, size_px, extent_m, centre, out_dir, prefix):
    cam_data = bpy.data.cameras.new("DL_Cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = extent_m
    cam = bpy.data.objects.new("DL_Cam", cam_data)
    scene.collection.objects.link(cam)
    cam.location = (centre[0], centre[1], 5.0)
    scene.camera = cam
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = False
    scene.cycles.filter_width = 0.8
    scene.render.resolution_x = scene.render.resolution_y = size_px
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.render.image_settings.file_format = "OPEN_EXR"
    scene.render.image_settings.color_depth = "32"
    scene.world = scene.world or bpy.data.worlds.new("DL")
    scene.world.use_nodes = True
    bg = next(n for n in scene.world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Strength"].default_value = 0.0
    files = {}
    for key, m in mats.items():
        bpy.context.view_layer.material_override = m
        f = os.path.join(out_dir, "_%s_%s.exr" % (prefix, key))
        scene.render.filepath = f
        bpy.ops.render.render(write_still=True)
        files[key] = f
    bpy.context.view_layer.material_override = None
    bpy.data.objects.remove(cam)
    return files


def exr_to_png(files, out_dir, prefix, wear=()):
    """EXR passes -> 8-bit PNG maps with raw (linear) values: the data maps must not get an sRGB curve;
    only the colour map is sRGB."""
    borrow("PIL")
    import numpy as np
    from PIL import Image

    def load(f):
        img = bpy.data.images.load(f)
        w, h = img.size
        a = np.empty(w * h * 4, np.float32)
        img.pixels.foreach_get(a)
        bpy.data.images.remove(img)
        return np.flipud(a.reshape(h, w, 4))

    alpha = load(files["normal"])[..., 3]
    maps = {}
    n = load(files["normal"])[..., :3]
    n = np.where(alpha[..., None] > 0.5, n, np.array([0.5, 0.5, 1.0], np.float32))
    maps["N"] = n
    hgt = load(files["height"])[..., 0]
    maps["H"] = np.where(alpha > 0.5, hgt, 0.5)
    maps["AO"] = np.where(alpha > 0.5, load(files["ao"])[..., 0], 1.0)
    # colour darkened by the item's own occlusion: the paint master's colour is all the AO a DBuffer
    # decal can show (there is no AO channel)
    col = load(files["color"])[..., :3] * maps["AO"][..., None]
    srgb = np.where(col <= 0.0031308, col * 12.92, 1.055 * np.power(np.clip(col, 0, None), 1 / 2.4) - 0.055)
    rm = load(files["rm"])
    written = {}
    for key, arr in maps.items():
        a8 = (np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8)
        fn = os.path.join(out_dir, "%s_%s.png" % (prefix, key))
        Image.fromarray(a8, "RGB" if a8.ndim == 3 else "L").save(fn)
        written[key] = fn
    # colour + its own opacity (1 only where an item says its colour replaces the hull's)
    own = np.where(alpha > 0.5, load(files["own"])[..., 0], 0.0)
    copa = (own > 0.5).astype(np.float32)
    bc = np.dstack([np.clip(srgb, 0, 1), copa[..., None]]).astype(np.float32)
    # M: R = alpha (where normal / AO apply), G = roughness, B = metallic
    m = np.dstack([alpha, np.clip(rm[..., 0], 0, 1), np.clip(rm[..., 1], 0, 1)]).astype(np.float32)
    maps2 = {"BC": bc, "M": m}
    keep = np.zeros(alpha.shape, bool)
    keep |= bc[..., 3] > 0.02
    for it, rect in wear:
        procedural_wear(maps2, m[..., 0], it, rect)
        keep[rect[1]:rect[3], rect[0]:rect[2]] = True
    m[..., 0] = feature_alpha(m[..., 0], maps["N"] * 2 - 1, maps["H"], keep)
    bc[..., :3] = dilate_colour(bc[..., :3], bc[..., 3] > 0.02)
    fn = os.path.join(out_dir, "%s_BC.png" % prefix)
    Image.fromarray((np.clip(bc, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(fn)
    written["BC"] = fn
    fn = os.path.join(out_dir, "%s_M.png" % prefix)
    Image.fromarray((m * 255 + 0.5).astype(np.uint8), "RGB").save(fn)
    written["M"] = fn
    for f in files.values():
        os.remove(f)
    return written


def feature_alpha(m_r, n, hgt, keep):
    """Alpha of structural decals only where there is a feature: the normal leaves the plane or the height
    leaves the surface (rivets, grooves, grilles, embossed text), grown by a few texels and softened. The
    flat rest of the footprint wrote the item's roughness over the paint and drew the outline of every
    decal (24. 9. 2026). keep: texels of info / wear items, whose alpha stays as rendered."""
    import numpy as np
    feat = ((np.abs(n[..., 0]) > 0.03) | (np.abs(n[..., 1]) > 0.03) | (np.abs(hgt - 0.5) > 0.003)).astype(np.float32)
    # the footprint plate's own rim is not a feature: drop what lies within 5 texels of the footprint edge
    inner = (m_r > 0.5).astype(np.float32)
    for _ in range(5):
        inner = np.minimum.reduce([inner, np.roll(inner, 1, 0), np.roll(inner, -1, 0), np.roll(inner, 1, 1), np.roll(inner, -1, 1)])
    feat *= inner
    grown = feat.copy()
    for _ in range(4):
        grown = np.maximum.reduce([grown, np.roll(grown, 1, 0), np.roll(grown, -1, 0), np.roll(grown, 1, 1), np.roll(grown, -1, 1)])
    soft = grown.copy()
    for _ in range(2):
        soft = (soft + np.roll(soft, 1, 0) + np.roll(soft, -1, 0) + np.roll(soft, 1, 1) + np.roll(soft, -1, 1)) / 5.0
    return np.where(keep, m_r, np.minimum(m_r, soft))


def refine(recipe_path):
    """Rewrites T_Decals_M / T_Trim_M alpha from the existing maps (feature_alpha) without rendering."""
    borrow("PIL")
    import numpy as np
    from PIL import Image
    out_dir = os.path.dirname(path(recipe_path))
    index = json.load(open(os.path.join(out_dir, "decal_library_index.json"), encoding="utf-8"))
    for prefix in ("T_Decals", "T_Trim"):
        m = np.array(Image.open(os.path.join(out_dir, prefix + "_M.png"))).astype(np.float32) / 255
        n = np.array(Image.open(os.path.join(out_dir, prefix + "_N.png"))).astype(np.float32)[..., :3] / 255 * 2 - 1
        hgt = np.array(Image.open(os.path.join(out_dir, prefix + "_H.png"))).astype(np.float32) / 255
        if hgt.ndim == 3:
            hgt = hgt[..., 0]
        keep = np.zeros(m.shape[:2], bool)
        if prefix == "T_Decals":
            H, W = keep.shape
            for it in index["decals"].values():
                if it.get("type") in ("info", "wear"):
                    u0, v0, u1, v1 = it["uv"]
                    keep[int((1 - v1) * H):int((1 - v0) * H), int(u0 * W):int(u1 * W)] = True
        m[..., 0] = feature_alpha(m[..., 0], n, hgt, keep)
        Image.fromarray((np.clip(m, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB").save(os.path.join(out_dir, prefix + "_M.png"))
    print("DECALLIB refined alpha")


def dilate_colour(rgb, mask, steps=48):
    """Colour grown out of the opaque texels into the transparent ones around them. The decal material
    uses straight alpha, so in the smaller mips a half-transparent texel averages the opaque part's colour
    with whatever colour the transparent part had - the light plate colour, which drew a light frame round
    every dark grille on the dark hull in the game (24. 9. 2026)."""
    import numpy as np
    out = rgb * mask[..., None]
    filled = mask.copy()
    for _ in range(steps):
        acc = np.zeros_like(out)
        cnt = np.zeros(mask.shape, np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            acc += np.roll(np.roll(out * filled[..., None], dy, 0), dx, 1)
            cnt += np.roll(np.roll(filled.astype(np.float32), dy, 0), dx, 1)
        new = (~filled) & (cnt > 0)
        if not new.any():
            break
        out[new] = acc[new] / cnt[new][..., None]
        filled |= new
    out[~filled] = rgb[~filled]
    return out


def item_type(item):
    return item.get("type") or ("info" if item.get("paint_color") else "structural")


def has_color(item):
    """Does the item carry its own colour (info and wear items)? The ship builder uses the paint material
    for those and the normal + AO pair for structural ones."""
    return item_type(item) in ("info", "wear")


def pack(items, sheet_m, pad):
    """Shelf packing of the items' footprints onto a square sheet (metres, y up). Returns the centre of each
    item; fails loudly if the sheet is too small (then raise px_per_m's sheet or split the library)."""
    order = sorted(items, key=lambda it: -it["footprint"][1])
    x, y_top, row_h, centres = pad, sheet_m - pad, 0.0, {}
    for it in order:
        w, h = it["footprint"]
        if x + w + pad > sheet_m:
            x, y_top, row_h = pad, y_top - row_h - pad, 0.0
        if y_top - h < 0:
            raise RuntimeError("decal sheet full at %s: make the sheet larger" % it["name"])
        centres[it["name"]] = (x + w / 2, y_top - h / 2)
        x += w + pad
        row_h = max(row_h, h)
    return centres


def procedural_wear(maps, alpha, it, rect):
    """Wear items have no geometry: their colour, alpha and roughness are drawn here, into their rectangle."""
    borrow("PIL")
    import numpy as np
    x0, y0, x1, y1 = rect
    w, h = x1 - x0, y1 - y0
    rng = np.random.default_rng(it["procedural"].get("seed", 1))
    kind = it["procedural"]["kind"]
    a = np.zeros((h, w), np.float32)
    col = np.array(it["procedural"].get("color", [0.08, 0.07, 0.06]), np.float32)
    rough = it["procedural"].get("rough", 0.7)
    metal = it["procedural"].get("metal", 0.0)
    if kind == "streak":
        # drips running down from a seam or grille: a few streaks, strongest at the top, fading down
        yy = np.linspace(0, 1, h)[:, None]
        for _ in range(it["procedural"].get("count", 7)):
            cx, sw = rng.uniform(0.1, 0.9) * w, rng.uniform(0.02, 0.08) * w
            length = rng.uniform(0.4, 1.0)
            xs = np.arange(w)[None, :]
            prof = np.exp(-((xs - cx) / sw) ** 2)
            fade = np.clip(1 - yy / length, 0, 1) ** 1.5
            a = np.maximum(a, prof * fade * rng.uniform(0.4, 0.9))
        a *= 0.85 + 0.15 * rng.random((h, w))
    elif kind == "scratches":
        # thin bright scratches through the paint to bare metal
        for _ in range(it["procedural"].get("count", 40)):
            px, py = rng.uniform(0, w), rng.uniform(0, h)
            ang, length = rng.uniform(0, math.pi), rng.uniform(0.05, 0.35) * max(w, h)
            steps = int(length)
            for k in range(steps):
                qx, qy = int(px + math.cos(ang) * k), int(py + math.sin(ang) * k)
                if 0 <= qx < w and 0 <= qy < h:
                    a[qy, qx] = max(a[qy, qx], 0.8 * (1 - abs(k / max(steps, 1) - 0.5)))
    elif kind == "scuff":
        # a worn band along an edge (top of the rectangle), broken up
        yy = np.linspace(0, 1, h)[:, None]
        noise = rng.random((h // 4 + 1, w // 4 + 1))
        noise = np.kron(noise, np.ones((4, 4)))[:h, :w]
        a = np.clip((1 - yy * 1.6) * (noise * 1.3 - 0.35), 0, 1)
    maps["BC"][y0:y1, x0:x1, :3] = np.where(a[..., None] > 0.01, col, maps["BC"][y0:y1, x0:x1, :3])
    maps["BC"][y0:y1, x0:x1, 3] = a
    alpha[y0:y1, x0:x1] = a
    maps["M"][y0:y1, x0:x1, 1] = rough
    maps["M"][y0:y1, x0:x1, 2] = metal


# ----------------------------------------------------------------------------------- main

def main(argv):
    recipe = json.load(open(path(argv[0]), encoding="utf-8"))
    out_dir = os.path.dirname(path(argv[0]))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    defaults = recipe["defaults"]
    index = {"decals": {}, "trim": {}}
    result = {}

    # decal atlas
    d = recipe["decals"]
    size = d["size_px"]
    extent = size / d["px_per_m"]          # fixed texel density: every decal equally sharp
    coll = bpy.data.collections.new("Decals")
    scene.collection.children.link(coll)
    centres = pack(d["items"], extent, d.get("pad_m", 0.02))
    wear = []
    for it in d["items"]:
        cx, cy = centres[it["name"]]
        fw, fh = it["footprint"]
        if it.get("procedural"):
            px = size / extent
            wear.append((it, (int((cx - fw / 2) * px), int((extent - cy - fh / 2) * px),
                              int((cx + fw / 2) * px), int((extent - cy + fh / 2) * px))))
        else:
            build_item(it, (cx, cy), coll, defaults)
        index["decals"][it["name"]] = {
            "uv": [(cx - fw / 2) / extent, (cy - fh / 2) / extent, (cx + fw / 2) / extent, (cy + fh / 2) / extent],
            "size_m": [fw, fh], "purpose": it.get("purpose", ""), "type": item_type(it), "has_color": has_color(it),
            "tags": it.get("tags", [])}
    mats = pass_materials(recipe)
    files = render_passes(scene, mats, size, extent, (extent / 2, extent / 2), out_dir, "T_Decals")
    result["decals"] = exr_to_png(files, out_dir, "T_Decals", wear)
    for o in list(coll.objects):
        bpy.data.objects.remove(o)

    # trim sheet: strips stacked in V, each tiling along U
    t = recipe["trim"]
    tw = t["width_m"]
    tsize = t["size_px"]
    coll2 = bpy.data.collections.new("Trim")
    scene.collection.children.link(coll2)
    v = 0.0
    for strip in t["strips"]:
        hgt = strip["height_m"]
        cy = tw - (v + hgt / 2)          # strips from the top of the square sheet down
        item = dict(strip)
        item["footprint"] = [tw * 1.2, hgt]     # the plate overhangs both ends so the strip tiles
        build_item(item, (tw / 2, cy), coll2, defaults)
        index["trim"][strip["name"]] = {"v": [(cy - hgt / 2) / tw, (cy + hgt / 2) / tw], "height_m": hgt,
                                         "tile_m": tw, "purpose": strip.get("purpose", ""), "type": item_type(strip),
                                         "has_color": has_color(strip)}
        v += hgt
    files = render_passes(scene, mats, tsize, tw, (tw / 2, tw / 2), out_dir, "T_Trim")
    result["trim"] = exr_to_png(files, out_dir, "T_Trim")
    index["decal_atlas_m"], index["trim_width_m"] = extent, tw
    index["maps"] = {"N": "tangent normal, OpenGL (+Y up): Unreal flip green", "H": "height, 0.5 = surface, +-%.3f m" % recipe["height_range_m"],
                     "AO": "ambient occlusion", "BC": "sRGB colour x AO, A = colour opacity (info and wear items only)", "M": "R alpha (normal/AO opacity), G roughness, B metallic"}
    with open(os.path.join(out_dir, "decal_library_index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, indent=1, ensure_ascii=False)
    print("DECALLIB " + json.dumps({"decals": len(index["decals"]), "trim": len(index["trim"]), "files": result}))


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:]
    if args and args[0] == "refine":
        refine(args[1])       # only the alpha rule changed: no need to render the passes again
    else:
        main(args)
