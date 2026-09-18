"""Finds where an AI cockpit interior fits into a ship's cabin, and where the pilot's eye goes.

    blender -b ArtSource\\Ships\\<Ship>\\<Ship>_Meshy.blend --python Tools\\Blender\\fit_ship_interior.py -- ArtSource\\Ships\\<Ship>\\<Ship>_ai_build.json

Reads the "interior" section of the ship's recipe (source FBX, rotate_z_deg, and "fit": the search
limits) and the built hull (SM_Ship_<Ship> in the open .blend). Searches scale (width and length),
height ratio and x / z offset, and keeps a placement only when:
  - every sampled vertex of the interior is inside the hull, at least margin_m from it (no clipping);
  - the pilot's eye - behind the side-stick grips by eye_behind_stick_m, at least headroom_m under the
    canopy roof and at least eye_above_stick_m above the grips - has a clear view ahead: no hull face
    facing it within clear_view_deg above the horizon across +-clear_view_yaw_deg (the canopy roof slopes
    down towards the windscreen; seen almost edge-on from just below it, it was a bright bar across the
    HUD). The highest eye that manages this is taken;
  - the top of the dashboard is dash_below_eye_deg below the eye (under the HUD) and 0.4 m ahead of it.
Of those it prints the best: smallest gap between the interior's rim and the cabin walls, least
height distortion. Put the chosen one into the recipe (interior.placement) and the eye into
sockets.Cockpit and <Ship>_setup.json.

Why not simply "as large as fits": an AI cockpit tub is taller for its width than a fighter's canopy
bubble; scaled to fill it, its dashboard reached the canopy roof and left no room for the eye. Like a
real fighter, the tub sits down in the fuselage with its rim at the canopy rail.
"""

import json
import math
import os
import random
import sys
import time

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def path(p):
    return p if os.path.isabs(p) else os.path.join(REPO, p)


def main(argv):
    cfg = json.load(open(path(argv[0]), encoding="utf-8"))
    spec = cfg["interior"]
    fit = spec.get("fit", {})
    margin = fit.get("margin_m", 0.02)
    headroom = fit.get("headroom_m", 0.22)
    behind = fit.get("eye_behind_stick_m", 0.15)
    above = fit.get("eye_above_stick_m", 0.45)
    dash_lo, dash_hi = fit.get("dash_below_eye_deg", [15.0, 22.0])
    clear_deg = fit.get("clear_view_deg", 6.0)
    clear_yaw = fit.get("clear_view_yaw_deg", 40.0)
    stick = Vector(fit["stick_grip"])            # in the rotated, unscaled interior
    hull = bpy.data.objects["SM_Ship_%s" % cfg["ship"]]
    bvh = BVHTree.FromObject(hull, bpy.context.evaluated_depsgraph_get())

    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path(spec["source_fbx"]))
    ob = [o for o in bpy.data.objects if o not in before and o.type == "MESH"][0]
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob.data.transform(Matrix.Rotation(math.radians(spec.get("rotate_z_deg", 0.0)), 4, "Z"))
    co = [v.co.copy() for v in ob.data.vertices]
    lo_x, hi_x = min(c.x for c in co), max(c.x for c in co)
    print("FIT interior (rotated, unscaled) x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (
        lo_x, hi_x, min(c.y for c in co), max(c.y for c in co), min(c.z for c in co), max(c.z for c in co)))

    # Extremes of 30 slices along x (the rim, top and bottom) plus random points.
    slices = {}
    keys = (("ymin", lambda c: -c.y), ("ymax", lambda c: c.y), ("zmax", lambda c: c.z), ("zmin", lambda c: -c.z),
            ("ymaxz", lambda c: c.y + c.z), ("yminz", lambda c: -c.y + c.z))
    for c in co:
        s = slices.setdefault(min(29, int((c.x - lo_x) / (hi_x - lo_x) * 30)), {})
        for key, value in keys:
            if key not in s or value(c) > value(s[key]):
                s[key] = c
    extremes = [p for s in slices.values() for p in s.values()]
    rim = [s[k] for s in slices.values() for k in ("ymin", "ymax")]
    dash_top = max(co, key=lambda c: c.z)
    random.seed(3)
    coarse = extremes + random.sample(co, min(300, len(co)))
    fine = extremes + random.sample(co, min(20000, len(co)))

    def place(p, s, r, x0, z0):
        return Vector((p.x * s + x0, p.y * s, p.z * s * r + z0))

    def inside(p):
        loc, normal, _, dist = bvh.find_nearest(p)
        return (loc is not None and (p - loc).dot(normal) < 0 and dist >= margin), dist

    def fits(pts, *placement):
        return all(inside(place(p, *placement))[0] for p in pts)

    def roof(x):
        hit = bvh.ray_cast(Vector((x, 0, 50)), Vector((0, 0, -1)))
        return hit[0].z if hit[0] else -99.0

    def facing_hit(origin, direction, reach=4.0):
        """First hull face facing the ray within reach (faces seen from behind are culled in Unreal)."""
        start, travelled = origin, 0.0
        for _ in range(12):
            loc, normal, _, dist = bvh.ray_cast(start, direction, reach - travelled)
            if loc is None:
                return False
            if normal.dot(direction) < 0:
                return True
            travelled += dist + 1e-4
            start = loc + direction * 1e-4
        return False

    def clear_view(eye):
        for yaw in range(-int(clear_yaw), int(clear_yaw) + 1, 10):
            for pitch in (0.0, clear_deg / 3, clear_deg * 2 / 3, clear_deg):
                y, p = math.radians(yaw), math.radians(pitch)
                if facing_hit(eye, Vector((math.cos(p) * math.cos(y), math.cos(p) * math.sin(y), math.sin(p)))):
                    return False
        return True

    t = time.time()
    s_lo, s_hi = fit.get("scale", [0.9, 1.5])
    x_lo, x_hi = fit.get("x", [2.0, 4.0])
    z_lo, z_hi = fit.get("z", [0.5, 1.6])
    step = fit.get("step_m", 0.05)
    found = []
    s = s_lo
    while s <= s_hi + 1e-6:
        for r in fit.get("height_ratios", [1.0, 0.95, 0.9, 0.85, 0.8]):
            x0 = x_lo
            while x0 <= x_hi + 1e-6:
                z0 = z_lo
                while z0 <= z_hi + 1e-6:
                    if fits(coarse, s, r, x0, z0):
                        ex = x0 + s * stick.x - behind
                        d = place(dash_top, s, r, x0, z0)
                        lowest = z0 + s * r * stick.z + above
                        ez = roof(ex) - headroom
                        while ez >= lowest and not clear_view(Vector((ex, 0.0, ez))):
                            ez -= 0.02
                        angle = math.degrees(math.atan2(ez - d.z, d.x - ex))
                        if ez >= lowest and dash_lo <= angle <= dash_hi and d.x - ex >= 0.4:
                            gaps = sorted(inside(place(p, s, r, x0, z0))[1] for p in rim)
                            near = gaps[: len(gaps) * 3 // 4]
                            gap = sum(near) / len(near)
                            found.append((gap + 0.4 * (1.0 - r), s, r, x0, z0, gap, ex, ez, angle))
                    z0 += step
                x0 += step
        s += 0.05
    found.sort()
    print("FIT %d placements pass in %.0f s; best, checked with %d points:" % (len(found), time.time() - t, len(fine)))
    shown = 0
    for score, s, r, x0, z0, gap, ex, ez, angle in found:
        if not fits(fine, s, r, x0, z0):
            continue
        print("FIT scale %.2f height x%.2f offset (%.2f, 0, %.2f): rim %.3f m from the walls; eye (%.0f, 0, %.0f) cm, "
              "%.0f cm under the roof; dashboard top %.1f deg below the eye" % (
                  s, r, x0, z0, gap, ex * 100, ez * 100, (roof(ex) - ez) * 100, angle))
        shown += 1
        if shown >= fit.get("show", 5):
            break
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[sys.argv.index("--") + 1:]))
