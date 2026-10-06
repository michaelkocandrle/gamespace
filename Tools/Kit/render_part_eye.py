"""A quick eye-height render of a run of kit parts from a kit blend (parts factory, step 4 blockout check of a section
without its own test section in Unreal, 6. 10. 2026).

    blender -b --factory-startup --python-exit-code 1 --python Tools/Kit/render_part_eye.py -- <Kit_*.blend> <out.png> <part>,<part>,... [<part>,... per slot]

Each argument after the output is one slot of the run (comma-separated parts that share it, e.g. a floor and its
shell); slots follow along +X by the first part's length (its bounding box in X). The camera stands 0.45 m before
the run, at 1.65 m, looking down the run with a 90 deg horizontal FOV (as SC). A dim studio world and soft lights,
Eevee: the forms and the passage, not the look.
"""
import math
import os
import sys

import bpy
from mathutils import Vector


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    blend, out, slots = args[0], args[1], [a.split(",") for a in args[2:]]
    bpy.ops.wm.open_mainfile(filepath=blend)
    sc = bpy.context.scene
    run = bpy.data.collections.new("eye_run")
    sc.collection.children.link(run)
    x = 0.0
    for k, slot in enumerate(slots):
        length = None
        for name in slot:
            ob = bpy.data.objects[name]
            dup = ob.copy()
            dup.location = Vector((x, 0.0, 0.0))
            run.objects.link(dup)
            if length is None:
                xs = [v.co.x for v in ob.data.vertices]
                length = max(xs) - min(xs)
        x += length
    for c in bpy.data.collections:
        if c is not run:
            c.hide_render = True
    run.hide_render = False
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    sc.view_settings.view_transform = "AgX"
    w = bpy.data.worlds.new("eye_world")
    sc.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.2, 0.21, 0.22, 1.0)
    bg.inputs[1].default_value = 0.5
    for k in range(int(x / 1.2) + 1):
        ld = bpy.data.lights.new("eye_l%d" % k, "AREA")
        ld.energy, ld.size = 60.0, 0.6
        lo = bpy.data.objects.new("eye_l%d" % k, ld)
        lo.location = (0.6 + k * 1.2, 0.0, 2.15)
        sc.collection.objects.link(lo)
    cd = bpy.data.cameras.new("eye_cam")
    cd.sensor_fit = "HORIZONTAL"
    cd.angle = math.radians(90.0)
    cam = bpy.data.objects.new("eye_cam", cd)
    sc.collection.objects.link(cam)
    cam.location = (-0.45, 0.0, 1.65)
    d = Vector((x, 0.0, 1.3)) - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    sc.render.filepath = os.path.abspath(out)
    bpy.ops.render.render(write_still=True)
    print("EYERENDER " + out)


main()
