"""Find holes in the Steadfast interior: places where a player inside would see out into space.

    MSYS_NO_PATHCONV=1 "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b \\
        --python Tools/Blender/find_interior_holes.py

Loads the room GLBs and the cockpit glass, and from a grid of points inside every room casts rays
in all directions. A ray "escapes" when it hits nothing, or when the first thing it hits is the back
of a face: Unreal draws single-sided, so the back of a wall is not there (Docs/WORKFLOW.md 9.3 h).
Glass counts as a wall. Prints HOLE lines grouped by where the ray left, and HOLES <n> at the end;
0 means closed. Rooms and their boxes come from Interior_layout.json's neighbour, the builder.
"""

import collections
import math
import os

import bpy
import mathutils

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FOLDER = os.path.join(ROOT, "ArtSource", "Ships", "Steadfast", "Interior")
FILES = ("CargoBay", "Corridor", "EngineRoom", "Cockpit", "CockpitGlass", "DoorLeaf")
# Where a person can stand, per room (Blender metres), kept a little off the walls.
ROOMS = {
    "EngineRoom": ((-6.6, -1.4), (-2.6, 2.6)),
    "CargoBay": ((0.4, 7.6), (-2.6, 2.6)),
    "Corridor": ((9.3, 16.7), (-0.6, 0.6)),
    "Cockpit": ((17.5, 21.6), (-1.8, 1.8)),
}
HEIGHTS = (0.4, 1.2, 1.9, 2.3)
STEP = 0.8
DIRECTIONS = 160


def fibonacci(n):
    golden = math.pi * (3.0 - math.sqrt(5.0))
    for i in range(n):
        z = 1.0 - 2.0 * (i + 0.5) / n
        r = math.sqrt(1.0 - z * z)
        yield mathutils.Vector((math.cos(golden * i) * r, math.sin(golden * i) * r, z))


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for name in FILES:
        bpy.ops.import_scene.gltf(filepath=os.path.join(FOLDER, name + ".glb"))
    # The door leaf is centred on the origin in its own file; move it into the doorway, closed.
    for obj in bpy.data.objects:
        if obj.name.startswith("DoorLeaf"):
            obj.location = (17.0, 0.0, 1.06)
            obj.scale = (1.0, 2.0, 1.0)          # both leaves, closed
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()
    glass = {o.name for o in bpy.data.objects if o.name.startswith("CockpitGlass")}
    directions = list(fibonacci(DIRECTIONS))
    holes = collections.Counter()
    samples = collections.defaultdict(list)
    for room, (xs, ys) in ROOMS.items():
        nx = max(1, int((xs[1] - xs[0]) / STEP) + 1)
        ny = max(1, int((ys[1] - ys[0]) / STEP) + 1)
        for i in range(nx):
            for j in range(ny):
                for z in HEIGHTS:
                    origin = mathutils.Vector((xs[0] + (xs[1] - xs[0]) * i / max(1, nx - 1),
                                               ys[0] + (ys[1] - ys[0]) * j / max(1, ny - 1), z))
                    # A point inside a prop (a pipe column, a lamp) sees the prop's inside, which is
                    # no hole: only points with 30 cm of clear air round them count.
                    if any(scene.ray_cast(depsgraph, origin, d, distance=0.3)[0] for d in directions[::4]):
                        continue
                    for d in directions:
                        # Through the backs of faces (Unreal does not draw them) until the ray meets
                        # the front of something - or nothing, which is the hole.
                        start = origin
                        for _ in range(12):
                            hit, location, normal, index, obj, _ = scene.ray_cast(depsgraph, start, d, distance=60.0)
                            if not hit or obj.name in glass or normal.dot(d) < 0.0:
                                break
                            start = location + d * 0.002
                        if hit and (obj.name in glass or normal.dot(d) < 0.0):
                            continue
                        where = location if hit else origin + d * 3.0
                        what = "nic"
                        if hit:
                            mat = obj.data.materials[obj.data.polygons[index].material_index].name if obj.data.materials else "-"
                            what = "rub %s/%s n=(%.1f,%.1f,%.1f)" % (obj.name, mat, normal.x, normal.y, normal.z)
                        key = (room, what,
                               round(where.x * 2) / 2, round(where.y * 2) / 2, round(where.z * 2) / 2)
                        holes[key] += 1
                        if len(samples[key]) < 1:
                            samples[key].append((tuple(round(c, 2) for c in origin), tuple(round(c, 2) for c in d)))
    for key, count in holes.most_common(60):
        print("HOLE %s %s kolem (%.1f, %.1f, %.1f): %d paprsků, např. z %s směr %s"
              % (key[0], key[1], key[2], key[3], key[4], count, samples[key][0][0], samples[key][0][1]))
    print("HOLES %d" % sum(holes.values()))


main()
