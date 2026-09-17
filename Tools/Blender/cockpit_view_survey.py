"""What the pilot sees: ray-casts a ship's cockpit view against the real model in Blender.

    & "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b ArtSource\\Ships\\Vanguard\\Vanguard.blend ^
        --python Tools\\Blender\\cockpit_view_survey.py -- 520 0 110 88

Arguments (all optional): eye X Y Z in UE centimetres (the value of cockpit_camera.relative_location in
<Ship>_setup.json), then the camera's horizontal field of view in degrees. Without arguments it sweeps
a grid of eye positions instead and prints the most open ones.

Blender metres = UE centimetres / 100 with Y mirrored, and the ship looks along +X, so an eye of
(520, 0, 110) in the setup file is (5.2, 0, 1.1) here. Meshes whose name starts with UCX_ (collision)
are ignored; everything else the pilot would see is not.

Why: the Vanguard has no modelled cockpit interior. From inside the canopy bubble the tinted glass
sits ~13 cm from the eye and fills the view (0 % open sky), so the eye belongs at the windscreen.
Run this after changing a ship's model or its cockpit_camera, then put the numbers in the setup file.
"""

import math
import sys

import bpy
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ROWS, COLS = 13, 25

MESHES = [o for o in bpy.data.objects if o.type == "MESH" and not o.name.startswith("UCX_") and "STAGE" not in o.name]


def cast(ob, origin, direction):
    matrix = ob.matrix_world
    inverse = matrix.inverted()
    hit, location, normal, index = ob.ray_cast(inverse @ origin, (inverse.to_3x3() @ direction).normalized(), distance=200.0)
    return (matrix @ location - origin).length if hit else 1e9


def survey(eye, fov):
    """(open %, per-object %, an ASCII picture of the view from bottom row to top)."""
    blocked = {}
    rows = []
    fov_v = fov * 9.0 / 16.0
    for r in range(ROWS - 1, -1, -1):
        pitch = math.radians((r / (ROWS - 1) - 0.5) * fov_v)
        line = ""
        for c in range(COLS):
            yaw = math.radians((c / (COLS - 1) - 0.5) * fov)
            direction = Vector((math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch)))
            nearest, name = 1e9, None
            for ob in MESHES:
                distance = cast(ob, eye, direction)
                if distance < nearest:
                    nearest, name = distance, ob.name
            if name is None:
                line += "."
            else:
                blocked[name] = blocked.get(name, 0) + 1
                line += "#" if "Canopy" not in name else "o"
        rows.append(line)
    total = ROWS * COLS
    return 100.0 * (total - sum(blocked.values())) / total, {k: 100.0 * v / total for k, v in blocked.items()}, rows


def clearance(eye):
    return min(cast(ob, eye, Vector(d)) for ob in MESHES
               for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)))


if len(ARGS) >= 3:
    eye = Vector((float(ARGS[0]) / 100.0, -float(ARGS[1]) / 100.0, float(ARGS[2]) / 100.0))
    fov = float(ARGS[3]) if len(ARGS) >= 4 else 88.0
    open_percent, blocked, rows = survey(eye, fov)
    print("COCKPIT eye (%.0f, %.0f, %.0f) cm, FOV %.0f deg" % (eye.x * 100, -eye.y * 100, eye.z * 100, fov))
    for line in rows:
        print("COCKPIT " + line)
    print("COCKPIT open %.1f %% of the view ('.' open, '#' hull, 'o' canopy glass), nearest surface %.2f m" % (open_percent, clearance(eye)))
    for name, percent in sorted(blocked.items()):
        print("COCKPIT   %-28s %5.1f %%" % (name, percent))
else:
    print("COCKPIT sweeping eye positions (x, z in cm): open %, nearest surface")
    best = []
    for x in range(300, 660, 20):
        for z in range(90, 130, 10):
            eye = Vector((x / 100.0, 0.0, z / 100.0))
            open_percent, blocked, _ = survey(eye, 88.0)
            near = clearance(eye)
            best.append((open_percent, x, z, near))
            print("COCKPIT x %4d z %4d  open %5.1f %%  nearest %.2f m" % (x, z, open_percent, near))
    best.sort(reverse=True)
    print("COCKPIT best: x %d z %d, open %.1f %%, nearest %.2f m" % (best[0][1], best[0][2], best[0][0], best[0][3]))
