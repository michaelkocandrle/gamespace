"""Textured beauty renders of a ship .blend from fixed angles, for reviewing an AI model by eye.

    blender -b <Ship>.blend --python Tools/Blender/render_ship_views.py -- --out DIR [--prefix NAME] [--res 1600]

Views: 3/4 front-left from above, 3/4 rear-right, side (starboard), front, top, belly. EEVEE, a sun and
a soft world, the model's own materials; the camera frames the bounding box of all visible meshes.
Writes <out>/<prefix>_<view>.png and prints RENDERVIEWS {...}.
"""
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector

VIEWS = {
    "front34": (35, -35, 20), "rear34": (-145, -145, 15), "side": (0, -90, 0),
    "front": (0, 0, 0), "top": (0, 0, 90), "belly": (0, 0, -90),
}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--prefix", default="ship")
    ap.add_argument("--res", type=int, default=1600)
    args = ap.parse_args(argv)
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    scene = bpy.context.scene
    for o in scene.objects:
        if o.name.startswith(("UCX_", "UBX_", "USP_", "UCP_", "HIGH_")):
            o.hide_render = True   # collision hulls and reference copies are not part of the look
    meshes = [o for o in scene.objects if o.type == "MESH" and o.visible_get() and not o.hide_render]
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    centre, radius = (lo + hi) / 2, (hi - lo).length / 2
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = args.res, int(args.res * 0.5625)
    scene.render.film_transparent = False
    world = bpy.data.worlds.new("RV") if not scene.world else scene.world
    scene.world = world
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.32, 0.34, 0.37, 1)
    bg.inputs[1].default_value = 0.8
    sun_data = bpy.data.lights.new("RV_Sun", "SUN")
    sun_data.energy = 3.5
    sun = bpy.data.objects.new("RV_Sun", sun_data)
    scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-40))
    cam_data = bpy.data.cameras.new("RV_Cam")
    cam = bpy.data.objects.new("RV_Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam_data.lens = 50
    written = {}
    for name, (yaw_off, yaw, pitch) in VIEWS.items():
        # yaw: direction the camera sits at, measured from +X (nose) towards +Y; pitch: elevation.
        az = math.radians(yaw + (yaw_off if name.endswith("34") else 0))
        if name in ("front34",):
            az = math.radians(35)
        if name == "rear34":
            az = math.radians(-145)
        el = math.radians(pitch)
        if name in ("side",):
            az = math.radians(-90)
        if name in ("front",):
            az = 0.0
        d = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
        dist = radius / math.tan(math.radians(18)) * 1.05
        cam.location = centre + d * dist
        up = Vector((0, 0, 1)) if abs(el) < math.radians(80) else Vector((-1, 0, 0)) if el > 0 else Vector((1, 0, 0))
        forward = (centre - cam.location).normalized()
        right = forward.cross(up).normalized()
        true_up = right.cross(forward)
        from mathutils import Matrix
        cam.matrix_world = Matrix((
            (right.x, true_up.x, -forward.x, cam.location.x),
            (right.y, true_up.y, -forward.y, cam.location.y),
            (right.z, true_up.z, -forward.z, cam.location.z),
            (0, 0, 0, 1)))
        path = os.path.join(out, "%s_%s.png" % (args.prefix, name))
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        written[name] = path
    print("RENDERVIEWS " + json.dumps(written))


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:])
