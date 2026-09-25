"""The pilot's eye view of a ship's cockpit in Blender, as the game frames it (see Docs/WORKFLOW.md, Blender MCP).

    python Tools/Blender/mcp/mcp_eye_view.py out.png                      live Blender over MCP (port 9876)
    python Tools/Blender/mcp/mcp_eye_view.py out.png --headless [--ship Wayfarer] [--displays on|off] [--look clay|material]

The eye and the field of view come from the ship's data, so the view matches the cockpit camera in the game:
SOCKET_Cockpit in ArtSource/Ships/<Ship>/Export/<Ship>_manifest.json (metres, mesh space of the game blend)
and components.cockpit_camera.field_of_view (horizontal) plus pawn.cockpit_view_pitch_deg in <Ship>_setup.json.
Unreal culls back faces, so the view does too (a hull seen from inside shows what is behind it).

--headless renders <Ship>_HS_Game.blend with Blender in the background (no live Blender needed), 1920x1080:
  clay      Workbench, one matt grey, studio light and cavity - shapes only (a structural base for concepts)
  material  Workbench with the materials' viewport colours
  --displays on   the four screen quads (slot *_Screens) glow a flat blue-white, where the game draws its MFDs
  --displays off  the screens are dark like the rest
The canopy glass is hidden (it would be an opaque clay sheet).
"""
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"


def eye_of(ship):
    manifest = json.load(open(os.path.join(REPO, "ArtSource", "Ships", ship, "Export", "%s_manifest.json" % ship), encoding="utf-8"))
    setup = json.load(open(os.path.join(REPO, "ArtSource", "Ships", ship, "%s_setup.json" % ship), encoding="utf-8"))
    sockets = manifest["sockets"]
    eye = sockets["SOCKET_Cockpit"]["location_m"]
    fov = setup.get("components", {}).get("cockpit_camera", {}).get("field_of_view", 88.0)
    pitch = setup.get("pawn", {}).get("cockpit_view_pitch_deg", 0.0)
    return eye, fov, pitch


CAMERA = r'''
import bpy, math
from mathutils import Euler
scene = bpy.context.scene
cam = bpy.data.objects.get("EyeCam")
if cam is None:
    cam = bpy.data.objects.new("EyeCam", bpy.data.cameras.new("EyeCam"))
    scene.collection.objects.link(cam)
cam.data.sensor_fit = "HORIZONTAL"; cam.data.angle = math.radians(FOV); cam.data.clip_start = 0.05
cam.location = EYE
# Blender cameras look down -Z: pitch 90 looks along +Y, yaw -90 turns that to +X (the nose)
cam.rotation_euler = Euler((math.radians(90 + PITCH), 0, math.radians(-90)), "XYZ")
scene.camera = cam
for o in bpy.data.objects:
    if o.name.startswith(("UCX_", "SOCKET_")) or o.type == "EMPTY":
        o.hide_set(True)
        o.hide_render = True
for m in bpy.data.materials:
    m.use_backface_culling = True
'''

LIVE = r'''
for area in bpy.context.screen.areas:
    if area.type == "VIEW_3D":
        space = area.spaces.active
        space.shading.type = "MATERIAL"
        space.overlay.show_overlays = False
        space.region_3d.view_perspective = "CAMERA"
        with bpy.context.temp_override(area=area, region=[r for r in area.regions if r.type == "WINDOW"][0]):
            bpy.ops.view3d.view_center_camera()
result = "eye view ready"
'''

HEADLESS = r'''
import sys
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
sh = scene.display.shading
sh.light = "STUDIO"
sh.color_type = "SINGLE" if LOOK == "clay" else "MATERIAL"
sh.single_color = (0.62, 0.62, 0.6)
sh.show_cavity = True
sh.cavity_type = "BOTH"
sh.show_backface_culling = True
sh.show_shadows = True
sh.shadow_intensity = 0.35
scene.display.shadow_focus = 0.5
sh.background_type = "VIEWPORT" if False else "WORLD"
world = scene.world or bpy.data.worlds.new("eye")
scene.world = world
world.color = (0.55, 0.6, 0.66)
scene.view_settings.view_transform = "Standard"
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    if o.name.endswith("_Canopy") or any(s.material and "Glass" in s.material.name for s in o.material_slots):
        o.hide_render = True
screens = [o for o in bpy.data.objects if o.type == "MESH" and any(s.material and s.material.name.endswith("_Screens") for s in o.material_slots)]
if DISPLAYS:
    # the screens glow: a separate emissive-looking colour in material mode, a bright flat patch in clay mode
    for o in screens:
        for s in o.material_slots:
            if s.material and s.material.name.endswith("_Screens"):
                s.material.diffuse_color = (0.55, 0.8, 1.0, 1.0)
    if LOOK == "clay":
        sh.color_type = "MATERIAL"
        for m in bpy.data.materials:
            if not m.name.endswith("_Screens"):
                m.diffuse_color = (0.62, 0.62, 0.6, 1.0)
scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("EYEVIEW", OUT)
'''


def main():
    args = sys.argv[1:]
    out = os.path.abspath(args[0])
    opt = lambda name, default: args[args.index(name) + 1] if name in args else default
    ship = opt("--ship", "Wayfarer")
    eye, fov, pitch = eye_of(ship)
    code = CAMERA.replace("EYE", repr(tuple(eye))).replace("FOV", repr(float(fov))).replace("PITCH", repr(float(pitch)))
    if "--headless" not in args:
        sys.path.insert(0, HERE)
        from mcp_socket import send
        print(send("execute_code", {"code": code + LIVE}))
        shot = send("get_viewport_screenshot", {"max_size": 1600, "filepath": out, "format": "png"})
        print(json.dumps(shot)[:300])
        return
    look = opt("--look", "clay")
    displays = opt("--displays", "on") == "on"
    script = os.path.join(os.path.dirname(out), "_eye_view_run.py")
    with open(script, "w", encoding="utf-8") as fh:
        fh.write(code + HEADLESS.replace("LOOK", repr(look)).replace("DISPLAYS", repr(displays)).replace("OUT", repr(out)))
    blend = os.path.join(REPO, "ArtSource", "Ships", ship, "%s_HS_Game.blend" % ship)
    run = subprocess.run([BLENDER, "-b", blend, "--python", script], capture_output=True, text=True)
    os.remove(script)
    lines = [l for l in run.stdout.splitlines() if l.startswith("EYEVIEW") or "Error" in l or "Traceback" in l]
    print("\n".join(lines) or run.stdout[-2000:] + run.stderr[-2000:])


if __name__ == "__main__":
    main()
