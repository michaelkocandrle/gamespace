"""The Wayfarer's cargo grid in variants, rendered in the ship (30. 9. 2026, author: "explain the grid's variants with
pictures and what depends on them - floor, ramp, thresholds; I decide").

    blender -b ArtSource/Ships/Wayfarer/Wayfarer_HS_Game.blend --python Tools/Design/hold_grid_variants.py -- <out_dir>

The game blend with the kit rooms put in (check_ship_geometry.add_kit_rooms), today's grid (rails and anchors of
hs_interior.obj_cargo_grid) cut out of the interior mesh and rebuilt per variant, eight containers on it, the free floor
in front of the tech corridor's door green, the quantum drive's floor hatch outlined yellow. A clay render (Workbench,
object colours): a top view with everything over 2 m cut away and three eye-level views (1.65 m). Never saves the blend.
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "Tools", "Blender"))
import check_ship_geometry as geo  # noqa: E402

SHIP = "Wayfarer"
OFF = Vector((-10.25, 0.0, -1.2))           # layout metres -> the game blend (recipe assemble.offset)
GRID_Y = (-1.85, 0.65)                       # across: 5 cm off the starboard liner's frames and L-track (unchanged)
GRID_LEN = 5.0                               # 4 x 1.25 m
SCU = 1.25
DOOR = (8.2, 0.0, 1.0)                       # the tech corridor's door: x, y0, y1 (layout "doors")
HATCH = (1.4, 2.6, -0.8, 0.8)                # the quantum drive's floor hatch (layout "objects", below)
VARIANTS = [("A", 2.9, "dnes: x 2,9-7,9"), ("B", 2.65, "o 0,25 m dozadu: x 2,65-7,65"), ("C", 2.35, "o 0,55 m dozadu: x 2,35-7,35")]
VIEWS = {
    # name: (camera, look at, fov) in layout metres
    "door": ((8.95, 0.5, 1.65), (6.3, -0.3, 0.6), 80.0),        # from the tech corridor, out through the door
    "aisle": ((4.3, 1.55, 1.65), (8.2, 0.35, 0.9), 75.0),       # walking forward to the door
    "ramp": ((1.35, 1.0, 1.65), (5.2, -0.8, 0.3), 85.0),        # just in from the ramp: the landing zone, the drive's hatch
}
COL = {"ship": (0.62, 0.62, 0.6, 1), "kit": (0.7, 0.69, 0.66, 1), "rail": (0.18, 0.18, 0.2, 1), "anchor": (0.85, 0.34, 0.06, 1),
       "box": (0.86, 0.86, 0.83, 1), "band": (0.85, 0.34, 0.06, 1), "free": (0.2, 0.75, 0.3, 1), "hatch": (0.95, 0.8, 0.1, 1)}


def L(p):
    return Vector(p) + OFF


def add_box(bm, lo, hi):
    lo, hi = L(lo), L(hi)
    tmp = bmesh.ops.create_cube(bm, size=1.0)
    for v in tmp["verts"]:
        v.co = Vector((lo.x + (v.co.x + 0.5) * (hi.x - lo.x), lo.y + (v.co.y + 0.5) * (hi.y - lo.y), lo.z + (v.co.z + 0.5) * (hi.z - lo.z)))


def obj_from(name, build, colour):
    bm = bmesh.new()
    build(bm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.color = colour
    bpy.context.scene.collection.objects.link(ob)
    return ob


def cut_todays_grid():
    """Today's rails and anchors out of the interior mesh: faces over the grid's rectangle up to 4.5 cm above the floor,
    the floor itself kept."""
    x0, x1 = 2.9, 7.9
    ob = bpy.data.objects["SM_Ship_%s_Interior" % SHIP]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    mats = [m.name if m else "" for m in ob.data.materials]
    lo, hi = L((x0 - 0.08, GRID_Y[0] - 0.08, -0.001)), L((x1 + 0.08, GRID_Y[1] + 0.08, 0.045))
    mw = ob.matrix_world
    kill = []
    for f in bm.faces:
        if "Floor" in mats[f.material_index]:
            continue
        pts = [mw @ v.co for v in f.verts]
        if all(lo.x <= p.x <= hi.x and lo.y <= p.y <= hi.y and lo.z <= p.z <= hi.z for p in pts):
            kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(ob.data)
    bm.free()
    return len(kill)


def grid(x0):
    """hs_interior.obj_cargo_grid at x0: rails, anchors, the containers, the free floor before the door."""
    x1, (y0, y1) = x0 + GRID_LEN, GRID_Y
    obs = []

    def rails(bm):
        for k in range(5):
            x = x0 + GRID_LEN * k / 4
            add_box(bm, (x - 0.03, y0, 0.0), (x + 0.03, y1, 0.025))
        for k in range(3):
            y = y0 + (y1 - y0) * k / 2
            add_box(bm, (x0, y - 0.03, 0.0), (x1, y + 0.03, 0.025))

    def anchors(bm):
        for k in range(3):
            y = y0 + (y1 - y0) * k / 2
            for i in range(5):
                x = x0 + GRID_LEN * i / 4
                add_box(bm, (x - 0.07, y - 0.07, 0.0), (x + 0.07, y + 0.07, 0.04))

    def boxes(bm, band):
        for i in range(4):
            for j in range(2):
                cx, cy = x0 + SCU * (i + 0.5), y0 + SCU * (j + 0.5)
                if band:
                    add_box(bm, (cx - 0.605, cy - 0.605, 0.55), (cx + 0.605, cy + 0.605, 0.65))
                else:
                    add_box(bm, (cx - 0.6, cy - 0.6, 0.04), (cx + 0.6, cy + 0.6, 1.24))

    def free(bm):
        add_box(bm, (x1 + 0.03, DOOR[1], 0.0), (DOOR[0], DOOR[2], 0.004))

    def hatch(bm):
        a0, a1, b0, b1 = HATCH
        for (p, q) in (((a0, b0), (a1, b0 + 0.03)), ((a0, b1 - 0.03), (a1, b1)), ((a0, b0), (a0 + 0.03, b1)), ((a1 - 0.03, b0), (a1, b1))):
            add_box(bm, (p[0], p[1], 0.0), (q[0], q[1], 0.03))      # over the hatch plate

    obs.append(obj_from("_grid_rails", rails, COL["rail"]))
    obs.append(obj_from("_grid_anchors", anchors, COL["anchor"]))
    obs.append(obj_from("_grid_boxes", lambda bm: boxes(bm, False), COL["box"]))
    obs.append(obj_from("_grid_bands", lambda bm: boxes(bm, True), COL["band"]))
    obs.append(obj_from("_grid_free", free, COL["free"]))
    obs.append(obj_from("_grid_hatch", hatch, COL["hatch"]))
    return obs


def setup_render():
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    sh = sc.display.shading
    sh.light, sh.color_type = "STUDIO", "OBJECT"
    sh.show_shadows, sh.show_cavity = True, True
    sh.cavity_type = "BOTH"
    sh.show_backface_culling = True
    sh.background_type = "WORLD"
    w = sc.world or bpy.data.worlds.new("grid")
    sc.world = w
    w.color = (0.03, 0.03, 0.035)
    sc.view_settings.view_transform = "Standard"
    for o in bpy.data.objects:
        if o.type == "EMPTY" or o.name.startswith(("UCX_", "SOCKET_")):
            o.hide_render = True
        elif o.type == "MESH" and not o.name.startswith("_grid"):
            o.color = COL["kit"] if "KitMod" in o.name else COL["ship"]
            if any(s in o.name for s in ("Canopy", "Glass")):
                o.hide_render = True
    cam = bpy.data.objects.new("_GridCam", bpy.data.cameras.new("_GridCam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.sensor_fit = "HORIZONTAL"
    return sc, cam


def main():
    out_dir = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
    os.makedirs(out_dir, exist_ok=True)
    recipe = json.load(open(os.path.join(ROOT, "ArtSource", "Ships", SHIP, "HardSurface", "%s_hs.json" % SHIP), encoding="utf-8"))
    kit = geo.add_kit_rooms(SHIP, recipe)
    cut = cut_todays_grid()
    sc, cam = setup_render()
    top = {"centre": [4.75, 0.0], "width_m": 9.5}
    report = {"kit": kit, "cut_faces": cut, "top": top, "renders": []}
    for key, x0, label in VARIANTS:
        obs = grid(x0)
        # the top view: orthographic, everything above 2.0 m clipped (ceiling, services, chamfers)
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = top["width_m"]
        cam.location = L((top["centre"][0], top["centre"][1], 12.0))
        cam.rotation_euler = (0.0, 0.0, 0.0)
        cam.data.clip_start, cam.data.clip_end = 10.0, 14.0
        sc.render.filepath = os.path.join(out_dir, "grid_%s_top.png" % key)
        bpy.ops.render.render(write_still=True)
        cam.data.type = "PERSP"
        cam.data.clip_start, cam.data.clip_end = 0.02, 60.0
        for name, (c, t, fov) in VIEWS.items():
            cam.location = L(c)
            cam.rotation_euler = (L(t) - L(c)).to_track_quat("-Z", "Y").to_euler()
            cam.data.angle = math.radians(fov)
            sc.render.filepath = os.path.join(out_dir, "grid_%s_%s.png" % (key, name))
            bpy.ops.render.render(write_still=True)
        report["renders"].append({"variant": key, "x0": x0, "label": label,
                                  "free_before_door_m": round(DOOR[0] - (x0 + GRID_LEN), 2),
                                  "ramp_to_grid_m": round(x0 - 1.0, 2),
                                  "over_drive_hatch_m": round(max(0.0, HATCH[1] - (x0 - 0.03)), 2)})
        for ob in obs:
            bpy.data.objects.remove(ob)
    json.dump(report, open(os.path.join(out_dir, "grid_variants.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("GRIDVARIANTS " + json.dumps(report, ensure_ascii=False))


main()
