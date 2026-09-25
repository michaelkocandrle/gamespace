"""How much the pilot sees out of the cockpit, measured on a mask rendered from the eye (the game's cockpit camera).

    blender -b ArtSource/Ships/<Ship>/<Ship>_HS_Game.blend --python Tools/Blender/eye_view_metrics.py -- <Ship> [out.png]

Renders 1920x1080 from SOCKET_Cockpit with the setup's FOV (as Tools/Blender/mcp/mcp_eye_view.py): the outside (the
world through the canopy openings, glass hidden) white, everything of the ship black, back faces culled as in
Unreal. Prints EYEVIEW {...}:
  outside_pct      share of the frame where the pilot sees out (no frame, no dash, no displays)
  dash_top_pct     height of the dash's top edge in the frame, % from the bottom (median over the middle 60 %
                   of the width: the first outside pixel going up each column)
  widest_pillar_pct  widest run of ship between two outside areas along rows in the upper 60 % of the frame, % of
                   the width (frame members, pillars; runs touching the frame's edge are not pillars)
  pillar_in_15deg  whether any ship pixel crosses the level line of sight within +-15 deg of straight ahead
Targets from the SC references: ship-pipeline skill, cockpit table (author 25. 9. 2026).
"""
import json
import math
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp"))
from mcp_eye_view import eye_of  # noqa: E402


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    ship = args[0]
    out = os.path.abspath(args[1]) if len(args) > 1 else os.path.join(bpy.app.tempdir, "eye_mask.png")
    eye, fov, pitch = eye_of(ship)
    sc = bpy.context.scene
    cam = bpy.data.objects.new("EyeMetric", bpy.data.cameras.new("EyeMetric"))
    sc.collection.objects.link(cam)
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.angle = math.radians(fov)
    cam.data.clip_start = 0.02
    cam.location = eye
    cam.rotation_euler = (math.radians(90 + pitch), 0, math.radians(-90))
    sc.camera = cam
    for o in bpy.data.objects:
        if o.type == "MESH" and (o.name.endswith(("_Canopy", "_Hologram")) or o.name.startswith(("UCX_", "SOCKET_"))):
            o.hide_render = True
        if o.type == "EMPTY":
            o.hide_render = True
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.render.film_transparent = False
    sh = sc.display.shading
    sh.light = "FLAT"
    sh.color_type = "SINGLE"
    sh.single_color = (0.0, 0.0, 0.0)
    sh.show_backface_culling = True
    sh.show_cavity = False
    sh.show_shadows = False
    sh.background_type = "WORLD"
    w = sc.world or bpy.data.worlds.new("m")
    sc.world = w
    w.color = (1.0, 1.0, 1.0)
    sc.view_settings.view_transform = "Standard"
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(out)
    px = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4)[::-1, :, 0]  # top row first
    outside = px > 0.5
    H, W = outside.shape
    res = {"outside_pct": round(100.0 * outside.mean(), 1)}
    tops = []
    for x in range(int(W * 0.2), int(W * 0.8)):
        col = outside[:, x]
        ys = np.nonzero(col[H // 2:][::-1])[0]            # from the bottom up, lower half only
        tops.append(100.0 * ys[0] / H if len(ys) else 50.0)
    res["dash_top_pct"] = round(float(np.median(tops)), 1)
    widest = 0
    for y in range(int(H * 0.05), int(H * 0.6), 6):
        row = outside[y]
        x = 0
        while x < W:
            if not row[x]:
                x0 = x
                while x < W and not row[x]:
                    x += 1
                if x0 > 0 and x < W:
                    widest = max(widest, x - x0)
            else:
                x += 1
    res["widest_pillar_pct"] = round(100.0 * widest / W, 1)
    half = math.degrees(math.atan(math.tan(math.radians(fov / 2))))
    band = int(W / 2 * math.tan(math.radians(15)) / math.tan(math.radians(fov / 2)))
    res["pillar_in_15deg"] = bool((~outside[H // 2, W // 2 - band:W // 2 + band]).any())
    print("EYEVIEW " + json.dumps(res))


main()
