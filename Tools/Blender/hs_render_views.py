"""Shaded orthographic views (front, side, top) and a 3/4 perspective of a part, for side-by-side
review of hard-surface work. Workbench studio light with cavity and outlines, so panel seams, bevels
and shading errors (bad normals, smoothing across hard edges) read at a glance.

    MSYS_NO_PATHCONV=1 blender -b Ship.blend --python Tools/Blender/hs_render_views.py -- \\
        --objects SM_Ship_Vanguard --crop-box -6.8,2.9,0.3,1.2,5.8,3.2 --out Saved/HardSurface/meshy --prefix meshy

--crop-box keeps only faces whose centre lies in the box (same as silhouette_compare.py). Views follow
silhouette_compare.py: front from +X, side from -Y (nose right), top from +Z (nose right).
"""
import argparse
import math
import os
import sys

import bmesh
import bpy
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from silhouette_compare import _crop_copy  # noqa: E402


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--collection", default="", help="all meshes in this collection (recursive)")
    ap.add_argument("--objects", default="")
    ap.add_argument("--crop-box", default="")
    ap.add_argument("--crop-cylinder", default="", help="yc,zc,r (see silhouette_compare.py)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--prefix", default="part")
    ap.add_argument("--res", type=int, default=900)
    ap.add_argument("--matcap", action="store_true", help="metal matcap instead of studio light")
    a = ap.parse_args(argv)
    a.out = os.path.abspath(a.out)
    os.makedirs(a.out, exist_ok=True)
    scene = bpy.context.scene
    names = [n for n in a.objects.split(",") if n]
    if a.collection:
        names += [o.name for o in bpy.data.collections[a.collection].all_objects if o.type == "MESH"]
    meshes = [o for o in scene.objects if o.type == "MESH" and
              ((o.name in names) if names else (not o.hide_render and not o.name.startswith("UCX_")))]
    if a.crop_box:
        box = [float(v) for v in a.crop_box.split(",")]
        cyl = [float(v) for v in a.crop_cylinder.split(",")] if a.crop_cylinder else None
        meshes = [_crop_copy(bpy, bmesh, o, box, cyl) for o in meshes]
    keep = set(meshes)
    # Only what the view layer shows: excluded library collections (the HS_Kit greebles) must keep
    # rendering through their instances.
    for o in bpy.context.view_layer.objects:
        o.hide_render = o not in keep

    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    centre, size = (lo + hi) / 2, hi - lo

    scene.render.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light = "STUDIO"
    sh.color_type = "SINGLE"
    sh.single_color = (0.62, 0.63, 0.65)
    sh.show_cavity = True
    sh.cavity_type = "BOTH"
    sh.cavity_ridge_factor, sh.cavity_valley_factor = 1.0, 1.4
    sh.show_object_outline = True
    sh.object_outline_color = (0.05, 0.05, 0.06)
    sh.show_specular_highlight = True
    sh.background_type = "VIEWPORT"
    sh.background_color = (0.09, 0.1, 0.12)
    scene.display.render_aa = "16"
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x = scene.render.resolution_y = a.res
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"

    cam_data = bpy.data.cameras.new("HS_CAM")
    cam = bpy.data.objects.new("HS_CAM", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    far = size.length * 2 + 1
    cam_data.clip_start, cam_data.clip_end = 0.01, far * 3
    views = {
        "front": (Vector((far, 0, 0)), Euler((math.pi / 2, 0, math.pi / 2)), max(size.y, size.z)),
        "side": (Vector((0, -far, 0)), Euler((math.pi / 2, 0, 0)), max(size.x, size.z)),
        "top": (Vector((0, 0, far)), Euler((0, 0, 0)), max(size.x, size.y)),
    }
    for view, (offset, rot, extent) in views.items():
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = extent * 1.1
        cam.location, cam.rotation_euler = centre + offset, rot
        scene.render.filepath = os.path.join(a.out, "%s_%s.png" % (a.prefix, view))
        bpy.ops.render.render(write_still=True)
    # 3/4 from front-left-above, perspective, framed on the bbox.
    cam_data.type = "PERSP"
    cam_data.lens = 50
    d = Vector((1.0, -0.9, 0.55)).normalized()
    cam.location = centre + d * (size.length * 1.35)
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(a.out, "%s_34.png" % a.prefix)
    bpy.ops.render.render(write_still=True)
    print("HS_VIEWS", a.out, a.prefix, [round(v, 3) for v in lo], [round(v, 3) for v in hi])


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
