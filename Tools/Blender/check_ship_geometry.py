"""Geometry check of a finished ship (the game blend after hs_assemble_ship.py), run before every hand-over.

    blender -b ArtSource/Ships/<Ship>/<Ship>_HS_Game.blend --python Tools/Blender/check_ship_geometry.py -- <Ship> [out_dir]

Prints GEOCHECK {...} (and writes <out_dir>/geocheck.json and the hole masks). A check fails with a list of what to fix:
  mirrored_decals     mesh-decal faces whose texture reads mirrored from their front ((T x B) . N < 0), and projected
                      interior decals (<Ship>_setup.json "Int_*") whose box reaches a surface behind the marked one -
                      the marking then shows mirrored on the wall's other side
  floating            interior parts (connected pieces) that touch nothing within TOL_TOUCH; lights and holograms
                      are exempt by material, known intentional ones by name in the recipe (checks.floating_exempt)
  penetrating         cockpit parts reaching behind the frame lining or outside the hull by more than TOL_PEN
  placeholders        slots without a material or with Blender's default; large plain faces are listed (warning)
  holes               ship-less pixels (the world) seen from the player's positions with every surface opaque -
                      the eye and the interior shot cameras of Tools/Shots/<ship>_interior.json
Meaning of pass: every list empty (warnings do not fail).
"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Vector
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
    bad = []
    for d in setup.get("decals", []):
        if not d["name"].startswith("Int_"):
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
        travelled = dist
        p = hit - x * 0.0005
        while travelled < half:
            h2, n2, i2, d2 = tree.ray_cast(p, -x, half - travelled)
            if h2 is None:
                break
            travelled += d2
            if n2.dot(x) < 0:
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


def floating_and_penetrating(ship, exempt_names):
    parts = [o for o in (obj(ship, "_Interior"), obj(ship, "_InteriorKit")) if o is not None]
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
    floating, penetrating, tree = floating_and_penetrating(ship, exempt)
    report = {
        "mirrored_decals": mirrored_mesh_decals(ship) + mirrored_projected(ship, tree),
        "floating": floating,
        "penetrating": penetrating,
    }
    report["placeholders"], report["warnings"] = placeholders(ship)
    report["holes"] = holes(ship, out_dir)
    report["pass"] = not any(report[k] for k in ("mirrored_decals", "floating", "penetrating", "placeholders", "holes"))
    report["counts"] = {k: len(report[k]) for k in ("mirrored_decals", "floating", "penetrating", "placeholders", "holes", "warnings")}
    json.dump(report, open(os.path.join(out_dir, "geocheck.json"), "w", encoding="utf-8"), indent=1)
    print("GEOCHECK " + json.dumps({"pass": report["pass"], "counts": report["counts"], "json": os.path.join(out_dir, "geocheck.json")}))


main()
