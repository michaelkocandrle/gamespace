"""Ship lights (step 6 of the SC detail plan, skill ship-pipeline 3b3), called by hs_build_ship.py after
the shape layers. Recipe block "lights", LAYOUT coordinates:

  lenses  a light fitting on the hull: a dark housing and an emissive lens, laid on the surface by a ray
          like the decals ("on": pod (x, deg) / side (x, z) / top / bottom (x, y) / ray (at, dir)), "size"
          [length, width, height] m, "color" (key of COLOURS -> material slot Light<Colour>), "mirror"
          (default true; "mirror_color" for the starboard copy: red port, green starboard), and optionally
          "light": a real light in front of it {"type": point / spot, "intensity_cd", "radius_m",
          "cone_deg", "aim": [x, y, z] layout point for a spot}.
  strips  emissive light strips in a dark channel along a pod or, with "on": side / bottom / top and "z" / "y",
          along the hull; ("pod_line": x range at deg; "r" places it at
          that radius instead of on the surface, e.g. inside the open bay), "width" m, "color".
  points  bare lights without a fitting (inside a bay): "at" layout point, "color", "light" as above.

The real lights are not geometry: they go to the scene property "hs_lights" (JSON), hs_assemble_ship.py
moves them into ship coordinates and writes Export/<Ship>_lights.json, and import_ship.py adds them to the
Blueprint as light components (no shadows).
"""
import json
import math

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

import hs_build_part as hp

COLOURS = {
    "red": (1.0, 0.05, 0.02), "green": (0.05, 1.0, 0.25), "white": (1.0, 0.95, 0.88),
    "amber": (1.0, 0.42, 0.05), "strip": (0.65, 0.85, 1.0), "warm": (1.0, 0.68, 0.38),
}


def _tree(coll):
    """BVH of every evaluated mesh of the collection (plates, pods, hull), world space."""
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    for ob in coll.objects:
        if ob.type != "MESH" or "Greebles" in ob.name:
            continue
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        tmp = bmesh.new()
        tmp.from_mesh(me)
        tmp.transform(ob.matrix_world)
        m = bpy.data.meshes.new("_tmp")
        tmp.to_mesh(m)
        tmp.free()
        bm.from_mesh(m)
        bpy.data.meshes.remove(m)
        ev.to_mesh_clear()
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    return tree


def _ray(spec, side, pod_axis):
    on = spec["on"]
    if on == "pod":
        a = math.radians(spec["deg"] if side > 0 else 180.0 - spec["deg"])
        radial = Vector((0.0, math.cos(a), math.sin(a)))
        return Vector((spec["x"], pod_axis[0] * side, pod_axis[1])) + radial * 3.0, -radial
    if on == "side":
        return Vector((spec["x"], 10.0 * side, spec["z"])), Vector((0, -side, 0))
    if on in ("top", "bottom"):
        s = 1 if on == "top" else -1
        return Vector((spec["x"], spec.get("y", 0.0) * side, 10.0 * s)), Vector((0, 0, -s))
    if on == "ray":
        at, d = Vector(spec["at"]), Vector(spec["dir"]).normalized()
        at.y *= side
        d.y *= side
        return at - d * 3.0, d
    raise ValueError(on)


def _frame(n):
    x = Vector((1, 0, 0)) - n * n.x
    if x.length < 1e-3:
        x = n.orthogonal()
    x.normalize()
    return x, n.cross(x)


def _box(bm, centre, x, y, n, size):
    res = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=res["verts"])
    m = Matrix((x, y, n)).transposed().to_4x4()
    m.translation = centre
    bmesh.ops.transform(bm, matrix=m, verts=res["verts"])


def _light_entry(name, spec_light, colour, loc, direction, side):
    e = {"name": name, "type": spec_light.get("type", "point"), "color": list(COLOURS[colour]),
         "intensity_cd": spec_light.get("intensity_cd", 20.0), "radius_m": spec_light.get("radius_m", 2.0),
         "location": [round(v, 4) for v in loc], "direction": [round(v, 4) for v in direction]}
    if e["type"] == "spot":
        e["cone_deg"] = spec_light.get("cone_deg", 40.0)
        if "aim" in spec_light:
            aim = Vector(spec_light["aim"])
            aim.y *= side
            e["direction"] = [round(v, 4) for v in (aim - Vector(loc)).normalized()]
    return e


def apply(recipe, made, coll, mats_factory, bevel):
    spec = recipe.get("lights")
    if not spec:
        return {}
    rev = recipe["parts"]["pod"]["revolve"]
    axis = (rev["axis"]["y"], rev["axis"]["z"])
    tree = _tree(coll)
    geom = {}          # colour -> bmesh of lenses / strips
    housing = bmesh.new()
    lights = []

    def bm_for(colour):
        if colour not in geom:
            geom[colour] = bmesh.new()
        return geom[colour]

    for lens in spec.get("lenses", []):
        for side in ((1, -1) if lens.get("mirror", True) else (1,)):
            colour = lens["color"] if side > 0 else lens.get("mirror_color", lens["color"])
            origin, d = _ray(lens, side, axis)
            hit, n, _, _ = tree.ray_cast(origin, d, 20.0)
            if hit is None:
                print("HSLIGHTS miss", lens["name"], side)
                continue
            n = n.normalized()
            x, y = _frame(n)
            ln, lw, lh = lens.get("size", [0.1, 0.035, 0.012])
            _box(housing, hit + n * 0.004, x, y, n, (ln + 0.03, lw + 0.03, 0.008))
            _box(bm_for(colour), hit + n * (0.008 + lh / 2), x, y, n, (ln, lw, lh))
            name = lens["name"] + ("" if not lens.get("mirror", True) else ("_L" if side > 0 else "_R"))
            if lens.get("light"):
                lights.append(_light_entry(name, lens["light"], colour, hit + n * (0.03 + lh), n, side))
    for st in spec.get("strips", []):
        x0, x1 = st["x"]
        steps = max(4, int((x1 - x0) / 0.05))
        for side in ((1, -1) if st.get("mirror", True) else (1,)):
            colour = st["color"]
            pts = []
            for k in range(steps + 1):
                xx = x0 + (x1 - x0) * k / steps
                if "r" in st:
                    a = math.radians(st["deg"] if side > 0 else 180.0 - st["deg"])
                    radial = Vector((0.0, math.cos(a), math.sin(a)))
                    centre = Vector((xx, axis[0] * side, axis[1]))
                    pts.append((centre + radial * st["r"], -radial if st.get("facing") == "in" else radial))
                else:
                    if st.get("on") in ("side", "bottom", "top"):
                        # hull strips: running lights along the side / belly (z or y fixed)
                        origin, d = _ray({"on": st["on"], "x": xx, "z": st.get("z", 0.0), "y": st.get("y", 0.0)}, side, axis)
                    else:
                        origin, d = _ray({"on": "pod", "x": xx, "deg": st["deg"]}, side, axis)
                    hit, n, _, _ = tree.ray_cast(origin, d, 20.0)
                    if hit is not None:
                        pts.append((hit, n.normalized()))
            if "r" not in st and st.get("on", "pod") == "pod" and len(pts) > 4:
                # a ray that fell into a panel gap lands on the substructure 3 cm deeper: drop it
                def rad(p, side=side):
                    return (Vector((0.0, p.y, p.z)) - Vector((0.0, axis[0] * side, axis[1]))).length
                rs = sorted(rad(p) for p, _ in pts)
                med = rs[len(rs) // 2]
                pts = [(p, n) for p, n in pts if abs(rad(p) - med) < 0.012]
            for (pa, na), (pb, nb) in zip(pts, pts[1:]):
                mid, n = (pa + pb) / 2, (na + nb).normalized()
                t = (pb - pa)
                length = t.length
                if length < 1e-4:
                    continue
                t.normalize()
                y = n.cross(t)
                w = st.get("width", 0.02)
                _box(housing, mid + n * 0.003, t, y, n, (length + 0.001, w + 0.02, 0.006))
                _box(bm_for(colour), mid + n * 0.007, t, y, n, (length + 0.001, w, 0.005))
            if st.get("light") and pts:
                pa, na = pts[len(pts) // 2]
                name = st["name"] + ("" if not st.get("mirror", True) else ("_L" if side > 0 else "_R"))
                lights.append(_light_entry(name, st["light"], colour, pa + na * 0.05, na, side))
    for pt in spec.get("points", []):
        for side in ((1, -1) if pt.get("mirror", True) else (1,)):
            at = Vector(pt["at"])
            at.y *= side
            name = pt["name"] + ("" if not pt.get("mirror", True) else ("_L" if side > 0 else "_R"))
            lights.append(_light_entry(name, pt["light"], pt["color"], at, Vector((0, 0, -1)), side))
    objs = []
    if housing.verts:
        ob = hp.finish(housing, "SM_Ship_Detail_LightHousings", coll, bevel)
        ob.modifiers["Bevel"].width = 0.002
        ob.data.materials.append(mats_factory("dark"))
        objs.append(ob)
    else:
        housing.free()
    for colour, bm in geom.items():
        ob = hp.finish(bm, "SM_Ship_Detail_Light_%s" % colour.title(), coll, bevel)
        ob.modifiers["Bevel"].width = 0.002
        ob.data.materials.append(mats_factory("light_" + colour))
        objs.append(ob)
    for ob in objs:
        made["light_" + ob.name] = ob
    bpy.context.scene["hs_lights"] = json.dumps(lights)
    return {"lenses": len(spec.get("lenses", [])), "strips": len(spec.get("strips", [])), "lights": len(lights),
            "objects": [o.name for o in objs]}
