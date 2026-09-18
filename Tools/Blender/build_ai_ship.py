"""AI model -> game-ready ship .blend, driven by one config file per ship (Docs/Ships/ShipPipeline.md, 2B).

    blender -b --python Tools\\Blender\\build_ai_ship.py -- ArtSource\\Ships\\<Ship>\\<Ship>_ai_build.json [--no-save]

Builds the ship from the raw AI export every time (a Meshy / Higgsfield FBX with PBR textures), so
the whole conversion is repeatable and reviewable as data. Steps, all driven by the config:

  1. import the source FBX into an empty scene, join it, apply its transforms;
  2. orient and size: rotate about Z so the nose points along +X, scale to length_m;
  3. parts: faces inside region boxes move to SM_Ship_<Ship>_<Part> (e.g. the landing gear, which AI
     models fuse into the hull); the holes the cut leaves in the hull are filled;
  4. decimate hull and parts to their triangle targets, keeping detail where "importance" rules say
     the player looks (tops, cockpit, nose) and removing more underneath and inside nozzles;
  5. a fresh UV atlas for the decimated meshes, and the source re-baked onto it: base colour, ORM
     (R 1, G roughness, B metallic) and a normal map of the full-resolution shading. AI atlases have
     thousands of tiny islands that decimation welds together, so the source UVs cannot be kept.
     Materials: one PBR slot M_Ship_<Ship>_Hull (the "pbr" master in Unreal) plus an emissive slot
     for nozzle discs, which the game makes glow;
  6. collision: one convex UCX hull per region box (a 26-direction k-DOP of the vertices inside,
     so at most 26 vertices each);
  7. sockets: explicit positions, or "bottom" of a part region (landing gear pad soles);
  8. saves out_blend. The old source file is never touched.

Coordinates in the config are Blender metres AFTER step 2: +X nose, +Y the ship's left, +Z up.
Measure them in the oriented model (Tools/Blender/build_ai_ship.py -- <config> --no-save prints the
bounds, and a first run with empty parts / collision is a good start). Then export as usual with
gamespace_ship_export.py and import with Tools/Assets/import_ship.py.
"""

import json
import math
import os
import sys
import time

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KDOP = [Vector(d).normalized() for d in (
    (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1),
    (1, 1, 0), (1, -1, 0), (-1, 1, 0), (-1, -1, 0), (1, 0, 1), (1, 0, -1), (-1, 0, 1), (-1, 0, -1),
    (0, 1, 1), (0, 1, -1), (0, -1, 1), (0, -1, -1),
    (1, 1, 1), (1, 1, -1), (1, -1, 1), (1, -1, -1), (-1, 1, 1), (-1, 1, -1), (-1, -1, 1), (-1, -1, -1))]


def log(msg):
    print("AISHIP " + msg)


def path(p):
    return p if os.path.isabs(p) else os.path.join(REPO, p)


def in_box(p, box):
    return all(lo <= p[i] <= hi for i, (lo, hi) in enumerate((box.get("x", (-1e9, 1e9)), box.get("y", (-1e9, 1e9)), box.get("z", (-1e9, 1e9)))))


def tri_count(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def bounds(obs):
    pts = [o.matrix_world @ v.co for o in obs for v in o.data.vertices]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])


def select_only(ob):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)


# --- 1-2: import, orient, size -----------------------------------------------------------------

def import_source(cfg, ship):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    bpy.ops.import_scene.fbx(filepath=path(cfg["source_fbx"]))
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    for o in list(bpy.data.objects):
        if o.type != "MESH":
            bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    hull = bpy.context.view_layer.objects.active
    hull.parent = None
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    lo, hi = bounds([hull])
    size = hi - lo
    orient = cfg["orient"]
    scale = orient["length_m"] / size.x if "length_m" in orient else 1.0
    centre = (lo + hi) * 0.5
    matrix = (Matrix.Rotation(math.radians(orient.get("rotate_z_deg", 0.0)), 4, "Z") @ Matrix.Scale(scale, 4)
              @ Matrix.Translation(-Vector((centre.x, centre.y, 0.0))))
    hull.data.transform(matrix)
    hull.data.update()
    hull.name = hull.data.name = "SM_Ship_%s" % ship
    lo, hi = bounds([hull])
    log("source %s: %d triangles, oriented and scaled x%.3f to %s m, min %s max %s" % (
        os.path.basename(cfg["source_fbx"]), tri_count(hull), scale, tuple(round(c, 2) for c in hi - lo),
        tuple(round(c, 2) for c in lo), tuple(round(c, 2) for c in hi)))
    return hull


# --- 3: parts -------------------------------------------------------------------------------------

def split_part(hull, ship, part, spec):
    regions = spec["regions"]
    bm = bmesh.new()
    bm.from_mesh(hull.data)
    picked = [f for f in bm.faces if all(any(in_box(v.co, r) for r in regions) for v in f.verts)]
    if not picked:
        bm.free()
        log("part %s: nothing inside its regions" % part)
        return None
    for f in bm.faces:
        f.select_set(False)
    for f in picked:
        f.select_set(True)
    bm.to_mesh(hull.data)
    bm.free()
    select_only(hull)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.separate(type="SELECTED")
    bpy.ops.object.mode_set(mode="OBJECT")
    ob = next(o for o in bpy.context.selected_objects if o != hull)
    ob.name = ob.data.name = "SM_Ship_%s_%s" % (ship, part)
    log("part %s: %d triangles moved out of the hull" % (ob.name, tri_count(ob)))
    if spec.get("fill_holes", True):
        for target in (hull, ob):
            bm = bmesh.new()
            bm.from_mesh(target.data)
            edges = [e for e in bm.edges if e.is_boundary]
            before = len(edges)
            bmesh.ops.holes_fill(bm, edges=edges, sides=spec.get("max_hole_sides", 400))
            left = sum(1 for e in bm.edges if e.is_boundary)
            bm.to_mesh(target.data)
            bm.free()
            log("  %s: %d open edges after the cut, %d left after filling holes" % (target.name, before, left))
    return ob


# --- 4: decimate ------------------------------------------------------------------------------------

def importance_weights(ob, rules, default):
    weights = []
    for v in ob.data.vertices:
        w = default
        for rule in rules:
            if "box" in rule and not in_box(v.co, rule["box"]):
                continue
            if "normal_z_min" in rule and v.normal.z < rule["normal_z_min"]:
                continue
            if "normal_z_max" in rule and v.normal.z > rule["normal_z_max"]:
                continue
            w = rule["weight"]
        weights.append(w)
    return weights


def decimate(ob, target, rules, default, factor):
    tris = tri_count(ob)
    if tris <= target:
        return
    t = time.time()
    group = ob.vertex_groups.new(name="Importance")
    weights = importance_weights(ob, rules, default)
    for level in sorted(set(weights)):
        group.add([i for i, w in enumerate(weights) if w == level], level, "REPLACE")
    select_only(ob)
    mod = ob.modifiers.new("Decimate", "DECIMATE")
    mod.decimate_type = "COLLAPSE"
    mod.ratio = target / tris
    mod.use_collapse_triangulate = True
    # Blender protects vertices with a LOW group weight (higher collapse cost), so importance is inverted.
    mod.vertex_group = group.name
    mod.invert_vertex_group = True
    mod.vertex_group_factor = factor
    bpy.ops.object.modifier_apply(modifier=mod.name)
    leftover = ob.vertex_groups.get("Importance")
    if leftover:
        ob.vertex_groups.remove(leftover)
    log("decimate %s: %d -> %d triangles (target %d) in %.0f s" % (ob.name, tris, tri_count(ob), target, time.time() - t))


def keep_high_copy(ob):
    """A copy of the full-resolution mesh (with the source material): what the textures are re-baked from."""
    high = ob.copy()
    high.data = ob.data.copy()
    high.name = "HIGH_" + ob.name
    bpy.context.scene.collection.objects.link(high)
    return high


def density_report(ob, rules, default):
    """Triangles per square metre on important vs unimportant surfaces, to show the weighting worked."""
    weights = importance_weights(ob, rules, default)
    buckets = {}
    for p in ob.data.polygons:
        w = max(weights[i] for i in p.vertices)
        b = buckets.setdefault(w, [0, 0.0])
        b[0] += 1
        b[1] += p.area
    for w in sorted(buckets):
        n, area = buckets[w]
        log("  importance %.2f: %6d triangles on %6.1f m2 = %6.0f per m2" % (w, n, area, n / max(area, 1e-6)))


# --- 5: new UVs, re-baked textures, materials ------------------------------------------------------

def preview_material(name, maps):
    """The PBR look in Blender. maps: base_color, normal, and either roughness + metallic (the source)
    or orm (the re-baked one: G roughness, B metallic)."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]

    def tex(key, colour):
        node = nt.nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(path(maps[key]))
        if not colour:
            node.image.colorspace_settings.name = "Non-Color"
        node.label = key
        return node
    nt.links.new(tex("base_color", True).outputs[0], bsdf.inputs["Base Color"])
    if "orm" in maps:
        split = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(tex("orm", False).outputs[0], split.inputs[0])
        nt.links.new(split.outputs[1], bsdf.inputs["Roughness"])
        nt.links.new(split.outputs[2], bsdf.inputs["Metallic"])
    else:
        nt.links.new(tex("metallic", False).outputs[0], bsdf.inputs["Metallic"])
        nt.links.new(tex("roughness", False).outputs[0], bsdf.inputs["Roughness"])
    normal = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tex("normal", False).outputs[0], normal.inputs["Color"])
    nt.links.new(normal.outputs[0], bsdf.inputs["Normal"])
    return mat


def unwrap(lows, margin, angle_deg):
    """One fresh UV atlas for the decimated hull and parts together. The AI atlas has thousands of tiny
    islands, and decimation welded them: triangles stretched across half the texture."""
    bpy.ops.object.select_all(action="DESELECT")
    for ob in lows:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = lows[0]
    t = time.time()
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle_deg), island_margin=margin, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    log("new UVs for %s in %.0f s" % (", ".join(o.name for o in lows), time.time() - t))


def rebake(pairs, source_material, spec):
    """Bakes the full-resolution model onto the decimated one's new UVs (Cycles, selected to active):
    base colour and ORM through an emission shader (exact texture values, no lighting), and a
    tangent-space normal map of the source's shading, so 200k triangles shade like 3.4 million."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 1
    nt = source_material.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    output = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    textures = {n.label: n for n in nt.nodes if n.type == "TEX_IMAGE"}
    emission = nt.nodes.new("ShaderNodeEmission")
    combine = nt.nodes.new("ShaderNodeCombineColor")
    combine.inputs[0].default_value = 1.0  # R: ambient occlusion, none
    nt.links.new(textures["roughness"].outputs[0], combine.inputs[1])
    nt.links.new(textures["metallic"].outputs[0], combine.inputs[2])

    target = bpy.data.materials.new("BakeTarget")
    target.use_nodes = True
    target_node = target.node_tree.nodes.new("ShaderNodeTexImage")
    target.node_tree.nodes.active = target_node
    kept = {low.name: list(low.data.materials) for low, _ in pairs}
    for low, _ in pairs:
        low.data.materials.clear()
        low.data.materials.append(target)

    def bake(key, size, colour, bake_type, emit_from):
        image = bpy.data.images.new(os.path.splitext(os.path.basename(spec[key]))[0], size, size, alpha=False)
        image.colorspace_settings.name = "sRGB" if colour else "Non-Color"
        image.generated_color = (0.5, 0.5, 1.0, 1.0) if bake_type == "NORMAL" else (0.0, 0.0, 0.0, 1.0)
        target_node.image = image
        if emit_from is not None:
            nt.links.new(emit_from, emission.inputs["Color"])
            nt.links.new(emission.outputs[0], output.inputs["Surface"])
        else:
            nt.links.new(bsdf.outputs[0], output.inputs["Surface"])
        t = time.time()
        for low, high in pairs:
            bpy.ops.object.select_all(action="DESELECT")
            high.select_set(True)
            low.select_set(True)
            bpy.context.view_layer.objects.active = low
            kwargs = dict(type=bake_type, use_selected_to_active=True, use_clear=False, margin=spec.get("margin_px", 16),
                          cage_extrusion=spec.get("cage_extrusion_m", 0.05), max_ray_distance=spec.get("max_ray_m", 0.2))
            if bake_type == "NORMAL":
                kwargs["normal_space"] = "TANGENT"
            bpy.ops.object.bake(**kwargs)
        os.makedirs(os.path.dirname(path(spec[key])), exist_ok=True)
        image.filepath_raw = path(spec[key])
        image.file_format = "PNG"
        image.save()
        log("baked %s %dx%d in %.0f s -> %s" % (key, size, size, time.time() - t, spec[key]))

    bake("base_color", spec.get("size", 4096), True, "EMIT", textures["base_color"].outputs[0])
    bake("orm", spec.get("orm_size", 2048), False, "EMIT", combine.outputs[0])
    bake("normal", spec.get("size", 4096), False, "NORMAL", None)
    nt.links.new(bsdf.outputs[0], output.inputs["Surface"])
    for low, _ in pairs:
        low.data.materials.clear()
        for m in kept[low.name]:
            low.data.materials.append(m)
    bpy.data.materials.remove(target)


def emissive_material(ship, colour):
    mat = bpy.data.materials.new("M_Ship_%s_Emissive" % ship)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Emission Color"].default_value = (colour[0], colour[1], colour[2], 1.0)
    bsdf.inputs["Emission Strength"].default_value = 5.0
    return mat


def assign_emissive(hull, spec, mat):
    """Nozzle discs: backward-facing faces behind x_max within radius of a nozzle centre (y, z)."""
    hull.data.materials.append(mat)
    index = len(hull.data.materials) - 1
    count = 0
    for p in hull.data.polygons:
        c = p.center
        if c.x > spec["x_max"] or p.normal.x > spec.get("normal_x_max", -0.5):
            continue
        if any((c.y - n[0]) ** 2 + (c.z - n[1]) ** 2 <= spec["radius"] ** 2 for n in spec["centres_yz"]):
            p.material_index = index
            count += 1
    log("emissive: %d faces in %d nozzle discs" % (count, len(spec["centres_yz"])))


# --- 6: collision -----------------------------------------------------------------------------------

def kdop_hull(name, points):
    extremes = []
    for d in KDOP:
        best = max(points, key=lambda p: p.dot(d))
        if all((best - e).length > 1e-4 for e in extremes):
            extremes.append(best)
    bm = bmesh.new()
    for p in extremes:
        bm.verts.new(p)
    result = bmesh.ops.convex_hull(bm, input=bm.verts)
    for v in result.get("geom_interior", []):
        if isinstance(v, bmesh.types.BMVert):
            bm.verts.remove(v)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.display_type = "WIRE"
    return ob


def build_collision(ship, sources, regions):
    points = [o.matrix_world @ v.co for o in sources for v in o.data.vertices]
    made = []
    for i, region in enumerate(regions):
        inside = [p for p in points if in_box(p, region["box"])]
        if len(inside) < 4:
            raise SystemExit("collision region %s has only %d vertices" % (region["name"], len(inside)))
        ob = kdop_hull("UCX_SM_Ship_%s_%02d" % (ship, i), inside)
        made.append(ob)
        log("collision %s = %s: %d vertices from %d points" % (region["name"], ob.name, len(ob.data.vertices), len(inside)))
    return made


# --- 7: sockets ---------------------------------------------------------------------------------------

def build_sockets(ship, hull, parts, sockets):
    for name, spec in sockets.items():
        empty = bpy.data.objects.new("SOCKET_" + name, None)
        empty.empty_display_type = "ARROWS"
        empty.empty_display_size = 0.5
        bpy.context.scene.collection.objects.link(empty)
        if "bottom_of" in spec:
            part = parts[spec["bottom_of"]]
            pts = [part.matrix_world @ v.co for v in part.data.vertices if in_box(part.matrix_world @ v.co, spec["box"])]
            lo = min(p.z for p in pts)
            location = Vector((sum(p.x for p in pts) / len(pts), sum(p.y for p in pts) / len(pts), lo))
            if spec.get("centre_on_bounds", True):
                location.x = (min(p.x for p in pts) + max(p.x for p in pts)) * 0.5
                location.y = (min(p.y for p in pts) + max(p.y for p in pts)) * 0.5
        else:
            location = Vector(spec["location"])
        empty.parent = hull
        empty.matrix_world = Matrix.Translation(location) @ Matrix.Rotation(math.radians(spec.get("rotate_z_deg", 0.0)), 4, "Z")
        log("socket %s at (%.2f, %.2f, %.2f) m" % (empty.name, location.x, location.y, location.z))


# --- main ----------------------------------------------------------------------------------------------

def main(argv):
    config_path = path(argv[0])
    save = "--no-save" not in argv
    cfg = json.load(open(config_path, encoding="utf-8"))
    ship = cfg["ship"]
    started = time.time()
    hull = import_source(cfg, ship)
    # The source look goes on before anything is split or copied: the full-resolution copies carry
    # it into the bake.
    source_material = preview_material("SourceLook", cfg["textures"])
    hull.data.materials.clear()
    hull.data.materials.append(source_material)

    parts = {}
    for part, spec in (cfg.get("parts") or {}).items():
        ob = split_part(hull, ship, part, spec)
        if ob:
            parts[part] = ob
    lows = [hull] + list(parts.values())

    d = cfg["decimate"]
    highs = {ob.name: keep_high_copy(ob) for ob in lows}
    decimate(hull, d["hull_target_tris"], d.get("importance", []), d.get("default_importance", 0.5), d.get("protect_factor", 1.0))
    density_report(hull, d.get("importance", []), d.get("default_importance", 0.5))
    for part, ob in parts.items():
        decimate(ob, cfg["parts"][part].get("target_tris", 10000), [], 1.0, 0.0)
    for ob in lows:
        # Plain smooth normals, sharp above smooth_angle_deg, nothing custom: the baked normal map is
        # relative to exactly these, and Unreal gets the same from the FBX.
        select_only(ob)
        if ob.data.has_custom_normals:
            bpy.ops.mesh.customdata_custom_splitnormals_clear()
        ob.data.shade_smooth()
        ob.data.set_sharp_from_angle(angle=math.radians(d.get("smooth_angle_deg", 60.0)))

    bake = cfg["rebake"]
    unwrap(lows, bake.get("uv_margin", 0.002), bake.get("uv_angle_deg", 66.0))
    rebake([(ob, highs[ob.name]) for ob in lows], source_material, bake)
    for high in highs.values():
        bpy.data.objects.remove(high)

    material = preview_material("M_Ship_%s_Hull" % ship, {k: bake[k] for k in ("base_color", "orm", "normal")})
    for ob in lows:
        ob.data.materials.clear()
        ob.data.materials.append(material)
    if cfg.get("emissive"):
        assign_emissive(hull, cfg["emissive"], emissive_material(ship, cfg["emissive"].get("colour", (0.35, 0.65, 1.0))))

    build_collision(ship, lows, cfg.get("collision", []))
    build_sockets(ship, hull, parts, cfg.get("sockets", {}))
    lo, hi = bounds(lows)
    log("result: hull %d triangles, parts %s, size %s m, min z %.2f" % (
        tri_count(hull), {k: tri_count(v) for k, v in parts.items()}, tuple(round(c, 2) for c in hi - lo), lo.z))
    if save:
        bpy.ops.wm.save_as_mainfile(filepath=path(cfg["out_blend"]))
        log("saved %s" % cfg["out_blend"])
    log("done in %.0f s" % (time.time() - started))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[sys.argv.index("--") + 1:]))
