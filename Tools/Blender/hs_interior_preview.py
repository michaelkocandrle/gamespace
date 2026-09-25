"""Eevee preview of a ship interior from the game's shot positions, for iterating the look without packaging.

    blender -b ArtSource/Ships/<Ship>/HardSurface/<Ship>_HS.blend --python Tools/Blender/hs_interior_preview.py -- \
        Tools/Shots/wayfarer_interior.json <out folder> [shot names...]

Cameras from the preset's camera_local / look_local (ship space in metres as the shot runner reads it:
layout = local + (10.25, 0, 1.2) with y mirrored - the Wayfarer's assemble offset), field of view from the
shot (horizontal). Lights: the interior entries of the scene's hs_lights (point / spot, candela converted
to watts roughly), a dim world. Not a match for Unreal's exposure or Lumen - it shows shape, layering,
materials and where the light falls.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

OFF = Vector((10.25, 0.0, 1.2))


def to_layout(p):
    return Vector((p[0], -p[1], p[2])) + OFF


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    preset, out = args[0], args[1]
    names = {a for a in args[2:] if "=" not in a}
    opts = dict(a.split("=", 1) for a in args[2:] if "=" in a)       # exposure=<EV> world=<strength> light=<gain>
    os.makedirs(out, exist_ok=True)
    shots = [s for s in json.load(open(preset, encoding="utf-8"))["shots"] if "camera_local" in s and (not names or s["name"] in names)]
    if "eye" in opts:
        # the pilot's eye: SOCKET_Cockpit of the recipe (layout metres), level view along +x, FOV 88 (the game's
        # cockpit camera); eye=<x,y,z> overrides the position
        ex, ey, ez = [float(v) for v in opts["eye"].split(",")] if opts["eye"] not in ("1", "") else (16.95, 0.0, 1.65)
        shots = [{"name": "eye", "fov": 88, "camera_local": [ex - OFF.x, -ey, ez - OFF.z], "look_local": [ex + 5.0 - OFF.x, -ey, ez - OFF.z]}]
    sc = bpy.context.scene
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.exposure = float(opts.get("exposure", 1.5))
    w = bpy.data.worlds.new("preview")
    sc.world = w
    w.use_nodes = True
    next(n for n in w.node_tree.nodes if n.type == "BACKGROUND").inputs[1].default_value = float(opts.get("world", 0.03))
    for o in list(bpy.data.objects):
        if o.type in ("LIGHT", "CAMERA"):
            bpy.data.objects.remove(o)
    for o in bpy.data.objects:
        # canopy glass renders as a dark sheet in Eevee (in the game it is clear): hide it
        if o.type == "MESH" and (o.name.endswith("_Canopy") or any(sl.material and "Glass" in sl.material.name for sl in o.material_slots)):
            o.hide_render = True
    for l in json.loads(sc.get("hs_lights", "[]")):
        if not l["name"].startswith("int_"):
            continue
        spot = l.get("type") == "spot"
        data = bpy.data.lights.new(l["name"], "SPOT" if spot else "POINT")
        data.energy = l["intensity_cd"] * (3.0 if spot else 1.5) * float(opts.get("light", 1.0))
        data.color = l["color"]
        data.shadow_soft_size = 0.05
        if spot:
            data.spot_size = math.radians(l.get("cone_deg", 40.0))
            data.spot_blend = 0.5
        ob = bpy.data.objects.new(l["name"], data)
        sc.collection.objects.link(ob)
        ob.location = l["location"]
        d = Vector(l.get("direction", (0, 0, -1)))
        ob.rotation_euler = Vector((0, 0, -1)).rotation_difference(d).to_euler()
    cam = bpy.data.cameras.new("preview")
    cam.lens_unit = "FOV"
    cam.sensor_fit = "HORIZONTAL"
    co = bpy.data.objects.new("preview", cam)
    sc.collection.objects.link(co)
    sc.camera = co
    for s in shots:
        cam.angle = math.radians(s.get("fov", 90))
        co.location = to_layout(s["camera_local"])
        co.rotation_euler = (to_layout(s["look_local"]) - co.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(out, s["name"] + ".png")
        bpy.ops.render.render(write_still=True)
        print("PREVIEW", sc.render.filepath)


main()
