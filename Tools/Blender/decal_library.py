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
        floor["own"] = 1.0
        made.append(floor)
    made.append(plate)
    for i, p in enumerate(item.get("parts", [])):
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
        ob = new_object("%s_p%d" % (item["name"], i), bm, coll, tuple(p.get("color", paint)),
                        p.get("rough", defaults["rough"]), p.get("metal", 0.0), bevel=p.get("bevel", 0.0012))
        # a part with its own colour (dark slats, metal bolts) shows it; the rest keeps the hull's paint
        ob["own"] = 1.0 if ("color" in p or item.get("paint_color")) else 0.0
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


def exr_to_png(files, out_dir, prefix, footprint_mask=None):
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
    copa = footprint_mask if footprint_mask is not None else np.zeros_like(alpha)
    own = np.where(alpha > 0.5, load(files["own"])[..., 0], 0.0)
    copa = np.maximum(copa, (own > 0.5).astype(np.float32))
    bc = np.dstack([dilate_colour(np.clip(srgb, 0, 1), copa > 0.5), copa[..., None]])
    fn = os.path.join(out_dir, "%s_BC.png" % prefix)
    Image.fromarray((bc * 255 + 0.5).astype(np.uint8), "RGBA").save(fn)
    written["BC"] = fn
    # M: R = alpha (where normal / AO apply), G = roughness, B = metallic
    m = np.dstack([alpha, np.clip(rm[..., 0], 0, 1), np.clip(rm[..., 1], 0, 1)])
    fn = os.path.join(out_dir, "%s_M.png" % prefix)
    Image.fromarray((m * 255 + 0.5).astype(np.uint8), "RGB").save(fn)
    written["M"] = fn
    for f in files.values():
        os.remove(f)
    return written


def dilate_colour(rgb, mask, steps=64):
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


def colour_opacity_mask(items, cells, cell_px, size_px):
    """Where an item's colour replaces the hull's: its footprint when "paint_color" is set."""
    borrow("PIL")
    import numpy as np
    m = np.zeros((size_px, size_px), np.float32)
    for it in items:
        if not it.get("paint_color"):
            continue
        c, r = it["cell"]
        span = it.get("span", [1, 1])
        m[r * cell_px:(r + span[1]) * cell_px, c * cell_px:(c + span[0]) * cell_px] = 1.0
    return m


def has_color(item):
    """Does any of the item show its own colour (BC alpha > 0)? The ship builder then adds a second quad
    with the paint material; items without it need only the normal-only decal."""
    return bool(item.get("paint_color") or item.get("recesses") or any("color" in p for p in item.get("parts", [])))


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
    cells, cell_m = d["cells"], d["cell_m"]
    extent = cells * cell_m
    size = d["size_px"]
    coll = bpy.data.collections.new("Decals")
    scene.collection.children.link(coll)
    for it in d["items"]:
        c, r = it["cell"]
        span = it.get("span", [1, 1])
        centre = ((c + span[0] / 2) * cell_m, extent - (r + span[1] / 2) * cell_m)
        build_item(it, centre, coll, defaults)
        fw, fh = it["footprint"]
        cx, cy = centre
        index["decals"][it["name"]] = {
            "uv": [(cx - fw / 2) / extent, (cy - fh / 2) / extent, (cx + fw / 2) / extent, (cy + fh / 2) / extent],
            "size_m": [fw, fh], "purpose": it.get("purpose", ""), "paint_color": bool(it.get("paint_color")),
            "has_color": has_color(it)}
    mats = pass_materials(recipe)
    files = render_passes(scene, mats, size, extent, (extent / 2, extent / 2), out_dir, "T_Decals")
    result["decals"] = exr_to_png(files, out_dir, "T_Decals", colour_opacity_mask(d["items"], cells, size // cells, size))
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
                                         "tile_m": tw, "purpose": strip.get("purpose", ""), "has_color": has_color(strip)}
        v += hgt
    files = render_passes(scene, mats, tsize, tw, (tw / 2, tw / 2), out_dir, "T_Trim")
    result["trim"] = exr_to_png(files, out_dir, "T_Trim")
    index["decal_atlas_m"], index["trim_width_m"] = extent, tw
    index["maps"] = {"N": "tangent normal, OpenGL (+Y up): Unreal flip green", "H": "height, 0.5 = surface, +-%.3f m" % recipe["height_range_m"],
                     "AO": "ambient occlusion", "BC": "sRGB colour x AO, A = colour opacity (labels + parts with their own colour)", "M": "R alpha (normal/AO opacity), G roughness, B metallic"}
    with open(os.path.join(out_dir, "decal_library_index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, indent=1, ensure_ascii=False)
    print("DECALLIB " + json.dumps({"decals": len(index["decals"]), "trim": len(index["trim"]), "files": result}))


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:])
