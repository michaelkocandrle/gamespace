"""Geometry check of a finished ship (the game blend after hs_assemble_ship.py), run before every hand-over.

    blender -b ArtSource/Ships/<Ship>/<Ship>_HS_Game.blend --python Tools/Blender/check_ship_geometry.py -- <Ship> [out_dir]

Prints GEOCHECK {...} (and writes <out_dir>/geocheck.json and the hole masks). A check fails with a list of what to fix:
  mirrored_decals     mesh-decal faces whose texture reads mirrored from their front ((T x B) . N < 0), and projected
                      interior decals (<Ship>_setup.json "Int_*") whose box reaches a surface behind the marked one -
                      the marking then shows mirrored on the wall's other side
  floating            interior parts (connected pieces) that touch nothing within TOL_TOUCH; lights and holograms
                      are exempt by material, known intentional ones by name in the recipe (checks.floating_exempt)
  penetrating         cockpit parts reaching behind the frame lining or outside the hull by more than TOL_PEN
  hull_in_rooms       exterior geometry (hull, canopy, gear: a wing root, a spar, a pod) inside a room's clear space -
                      between its walls, deck to ceiling (the kit rooms: between the W panels); the cockpit excepted
  placeholders        slots without a material or with Blender's default; large plain faces are listed (warning)
  holes               ship-less pixels (the world) seen from the player's positions with every surface opaque -
                      the eye and the interior shot cameras of Tools/Shots/<ship>_interior.json
  walk_blocked        where the walker (the character's capsule inside a ship, WALK_R x WALK_H - PlayerCharacter
                      ShipCapsuleRadius / 2 * ShipCapsuleHalfHeight) cannot pass a doorway of the layout, stepping
                      over whatever floor, steps or stairs lie there; doors built closed are named in the recipe
                      (checks.walk_exempt)
The kit rooms' parts (recipe interior.kit_modules, placed in Unreal by Tools/Assets/kit_rooms.py) are put into the
ship first (add_kit_rooms), so the checks see them as the game does.
Meaning of pass: every list empty (warnings do not fail).
"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp"))
from mcp_eye_view import eye_of  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
TOL_TOUCH = 0.006
TOL_PEN = 0.005
EXEMPT_FLOAT_MATS = ("IntGlow", "IntLight", "_Screens", "KitCables")   # emissive strips, holograms, screen quads, the
                                                                       # kit's cable meshes (loose inside their trays)
FLAT_MATS = ("IntWall", "IntPanel", "IntDark", "IntFloor", "IntConsole")
BIG_FACE_M2 = 0.4
AXIS_Z = 0.45          # ship space: the pilot's eye height (the cabin's middle)
WALK_R = 0.25          # the walker inside a ship (PlayerCharacter ShipCapsuleRadius, ShipCapsuleHalfHeight 0.90)
WALK_H = 1.80
WALK_STEP = 0.45       # Character Movement's MaxStepHeight
WALK_HOVER = 0.024     # it floats this much over the floor (MAX_FLOOR_DIST)


def obj(ship, suffix):
    return bpy.data.objects.get("SM_Ship_%s%s" % (ship, suffix))


def world_bm(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.transform(ob.matrix_world)
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    return bm


# ------------------------------------------------------------------------------------------ decals

def mirrored_mesh_decals(ship):
    bad = []
    for suffix in ("_Decals", "_InteriorDecals"):
        ob = obj(ship, suffix)
        if ob is None:
            continue
        bm = world_bm(ob)
        uv = bm.loops.layers.uv.active
        mats = [m.name if m else "" for m in ob.data.materials]
        for f in bm.faces:
            if len(f.loops) < 3:
                continue
            if "Trim" in mats[f.material_index]:
                continue          # trim-sheet ribbons: symmetric strips (bolts, grooves), no text to mirror
            l0, l1, l2 = f.loops[0], f.loops[1], f.loops[2]
            p0, p1, p2 = l0.vert.co, l1.vert.co, l2.vert.co
            u0, u1, u2 = l0[uv].uv, l1[uv].uv, l2[uv].uv
            e1, e2 = p1 - p0, p2 - p0
            d1, d2 = u1 - u0, u2 - u0
            det = d1.x * d2.y - d2.x * d1.y
            if abs(det) < 1e-12:
                continue
            t = (e1 * d2.y - e2 * d1.y) / det
            b = (e2 * d1.x - e1 * d2.x) / det
            if t.cross(b).dot(f.normal) < 0:
                bad.append({"object": ob.name, "at": [round(v, 2) for v in f.calc_center_median()]})
        bm.free()
    return bad


def mirrored_projected(ship, tree):
    setup = json.load(open(os.path.join(ROOT, "ArtSource", "Ships", ship, "%s_setup.json" % ship), encoding="utf-8"))
    recipe = json.load(open(os.path.join(ROOT, "ArtSource", "Ships", ship, "HardSurface", "%s_hs.json" % ship), encoding="utf-8"))
    sys.path.insert(0, os.path.join(ROOT, "Tools", "Kit"))
    import kit_layout
    bad = []
    for d in setup.get("decals", []):
        if not d["name"].startswith("Int_") or not kit_layout.decal_active(d, recipe):
            continue
        loc = Vector((d["location"][0] / 100, -d["location"][1] / 100, d["location"][2] / 100))
        pitch, yaw = math.radians(d["rotation"][0]), math.radians(d["rotation"][1])
        x_ue = Vector((math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch)))
        # rounded: a component like cos(90 deg) = 6e-17 makes BVHTree.ray_cast miss everything
        x = Vector((round(x_ue.x, 6) + 0.0, round(-x_ue.y, 6) + 0.0, round(x_ue.z, 6) + 0.0)).normalized()
        half = min(d["size"][0], float(d.get("max_depth_cm", 4.0))) / 100.0     # the import caps interior depth
        # it projects along -X onto the surface it marks (facing +X). Mirrored text appears when the box also
        # reaches, further along -X, a surface facing -X: the other side of the wall
        hit, nrm, idx, dist = tree.ray_cast(loc, -x, half)
        if hit is None:
            bad.append({"decal": d["name"], "note": "marks nothing within its depth"})
            continue
        travelled = first = dist
        p = hit - x * 0.0005
        while travelled < half:
            h2, n2, i2, d2 = tree.ray_cast(p, -x, half - travelled)
            if h2 is None:
                break
            travelled += d2
            # a back face within 8 mm of the marked surface is a detail set into it (the kit floor's anti-slip lanes
            # sit 1 mm into the plate, 30. 9. 2026), never a wall's other side
            if n2.dot(x) < 0 and travelled - first > 0.008:
                bad.append({"decal": d["name"], "note": "box reaches the wall's other side: reads mirrored there"})
                break
            p = h2 - x * 0.0005
    return bad


# ------------------------------------------------------------------------------------------ parts

def islands(bm):
    """Connected pieces of a bmesh as lists of face indices."""
    seen = set()
    out = []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, part = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop()
            part.append(g.index)
            for v in g.verts:
                for h in v.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        out.append(part)
    return out


def add_kit_rooms(ship, recipe):
    """The kit rooms' parts (recipe interior.kit_modules) as one mesh SM_Ship_<Ship>_InteriorKitMod, placed as
    Tools/Assets/kit_rooms.py places them in Unreal (Tools/Kit/kit_layout.py): the blend has only the bulkheads
    there, so without them every view into a kit room was a hole. The holes, the floating parts and the hull are
    then checked with the real parts. Never saved (this process does not write the blend)."""
    mods = (recipe.get("interior") or {}).get("kit_modules")
    sys.path.insert(0, os.path.join(ROOT, "Tools", "Kit"))
    import kit_layout
    if not mods or not kit_layout.active_rooms(recipe):
        return None
    placed = kit_layout.layout_parts(mods, kit_layout.manifest_parts())
    want = {"SM_Kit_" + m for m, _, _ in placed}
    src = {}
    for path in kit_layout.kit_blends():
        with bpy.data.libraries.load(path, link=False) as (data_from, data_to):
            names = [n for n in data_from.objects if n in want and n not in src]
            data_to.objects = list(names)       # (a copy: the load swaps the list's names for the objects)
        for n, ob in zip(names, data_to.objects):      # (loaded in the order asked for)
            if ob is not None:
                src[n] = ob
    missing = sorted(want - set(src))
    if missing:
        raise RuntimeError("kit parts not in ArtSource/Kit/*.blend: %s" % missing)
    tmp_coll = bpy.data.collections.new("_kit_parts")
    bpy.context.scene.collection.children.link(tmp_coll)
    for ob in src.values():
        tmp_coll.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    off = recipe["assemble"]["offset"]
    combined, mat_names = bmesh.new(), []
    for m, (x, y_ue, z), yaw in placed:
        ob = src["SM_Kit_" + m]
        ev = ob.evaluated_get(dg)
        tmp = bmesh.new()
        tmp.from_mesh(ev.to_mesh())
        # Unreal (y mirrored, yaw about +Z) -> the game blend: y back to Blender's sense, the turn the other way
        tmp.transform(Matrix.Translation((x + off[0], -y_ue + off[1], z + off[2])) @ Matrix.Rotation(math.radians(-yaw), 4, "Z"))
        remap = []
        for mt in ob.data.materials:
            n = mt.name if mt else ""
            if n not in mat_names:
                mat_names.append(n)
            remap.append(mat_names.index(n))
        for f in tmp.faces:
            f.material_index = remap[f.material_index] if f.material_index < len(remap) else 0
        me = bpy.data.meshes.new("_kit_tmp")
        tmp.to_mesh(me)
        tmp.free()
        ev.to_mesh_clear()
        combined.from_mesh(me)
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new("SM_Ship_%s_InteriorKitMod" % ship)
    combined.to_mesh(me)
    combined.free()
    for n in mat_names:
        me.materials.append(bpy.data.materials.get(n))
    kob = bpy.data.objects.new(me.name, me)
    bpy.context.scene.collection.objects.link(kob)
    for ob in list(src.values()):
        bpy.data.objects.remove(ob)
    bpy.data.collections.remove(tmp_coll)
    return {"parts": len(placed), "faces": len(me.polygons)}


def hull_in_rooms(ship, recipe):
    """Exterior geometry inside the rooms' clear space (the author's question, 28. 9. 2026): 'penetrating' only
    catches interior parts reaching out through the hull, not a wing root, spar or pod reaching into a room. Every
    room of the layout but the cockpit (its own lining and canopy frame) gets a clear box - between its walls
    (wall_inset_m, 5 cm in from them), deck to ceiling; a kit room the W corridor between the wall panels - and the
    exterior parts (hull, canopy, gear) must not overlap it. Only the rooms' length along x is taken whole."""
    layout = json.load(open(os.path.join(ROOT, "ArtSource", "Ships", ship, "Design", "%s_layout.json" % ship), encoding="utf-8"))
    spec = recipe.get("interior") or {}
    H, inset = spec.get("height_m", 2.3), spec.get("wall_inset_m", 0.05)
    sys.path.insert(0, os.path.join(ROOT, "Tools", "Kit"))
    import kit_layout
    mods = kit_layout.active_rooms(recipe)
    off = recipe["assemble"]["offset"]
    ext = bmesh.new()
    for suffix in ("", "_Canopy", "_Gear"):
        ob = obj(ship, suffix)
        if ob is None:
            continue
        me = bpy.data.meshes.new("_ext")
        tb = world_bm(ob)
        tb.to_mesh(me)
        tb.free()
        ext.from_mesh(me)
        bpy.data.meshes.remove(me)
    ext.faces.ensure_lookup_table()
    ext_tree = BVHTree.FromBMesh(ext)
    out = []
    m = 0.05
    for room in layout["rooms"]:
        if room["id"] == "cockpit":
            continue
        x0, x1, y0, y1 = room["rect"]
        fz = room.get("floor_z", layout["decks"][room.get("deck", "main")]["floor_z"])
        widths = (spec.get("kit_modules") or {}).get("width") or {}
        boxes = []
        if room["id"] in mods and room["id"] in widths:
            # a hull liner (section L): face to face up to the chamfer's foot, the chamfer's top line above it
            hw = widths[room["id"]] / 2
            sec = json.load(open(os.path.join(ROOT, "ArtSource", "Kit", "kit_rules.json"), encoding="utf-8"))["sections"]["L"]
            vt, xt = sec["vertical_to"], 0.75 * sec["slope_rise"]
            boxes = [(-hw, hw, 0.0, vt), (-hw + xt, hw - xt, vt, H)]
        elif room["id"] in mods:
            boxes = [(-1.2, 1.2, 0.0, H)]            # the W section's panel faces
        else:
            boxes = [(y0 + inset, y1 - inset, 0.0, H)]
        for (y0, y1, za, zb) in boxes:
            _box_check(out, room, ext, ext_tree, off, x0, x1, y0, y1, fz + za, fz + zb, m)
    ext.free()
    return out


def _box_check(out, room, ext, ext_tree, off, x0, x1, y0, y1, z0, z1, m):
    """hull_in_rooms for one clear box of a room (layout metres)."""
    lo = Vector((x0 + m + off[0], y0 + m + off[1], z0 + m + off[2]))
    hi = Vector((x1 - m + off[0], y1 - m + off[1], z1 - m + off[2]))
    box = bmesh.new()
    res = bmesh.ops.create_cube(box, size=1.0)
    bmesh.ops.scale(box, vec=hi - lo, verts=res["verts"])
    bmesh.ops.translate(box, vec=(lo + hi) / 2, verts=res["verts"])
    box_tree = BVHTree.FromBMesh(box)
    box.free()
    hits = ext_tree.overlap(box_tree)
    # faces wholly inside the box do not intersect its skin: test the exterior's vertices too
    inside = [v.co for v in ext.verts if lo.x < v.co.x < hi.x and lo.y < v.co.y < hi.y and lo.z < v.co.z < hi.z]
    if hits or inside:
        pts = [ext.faces[a].calc_center_median() for a, b in hits[:1]] or inside[:1]
        p = pts[0]
        out.append({"room": room["id"], "faces": len({a for a, b in hits}), "verts_inside": len(inside),
                    "at_layout": [round(p.x - off[0], 2), round(p.y - off[1], 2), round(p.z - off[2], 2)]})


def floating_and_penetrating(ship, exempt_names):
    parts = [o for o in (obj(ship, "_Interior"), obj(ship, "_InteriorKit"), obj(ship, "_InteriorKitMod")) if o is not None]
    hull = obj(ship, "")
    all_bm = bmesh.new()
    owner = []                    # per face of all_bm: (object index, island id) or ("hull", -1)
    per_obj = []
    for k, ob in enumerate(parts):
        bm = world_bm(ob)
        isl = islands(bm)
        fid = {}
        for i, part in enumerate(isl):
            for fi in part:
                fid[fi] = i
        per_obj.append((ob, bm, isl))
        me = bpy.data.meshes.new("_chk")
        bm.to_mesh(me)
        n0 = len(all_bm.faces)
        all_bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        owner += [(k, fid[i]) for i in range(len(bm.faces))]
    for ob in (hull, obj(ship, "_Canopy"), obj(ship, "_Screens"), obj(ship, "_Gear")):
        if ob is None:
            continue
        hb = world_bm(ob)
        me = bpy.data.meshes.new("_chk")
        hb.to_mesh(me)
        all_bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        owner += [("other", -1)] * len(hb.faces)
        hb.free()
    all_bm.faces.ensure_lookup_table()
    tree = BVHTree.FromBMesh(all_bm)
    hull_tree = BVHTree.FromBMesh(world_bm(hull)) if hull else None
    # the frame lining (slot IntFrame of the interior): parts reaching behind it pierce the cockpit's wall
    liner_tree = None
    if per_obj:
        ob0, bm0, _ = per_obj[0]
        mats0 = [m.name if m else "" for m in ob0.data.materials]
        lb = bm0.copy()
        bmesh.ops.delete(lb, geom=[f for f in lb.faces if not (mats0 and "IntFrame" in mats0[f.material_index])], context="FACES")
        if lb.faces:
            liner_tree = BVHTree.FromBMesh(lb)
        lb.free()
    floating, penetrating = [], []
    for k, (ob, bm, isl) in enumerate(per_obj):
        mats = [m.name if m else "" for m in ob.data.materials]
        liner_faces = {i for i, f in enumerate(bm.faces) if mats and "IntFrame" in mats[f.material_index]}
        for i, part in enumerate(isl):
            f0 = bm.faces[part[0]]
            mat = mats[f0.material_index] if mats else ""
            if any(e in mat for e in EXEMPT_FLOAT_MATS):
                continue
            verts = {v for fi in part for v in bm.faces[fi].verts}
            centre = sum((v.co for v in verts), Vector()) / len(verts)
            if any(n in ob.name or n in mat for n in exempt_names):
                continue
            sample = list(verts)[:: max(1, len(verts) // 16)]
            touching = False
            for v in sample:
                for loc, nrm, idx, dist in tree.find_nearest_range(v.co, TOL_TOUCH):
                    if owner[idx] != (k, i):
                        touching = True
                        break
                if touching:
                    break
            if not touching:
                # parts sunk into others (a shaft in a boot, rings on a core, tiles in a slab) share no nearby
                # vertices: test the piece's faces for overlap with the rest
                pbm = bmesh.new()
                vmap = {}
                for fi in part:
                    fv = []
                    for v in bm.faces[fi].verts:
                        if v.index not in vmap:
                            vmap[v.index] = pbm.verts.new(v.co)
                        fv.append(vmap[v.index])
                    try:
                        pbm.faces.new(fv)
                    except ValueError:
                        pass
                ptree = BVHTree.FromBMesh(pbm)
                pbm.free()
                touching = any(owner[b] != (k, i) for a, b in ptree.overlap(tree))
            if not touching:
                floating.append({"object": ob.name, "material": mat, "at": [round(c, 2) for c in centre], "faces": len(part)})
            # penetration: cockpit parts behind the frame lining or outside the hull (lining itself excluded)
            if part[0] in liner_faces or "IntDark" in mat:
                continue
            if liner_tree is not None:
                # parts mounted on the lining (rims, seams, pinstripes) follow its curve: not a penetration
                near = sum(1 for v in sample if (lambda r: r[0] is not None and r[3] < 0.04)(liner_tree.find_nearest(v.co)))
                if near >= 0.8 * len(sample):
                    continue
            if hull_tree is None:
                continue
            worst = 0.0
            for v in sample:
                # towards the cabin's centre line at the eye's height (the same height fails under a roof:
                # that point is outside the hull)
                axis = Vector((v.co.x, 0.0, AXIS_Z))
                d = axis - v.co
                if d.length < 0.05:
                    continue
                dn = d.normalized()
                # behind the lining: the first lining face on the way to the cabin's axis is met from its back
                # (lining normals face the cabin); outside the hull: the first hull face is met from its front
                # (hull normals face out). Crossing a frame bar on the way in is met from the front - not counted.
                if liner_tree is not None:
                    hit, nrm, idx, dist = liner_tree.ray_cast(v.co, dn, min(d.length, 1.2))
                    if hit is not None and nrm.dot(dn) > 0:
                        worst = max(worst, dist)
                hit, nrm, idx, dist = hull_tree.ray_cast(v.co, dn, min(d.length, 1.2))
                if hit is not None and nrm.dot(dn) < 0:
                    worst = max(worst, dist)
            if worst > TOL_PEN:
                penetrating.append({"object": ob.name, "material": mat, "at": [round(c, 2) for c in centre], "depth_m": round(worst, 3)})
    for ob, bm, isl in per_obj:
        bm.free()
    return floating, penetrating, tree


# ------------------------------------------------------------------------------------------ walking

def walk_blocked(ship, recipe):
    """The walker through every doorway of the layout (author 29. 9. 2026: a ship you can walk through). A sliver of
    the cockpit floor's edge hanging across the doorway and a wall over the stairs, 2 cm too low for the head, both
    stopped the character in the game while every other check passed. From 0.8 m before a door to 0.8 m past it,
    along the door's axis at its centre and 12 cm to each side (blocked at the centre fails; only to a side it is
    a tight passage, a warning - the walker scrapes along it): the capsule rests on the highest floor under its
    footprint within a step's height (rays down, as Character Movement stands on step edges), and then must not
    come nearer than its radius to anything with its body - bottom sphere lifted clear of the edges it stands on,
    up to the top of the head. Interior parts only: in the game they alone block the walker (the hull does not)."""
    layout = json.load(open(os.path.join(ROOT, "ArtSource", "Ships", ship, "Design", "%s_layout.json" % ship), encoding="utf-8"))
    off = Vector(recipe["assemble"]["offset"])
    parts = [o for o in (obj(ship, "_Interior"), obj(ship, "_InteriorKit"), obj(ship, "_InteriorKitMod")) if o is not None]
    all_bm = bmesh.new()
    for ob in parts:
        bm = world_bm(ob)
        me = bpy.data.meshes.new("_walk")
        bm.to_mesh(me)
        all_bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        bm.free()
    tree = BVHTree.FromBMesh(all_bm)
    all_bm.free()
    exempt = recipe.get("checks", {}).get("walk_exempt", [])
    out, tight = [], []
    for door in layout["doors"]:
        ax = door["axis"]
        at = door["at"]
        if door.get("name") in exempt:
            continue                                   # built closed (the ramp, a sliding leaf): recipe checks.walk_exempt
        fz = layout["decks"][door.get("deck", "main")]["floor_z"]
        for side in (0.0, -0.12, 0.12):
            feet = fz
            worst = None
            steps = 54                                 # 3 cm (9. 10. 2026: at 5 cm the head in a doorway's head slipped between samples)
            for i in range(steps):
                t = -0.8 + 1.6 * i / (steps - 1)
                c = Vector((at[0] + t, at[1] + side, 0.0)) if ax == "x" else Vector((at[0] + side, at[1] + t, 0.0))
                # the floor under the footprint, within a step up
                rest = None
                for k in range(-6, 7):
                    d = WALK_R * k / 6.0
                    for e in ((d, 0.0), (0.0, d)):
                        o = Vector((c.x + e[0], c.y + e[1], feet + WALK_STEP + 0.01)) + off
                        hit = tree.ray_cast(o, Vector((0.0, 0.0, -1.0)), WALK_STEP + 1.0)
                        if hit[0] is None:
                            continue
                        z = hit[0].z - off.z + math.sqrt(max(WALK_R ** 2 - e[0] ** 2 - e[1] ** 2, 0.0)) - WALK_R
                        rest = z if rest is None else max(rest, z)
                if rest is None:
                    continue                          # no floor within a step: a drop, the walker falls to it
                feet = rest + WALK_HOVER
                # the body from just over the bottom sphere to the top of the head
                z = feet + WALK_R + 0.05
                while z <= feet + WALK_H - WALK_R + 1e-6:
                    near = tree.find_nearest(Vector((c.x, c.y, z)) + off, WALK_R)
                    if near[0] is not None and (near[0] - off).z <= feet + WALK_STEP:
                        near = (None, None, None, None)     # a step's edge within MaxStepHeight: Character Movement steps onto it
                    if near[0] is not None and near[3] < WALK_R + 0.01:          # 1 cm of clearance: none stopped the game's walker
                        gap = WALK_R + 0.01 - near[3]
                        if worst is None or gap > worst["overlap_m"]:
                            q = near[0] - off
                            worst = {"door": door.get("name", ""), "walker_at": [round(c.x, 2), round(c.y, 2), round(feet, 2)],
                                     "obstacle_at": [round(q.x, 3), round(q.y, 3), round(q.z, 3)], "overlap_m": round(gap, 3)}
                    z += 0.05
            if worst:
                worst["offset_m"] = side
                if side == 0.0:
                    out.append(worst)
                    tight = [t for t in tight if t["door"] != worst["door"]]
                    break
                if not any(t["door"] == worst["door"] for t in tight):
                    tight.append(worst)
    return out, tight


# ------------------------------------------------------------------------------------------ materials and holes

def placeholders(ship):
    bad, warn = [], []
    for ob in bpy.data.objects:
        if ob.type != "MESH" or not ob.name.startswith("SM_Ship_%s" % ship):
            continue
        mats = list(ob.data.materials)
        for i, m in enumerate(mats):
            if m is None or m.name.startswith("Material") or m.name == "WorldGridMaterial":
                bad.append({"object": ob.name, "slot": i, "material": m.name if m else None})
        if "_Interior" in ob.name:
            areas = {}
            for p in ob.data.polygons:
                name = mats[p.material_index].name if mats and mats[p.material_index] else ""
                if any(f in name for f in FLAT_MATS) and p.area > BIG_FACE_M2:
                    areas[name] = areas.get(name, 0) + 1
            for name, n in areas.items():
                warn.append({"object": ob.name, "material": name, "large_plain_faces": n})
    return bad, warn


def holes(ship, out_dir):
    """Render opaque masks from the player's positions: any world pixel is a hole."""
    sc = bpy.context.scene
    eye, fov, pitch = eye_of(ship)
    views = [("eye", Vector(eye), Euler((math.radians(90 + pitch), 0, math.radians(-90))), fov)]
    preset = os.path.join(ROOT, "Tools", "Shots", "%s_interior.json" % ship.lower())
    if os.path.isfile(preset):
        for s in json.load(open(preset, encoding="utf-8"))["shots"]:
            if "camera_local" in s and s["name"] not in ("canopy_outside",):   # views from outside the ship
                c = Vector((s["camera_local"][0], -s["camera_local"][1], s["camera_local"][2]))
                l = Vector((s["look_local"][0], -s["look_local"][1], s["look_local"][2]))
                views.append((s["name"], c, (l - c).to_track_quat("-Z", "Y").to_euler(), s.get("fov", 90)))
    cam = bpy.data.objects.new("GeoCheckCam", bpy.data.cameras.new("GeoCheckCam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.clip_start = 0.02
    for o in bpy.data.objects:
        if o.type == "EMPTY" or o.name.startswith(("UCX_", "SOCKET_")):
            o.hide_render = True
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.render.resolution_x, sc.render.resolution_y = 960, 540
    sh = sc.display.shading
    sh.light, sh.color_type, sh.single_color = "FLAT", "SINGLE", (0.0, 0.0, 0.0)
    sh.show_backface_culling = True
    sh.show_cavity = sh.show_shadows = False
    sh.background_type = "WORLD"
    w = sc.world or bpy.data.worlds.new("chk")
    sc.world = w
    w.color = (1.0, 1.0, 1.0)
    sc.view_settings.view_transform = "Standard"
    out = []
    # the canopy glass is two-sided in the game; for the mask it must stop the view from inside too
    # every glass face (the canopy object and Glass slots on other meshes) seen from both sides
    for ob in [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("SM_Ship_%s" % ship)]:
        gl = [i for i, m in enumerate(ob.data.materials) if m and ("Glass" in m.name or ob.name.endswith("_Canopy"))]
        if not gl:
            continue
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index not in gl], context="FACES")
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
        me = bpy.data.meshes.new(ob.name + "_inner")
        bm.to_mesh(me)
        bm.free()
        inner = bpy.data.objects.new(me.name, me)
        inner.matrix_world = ob.matrix_world
        sc.collection.objects.link(inner)
    for name, loc, rot, f in views:
        cam.location, cam.rotation_euler, cam.data.angle = loc, rot, math.radians(f)
        path = os.path.join(out_dir, "holes_%s.png" % name)
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(path)
        px = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4)[:, :, 0]
        share = float((px > 0.5).mean())
        bpy.data.images.remove(img)
        if share > 0.0005:
            out.append({"view": name, "world_pct": round(100 * share, 3), "mask": path})
            if os.environ.get("GEOCHECK_DEBUG"):
                # the same view with random colours per object: which part should have closed the hole
                sh.color_type, sh.light = "RANDOM", "STUDIO"
                sc.render.filepath = path.replace(".png", "_obj.png")
                bpy.ops.render.render(write_still=True)
                sh.color_type, sh.light = "SINGLE", "FLAT"
    return out


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    ship = args[0]
    out_dir = os.path.abspath(args[1]) if len(args) > 1 else os.path.join(ROOT, "Saved", "GeoCheck")
    os.makedirs(out_dir, exist_ok=True)
    recipe = json.load(open(os.path.join(ROOT, "ArtSource", "Ships", ship, "HardSurface", "%s_hs.json" % ship), encoding="utf-8"))
    exempt = recipe.get("checks", {}).get("floating_exempt", [])
    kit_rooms = add_kit_rooms(ship, recipe)
    floating, penetrating, tree = floating_and_penetrating(ship, exempt)
    report = {
        "mirrored_decals": mirrored_mesh_decals(ship) + mirrored_projected(ship, tree),
        "floating": floating,
        "penetrating": penetrating,
        "hull_in_rooms": hull_in_rooms(ship, recipe),
    }
    report["placeholders"], report["warnings"] = placeholders(ship)
    report["holes"] = holes(ship, out_dir)
    report["walk_blocked"], tight = walk_blocked(ship, recipe)
    report["warnings"] += [dict(t, walk_tight=True) for t in tight]
    report["pass"] = not any(report[k] for k in ("mirrored_decals", "floating", "penetrating", "hull_in_rooms", "placeholders",
                                                 "holes", "walk_blocked"))
    report["kit_rooms"] = kit_rooms
    report["counts"] = {k: len(report[k]) for k in ("mirrored_decals", "floating", "penetrating", "hull_in_rooms", "placeholders",
                                                    "holes", "walk_blocked", "warnings")}
    json.dump(report, open(os.path.join(out_dir, "geocheck.json"), "w", encoding="utf-8"), indent=1)
    print("GEOCHECK " + json.dumps({"pass": report["pass"], "counts": report["counts"], "json": os.path.join(out_dir, "geocheck.json")}))


if __name__ == "__main__":       # (blender --python runs it as __main__; hull_fit_kit_rooms imports it)
    main()
