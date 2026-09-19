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
  8. interior (optional, "interior" in the config): a second AI export - the cockpit - imported into the
     same scene, oriented, scaled (width/length and height separately) and placed into the cabin,
     decimated, given its own UVs and re-baked textures, as the part SM_Ship_<Ship>_Interior with the
     slot M_Ship_<Ship>_Interior. It stays out of the collision and the sockets. Its placement comes
     from Tools/Blender/fit_ship_interior.py. Optional "displays": the AI's painted screens (generative
     textures cannot draw readable instruments) are cut out and replaced by flat quads with their own slot
     M_Ship_<Ship>_Screens, UV-mapped side by side across one texture (the first display the left part of
     it, and so on); the game draws its flight displays into that texture (UCockpitDisplayComponent);
  9. lining (optional, "lining"): the hull's faces inside region boxes, minus the canopy glass, copied with
     their normals turned inwards into the part SM_Ship_<Ship>_Lining (same material and UVs). The hull is
     one-sided, so from the cockpit the fuselage was invisible and the pilot looked through the floor and
     the sides at the ground; the lining is what the inside of the fuselage looks like, the glass stays
     clear. A part of its own, so the hull stays a clean outer shell (fit_ship_interior.py tests
     "inside" against it);
 10. canopy clean-up (optional, "canopy_clear"): hull faces inside the canopy that point into the cabin
     (the undersides of the frame between the panes) are deleted. Nobody sees them from outside - the
     panes are opaque - but from the seat the windscreen frame crossed the HUD;
 11. saves out_blend. The old source file is never touched.

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


def focus_uvs(ob, focus, margin):
    """More texels where the camera looks: UV islands facing focus["eye"] within focus["reach_m"] are
    scaled by focus["scale"] and the atlas repacked, so a cockpit's dashboard gets more of the texture
    than the undersides of its consoles."""
    from bpy_extras import bmesh_utils
    eye = Vector(focus["eye"])
    select_only(ob)
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    scaled = 0
    for island in bmesh_utils.bmesh_linked_uv_islands(bm, uv):
        seen = 0.0
        total = 0.0
        for f in island:
            c = f.calc_center_median()
            area = f.calc_area()
            total += area
            to_eye = eye - c
            if to_eye.length < focus.get("reach_m", 2.0) and f.normal.dot(to_eye.normalized()) > 0.2:
                seen += area
        if total > 0 and seen / total > 0.5:
            loops = [l for f in island for l in f.loops]
            centre = sum((l[uv].uv for l in loops), Vector((0.0, 0.0))) / len(loops)
            for l in loops:
                l[uv].uv = centre + (l[uv].uv - centre) * focus["scale"]
            scaled += 1
    bmesh.update_edit_mesh(ob.data)
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(rotate=True, margin=margin)
    bpy.ops.object.mode_set(mode="OBJECT")
    log("UV focus: %d islands facing the eye scaled x%.1f, atlas repacked" % (scaled, focus["scale"]))


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


def surface_nodes(nt, textures, surface):
    """Roughness, metallic and the emissive mask as node outputs, after the recipe's surface rules:
    roughness at least roughness_min, metallic at most metallic_max, and inside the "screens" rectangles
    (a frame: origin, axes u / v / w, rects [u0, u1, v0, v1], depth along w) the screen's own roughness
    and metallic, with the mask 1 there. The mask goes into the ORM's R channel; the game makes the
    base colour glow by it (M_Ship_PBR EmissiveStrength)."""
    def math(op, a, b):
        node = nt.nodes.new("ShaderNodeMath")
        node.operation = op
        for i, value in enumerate((a, b)):
            if isinstance(value, (int, float)):
                node.inputs[i].default_value = value
            else:
                nt.links.new(value, node.inputs[i])
        return node.outputs[0]

    rough = textures["roughness"].outputs[0]
    metal = textures["metallic"].outputs[0]
    if "roughness_min" in surface:
        rough = math("MAXIMUM", rough, surface["roughness_min"])
    if "metallic_max" in surface:
        metal = math("MINIMUM", metal, surface["metallic_max"])
    screens = surface.get("screens")
    if not screens:
        return rough, metal, 1.0
    position = nt.nodes.new("ShaderNodeNewGeometry").outputs["Position"]
    offset = nt.nodes.new("ShaderNodeVectorMath")
    offset.operation = "SUBTRACT"
    nt.links.new(position, offset.inputs[0])
    offset.inputs[1].default_value = screens["origin"]

    def along(axis):
        dot = nt.nodes.new("ShaderNodeVectorMath")
        dot.operation = "DOT_PRODUCT"
        nt.links.new(offset.outputs[0], dot.inputs[0])
        dot.inputs[1].default_value = Vector(axis).normalized()
        return dot.outputs["Value"]
    u, v, w = along(screens["u"]), along(screens["v"]), along(screens["w"])
    depth_ok = math("LESS_THAN", math("ABSOLUTE", w, 0.0), screens.get("depth", 0.03))
    mask = None
    for u0, u1, v0, v1 in screens["rects"]:
        inside = math("MULTIPLY", math("MULTIPLY", math("GREATER_THAN", u, u0), math("LESS_THAN", u, u1)),
                      math("MULTIPLY", math("GREATER_THAN", v, v0), math("LESS_THAN", v, v1)))
        mask = inside if mask is None else math("MAXIMUM", mask, inside)
    mask = math("MULTIPLY", mask, depth_ok)
    keep = math("SUBTRACT", 1.0, mask)
    rough = math("ADD", math("MULTIPLY", rough, keep), math("MULTIPLY", mask, screens.get("roughness", 0.3)))
    metal = math("ADD", math("MULTIPLY", metal, keep), math("MULTIPLY", mask, screens.get("metallic", 0.0)))
    return rough, metal, mask


def rebake(pairs, source_material, spec, surface=None):
    """Bakes the full-resolution model onto the decimated one's new UVs (Cycles, selected to active):
    base colour and ORM through an emission shader (exact texture values, no lighting), and a
    tangent-space normal map of the source's shading, so 200k triangles shade like 3.4 million.
    surface: optional rules for roughness / metallic and emissive screens (surface_nodes)."""
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
    rough, metal, glow = surface_nodes(nt, textures, surface or {})
    # R: emissive mask (1 on the whole hull, where the game leaves EmissiveStrength at 0), G roughness, B metallic
    if isinstance(glow, float):
        combine.inputs[0].default_value = glow
    else:
        nt.links.new(glow, combine.inputs[0])
    nt.links.new(rough, combine.inputs[1])
    nt.links.new(metal, combine.inputs[2])

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


# --- 8: interior -----------------------------------------------------------------------------------------

def add_interior(ship, spec):
    """The cockpit interior as its own part: see step 8 in the module notes."""
    t = time.time()
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path(spec["source_fbx"]))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    for o in new:
        if o.type != "MESH":
            bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.parent = None
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    tris = tri_count(ob)
    place = spec["placement"]
    s, r = place["scale"], place.get("height_ratio", 1.0)
    placement = Matrix.Translation(Vector(place["offset"])) @ Matrix.Diagonal((s, s, s * r, 1.0))
    matrix = placement @ Matrix.Rotation(math.radians(spec.get("rotate_z_deg", 0.0)), 4, "Z")
    ob.data.transform(matrix)
    ob.data.update()
    ob.name = ob.data.name = "SM_Ship_%s_Interior" % ship
    lo, hi = bounds([ob])
    log("interior %s: %d triangles, placed at scale %.2f (height x%.2f): min %s max %s" % (
        os.path.basename(spec["source_fbx"]), tris, s, r, tuple(round(c, 2) for c in lo), tuple(round(c, 2) for c in hi)))

    source = preview_material("InteriorSourceLook", spec["textures"])
    ob.data.materials.clear()
    ob.data.materials.append(source)
    high = keep_high_copy(ob)
    decimate(ob, spec.get("target_tris", 120000), [], 1.0, 0.0)
    select_only(ob)
    if ob.data.has_custom_normals:
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
    ob.data.shade_smooth()
    ob.data.set_sharp_from_angle(angle=math.radians(spec.get("smooth_angle_deg", 60.0)))
    bake = spec["rebake"]
    unwrap([ob], bake.get("uv_margin", 0.002), bake.get("uv_angle_deg", 66.0))
    if spec.get("uv_focus"):
        focus_uvs(ob, spec["uv_focus"], bake.get("uv_margin", 0.002))
    rebake([(ob, high)], source, bake, spec.get("surface"))
    bpy.data.objects.remove(high)
    ob.data.materials.clear()
    ob.data.materials.append(preview_material("M_Ship_%s_Interior" % ship, {k: bake[k] for k in ("base_color", "orm", "normal")}))
    if spec.get("displays"):
        add_displays(ob, ship, spec["displays"], placement)
    log("interior done: %d triangles in %.0f s" % (tri_count(ob), time.time() - t))
    return ob


def add_displays(ob, ship, spec, matrix):
    """Flat screens instead of the AI's painted ones: see step 8 in the module notes. Each display is a
    rectangle in the interior's own frame (rotated, before scale and placement: centre, u = the screen's
    right, v = its up, rect [u0, u1, v0, v1] in metres), measured once in the source model. Faces of the
    interior behind it (centre inside the rectangle shrunk by cut_inset_m, within cut_depth_m of the plane)
    are deleted, and a quad is put on the plane, offset_m towards the pilot. The quads share one slot and
    one texture: display i of n gets the i-th n-th of it, left to right."""
    screens = spec["screens"]

    def inside_quad(a, b, quad):
        # Convex quad TL TR BR BL (clockwise on screen): inside when on the same side of every edge.
        signs = []
        for k in range(4):
            (x0, y0), (x1, y1) = quad[k], quad[(k + 1) % 4]
            signs.append((x1 - x0) * (b - y0) - (y1 - y0) * (a - x0))
        return all(s <= 0 for s in signs) or all(s >= 0 for s in signs)
    inset, depth, offset = spec.get("cut_inset_m", 0.012), spec.get("cut_depth_m", 0.02), spec.get("offset_m", 0.002)
    local = matrix.inverted()
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    uv = bm.loops.layers.uv.active
    ob.data.materials.append(bpy.data.materials.get("M_Ship_%s_Screens" % ship) or screen_material("M_Ship_%s_Screens" % ship))
    slot = len(ob.data.materials) - 1
    for i, screen in enumerate(screens):
        c, u, v = Vector(screen["centre"]), Vector(screen["u"]).normalized(), Vector(screen["v"]).normalized()
        n = u.cross(v).normalized()
        # The screen's outline: "corners" (top-left, top-right, bottom-right, bottom-left, as the bezel
        # opening really is - not a rectangle), or a "rect" [u0, u1, v0, v1].
        if "corners" in screen:
            tl, tr, br, bl = [tuple(p) for p in screen["corners"]]
        else:
            u0, u1, v0, v1 = screen["rect"]
            tl, tr, br, bl = (u0, v1), (u1, v1), (u1, v0), (u0, v0)
        quad = [tl, tr, br, bl]
        doomed = []
        for f in bm.faces:
            d = local @ f.calc_center_median() - c
            a, b = d.dot(u), d.dot(v)
            if inside_quad(a, b, quad) and abs(d.dot(n)) < depth:
                doomed.append(f)
        bmesh.ops.delete(bm, geom=doomed, context="FACES")
        corners = [bl, br, tr, tl]
        texture_corners = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        verts = [bm.verts.new(matrix @ (c + u * a + v * b + n * offset)) for a, b in corners]
        face = bm.faces.new(verts)
        face.material_index = slot
        face.smooth = False
        # Blender's UV origin is bottom-left; the importer flips V, so the top of the screen lands on
        # the top row of the texture. The whole texture share goes onto the quad, whatever its shape.
        for loop, (x, y) in zip(face.loops, texture_corners):
            loop[uv].uv = ((i + x) / len(screens), y)
        face.normal_update()
        pilot = matrix @ (c + n) - matrix @ c
        if face.normal.dot(pilot) < 0:
            face.normal_flip()
        # A socket just in front of the screen: the game hangs the display's glow (a rect light) on it.
        socket = bpy.data.objects.new("SOCKET_Display_%s" % screen.get("name", i), None)
        socket.empty_display_type = "ARROWS"
        socket.empty_display_size = 0.1
        bpy.context.scene.collection.objects.link(socket)
        socket.parent = ob
        socket.matrix_world = Matrix.Translation(matrix @ (c + n * spec.get("light_offset_m", 0.03)))
        log("display %s: %d faces of the AI screen cut, quad %.0f x %.0f cm (before scaling)" % (
            screen.get("name", i), len(doomed), (tr[0] - tl[0]) * 100, (tl[1] - bl[1]) * 100))
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def screen_material(name):
    """Blender stand-in for the game's screen: dark glass with a faint glow."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.01, 0.015, 0.02, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.35
    bsdf.inputs["Emission Color"].default_value = (0.1, 0.35, 0.3, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 1.0
    return mat


# --- 9: lining -----------------------------------------------------------------------------------------

def clear_canopy(hull, spec):
    """See step 10 in the module notes."""
    box, axis_z, min_dot = spec["box"], spec.get("axis_z", 1.2), spec.get("min_dot", 0.2)
    bm = bmesh.new()
    bm.from_mesh(hull.data)
    doomed = []
    for f in bm.faces:
        c = f.calc_center_median()
        if not in_box(c, box):
            continue
        towards = Vector((0.0, -c.y, axis_z - c.z))
        if towards.length > 1e-6 and f.normal.dot(towards.normalized()) > min_dot:
            doomed.append(f)
    bmesh.ops.delete(bm, geom=doomed, context="FACES")
    bm.to_mesh(hull.data)
    bm.free()
    hull.data.update()
    log("canopy clean-up: %d inward faces inside the canopy deleted" % len(doomed))


def frame_canopy(hull, ship, spec, eye):
    """The inside of the canopy frame gets its own slot M_Ship_<Ship>_CanopyFrame: hull faces inside the
    box that the pilot's eye sees from the front (from outside they face away and are culled). With the
    hull's paint they caught the sun and read as bright wires across the view; a real frame is dark
    from inside."""
    name = "M_Ship_%s_CanopyFrame" % ship
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (0.02, 0.022, 0.025, 1.0)
    hull.data.materials.append(mat)
    slot = len(hull.data.materials) - 1
    count = 0
    for f in hull.data.polygons:
        c = hull.matrix_world @ f.center
        n = (hull.matrix_world.to_3x3() @ f.normal).normalized()
        if in_box(c, spec["box"]) and n.dot((eye - c).normalized()) > spec.get("min_dot", 0.0):
            f.material_index = slot
            count += 1
    log("canopy frame: %d faces seen from the eye get %s" % (count, name))


def add_lining(hull, ship, spec):
    """See step 9 in the module notes: a part with the hull's material slots and UVs."""
    regions, exclude = spec["regions"], spec.get("exclude", [])
    bm = bmesh.new()
    bm.from_mesh(hull.data)

    def any_box(v, boxes):
        return any(in_box(v.co, b) for b in boxes)
    keep = {f for f in bm.faces if all(any_box(v, regions) for v in f.verts) and not all(any_box(v, exclude) for v in f.verts)}
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f not in keep], context="FACES")
    bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    mesh = hull.data.copy()
    mesh.name = "SM_Ship_%s_Lining" % ship
    bm.to_mesh(mesh)
    bm.free()
    lining = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.scene.collection.objects.link(lining)
    lining.matrix_world = hull.matrix_world.copy()
    # Only the slots its faces use (the nozzle discs are outside it): the manifest lists the object's
    # slots, the FBX only the used ones, and the import checks that they agree.
    select_only(lining)
    bpy.ops.object.material_slot_remove_unused()
    log("lining: %s, %d triangles facing inwards" % (lining.name, tri_count(lining)))
    return lining


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

    if cfg.get("canopy_clear"):
        clear_canopy(hull, cfg["canopy_clear"])
    if cfg.get("canopy_frame"):
        frame_canopy(hull, ship, cfg["canopy_frame"], Vector(cfg["sockets"]["Cockpit"]["location"]))
    if cfg.get("lining"):
        add_lining(hull, ship, cfg["lining"])
    build_collision(ship, lows, cfg.get("collision", []))
    build_sockets(ship, hull, parts, cfg.get("sockets", {}))
    if cfg.get("interior"):
        add_interior(ship, cfg["interior"])
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
