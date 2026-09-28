"""Close-up renders of built kit parts from a standing eye (batch 4, 28. 9. 2026): the catalog renders frame a whole
2.3 m module in 900 px, too small to judge a component bay's detail.

    blender -b --factory-startup --python Tools/Kit/render_kit_closeup.py -- <Kit_*.blend> <part> [<part> ...]

Per part: an eye 1.65 m high, 1.3 m in front of the wall face, looking at the module's middle at waist height, plus
a 3/4 view from 0.9 m aside; a dim studio world and a soft light from the corridor's ceiling. Output
Saved/KitCatalog/closeup_<part>_{eye,side}.png (1400 x 1000).
"""
import math
import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "Saved", "KitCatalog")


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, args[0]))
    sc = bpy.context.scene
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 1400, 1000
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.exposure = 0.4
    w = bpy.data.worlds.new("closeup")
    sc.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.05, 0.05, 0.055, 1.0)
    bg.inputs[1].default_value = 1.0
    for o in list(sc.objects):
        if o.type in ("LIGHT", "CAMERA"):
            bpy.data.objects.remove(o)
    # a ceiling light over the corridor's middle, 1.2 m out from the wall, and a faint fill from the eye
    for name, loc, energy, size in (("ceiling", (1.2, 0.6, 2.3), 260.0, 1.2), ("fill", (1.6, 0.2, 1.6), 40.0, 0.6)):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy, ld.size = energy, size
        lo = bpy.data.objects.new(name, ld)
        lo.location = loc
        lo.rotation_euler = (Vector((0.2, 0.6, 0.6)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(lo)
    cd = bpy.data.cameras.new("eye")
    cd.lens = 28
    cam = bpy.data.objects.new("eye", cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    os.makedirs(OUT, exist_ok=True)
    for part in args[1:]:
        ob = bpy.data.objects.get(part)
        if ob is None:
            print("CLOSEUP missing", part)
            continue
        for o in sc.objects:
            if o.type == "MESH":
                o.hide_render = not (o is ob or o.parent is ob) or o.name.startswith("UCX_")
        for c in bpy.data.collections:
            c.hide_render = False
        L = ob.dimensions.y
        target = Vector((-0.1, L / 2, 0.62))
        for tag, eye in (("eye", Vector((1.3, L / 2, 1.65))), ("side", Vector((1.0, L / 2 - 0.9, 1.5)))):
            cam.location = eye
            cam.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
            sc.render.filepath = os.path.join(OUT, "closeup_%s_%s.png" % (part, tag))
            bpy.ops.render.render(write_still=True)
            print("CLOSEUP", sc.render.filepath)


main()
