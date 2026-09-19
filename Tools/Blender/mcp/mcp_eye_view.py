"""Blender MCP helpers for the live-viewport workflow, see Docs/WORKFLOW.md (chapter Blender MCP)."""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_socket import send

CODE = r'''
import bpy, math
from mathutils import Euler, Vector
scene = bpy.context.scene
cam = bpy.data.objects.get("EyeCam")
if cam is None:
    cam = bpy.data.objects.new("EyeCam", bpy.data.cameras.new("EyeCam"))
    scene.collection.objects.link(cam)
cam.data.sensor_fit = "HORIZONTAL"; cam.data.angle = math.radians(88); cam.data.clip_start = 0.05
cam.location = (1.74, 0.0, 1.89)
cam.rotation_euler = Euler((math.radians(90), 0, math.radians(-90)), "XYZ")
scene.camera = cam
for o in bpy.data.objects:
    if o.name.startswith(("UCX_", "SOCKET_")) or o.type == "EMPTY":
        o.hide_set(True)
# Unreal culls back faces: do the same in the viewport.
for m in bpy.data.materials:
    m.use_backface_culling = True
for area in bpy.context.screen.areas:
    if area.type == "VIEW_3D":
        space = area.spaces.active
        space.shading.type = "MATERIAL"
        space.overlay.show_overlays = False
        space.region_3d.view_perspective = "CAMERA"
        space.lens = 50
        with bpy.context.temp_override(area=area, region=[r for r in area.regions if r.type == "WINDOW"][0]):
            bpy.ops.view3d.view_center_camera()
result = "eye view ready"
'''
print(send("execute_code", {"code": CODE}))
shot = send("get_viewport_screenshot", {"max_size": 1600, "filepath": sys.argv[1], "format": "png"})
print(json.dumps(shot)[:300])
