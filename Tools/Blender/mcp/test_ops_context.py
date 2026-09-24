"""Exercises ops_context.run_op on a throwaway scene and prints one line per operator.

Headless:  MSYS_NO_PATHCONV=1 blender -b --factory-startup --python Tools/Blender/mcp/test_ops_context.py
Over MCP:  exec(open(r"C:\\gamespace\\gamespace\\Tools\\Blender\\mcp\\test_ops_context.py").read())
The scene objects are named OPS_TEST_* and removed at the end; nothing else is touched or saved.
Each line: OPSTEST <operator> OK|FAIL|SKIP <detail>.
"""
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.join(r"C:\gamespace\gamespace\Tools\Blender\mcp"))
import importlib  # noqa: E402

import ops_context  # noqa: E402

importlib.reload(ops_context)
from ops_context import OpsContextError, edit_mode, find_view3d, run_op  # noqa: E402

results = []


def cube(name, size=1.0, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=size)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    bpy.context.scene.collection.objects.link(ob)
    return ob


def faces(ob):
    return len(ob.data.polygons)


def check(label, fn):
    try:
        detail = fn()
        results.append((label, "OK", detail))
    except OpsContextError as ex:
        results.append((label, "SKIP", str(ex)))
    except Exception as ex:  # noqa: BLE001
        results.append((label, "FAIL", "%s: %s" % (type(ex).__name__, ex)))


def t_join():
    a, b = cube("OPS_TEST_A"), cube("OPS_TEST_B", loc=(3, 0, 0))
    run_op("object.join", active=a, selected=[a, b])
    assert "OPS_TEST_B" not in bpy.data.objects and faces(a) == 12, faces(a)
    return "2 cubes -> 1 object, %d faces" % faces(a)


def t_modifier_apply():
    ob = cube("OPS_TEST_MOD")
    mod = ob.modifiers.new("Bevel", "BEVEL")
    mod.width, mod.segments = 0.1, 2
    run_op("object.modifier_apply", active=ob, selected=[ob], modifier=mod.name)
    assert not ob.modifiers and faces(ob) > 6
    return "bevel modifier applied, %d faces" % faces(ob)


def t_bevel_profile():
    ob = cube("OPS_TEST_BEVEL")
    with edit_mode(ob):
        run_op("mesh.select_all", active=ob, action="SELECT")
        run_op("mesh.bevel", active=ob, offset=0.1, segments=3, profile=0.8, affect="EDGES")
    assert faces(ob) > 6
    return "edge bevel 3 segments profile 0.8, %d faces" % faces(ob)


def t_boolean():
    a, cutter = cube("OPS_TEST_BOOL"), cube("OPS_TEST_CUTTER", size=0.6, loc=(0.5, 0.5, 0.5))
    mod = a.modifiers.new("Bool", "BOOLEAN")
    mod.operation, mod.object, mod.solver = "DIFFERENCE", cutter, "EXACT"
    run_op("object.modifier_apply", active=a, selected=[a], modifier=mod.name)
    assert faces(a) > 6
    return "EXACT difference applied, %d faces" % faces(a)


def t_inset():
    ob = cube("OPS_TEST_INSET")
    with edit_mode(ob):
        run_op("mesh.select_all", active=ob, action="SELECT")
        run_op("mesh.inset", active=ob, thickness=0.1, depth=0.02, use_individual=True)
    assert faces(ob) == 30, faces(ob)
    return "individual inset, %d faces" % faces(ob)


def t_knife_project():
    ob = cube("OPS_TEST_KNIFE", size=2.0)
    # The cutter needs wire or boundary edges: a flat square, not a closed cube.
    me = bpy.data.meshes.new("OPS_TEST_KNIFE_CUT")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.4)
    bm.to_mesh(me)
    bm.free()
    cutter = bpy.data.objects.new("OPS_TEST_KNIFE_CUT", me)
    cutter.location = (0, 0, 3)
    bpy.context.scene.collection.objects.link(cutter)
    found = find_view3d()
    if found:
        # Look straight down so the cutter projects onto the top face.
        rv3d = found[1].spaces.active.region_3d
        rv3d.view_perspective = "ORTHO"
        rv3d.view_rotation = (1, 0, 0, 0)
        rv3d.view_location = (0, 0, 0)
        rv3d.view_distance = 10
        rv3d.update()
    before = faces(ob)
    for o in bpy.context.view_layer.objects:
        o.select_set(o in (ob, cutter))
    with edit_mode(ob):
        cutter.select_set(True)
        run_op("mesh.select_all", active=ob, action="SELECT")
        run_op("mesh.knife_project", active=ob, selected=[ob, cutter], cut_through=False)
    assert faces(ob) > before, (before, faces(ob))
    return "cut %d -> %d faces" % (before, faces(ob))


def cleanup():
    for ob in [o for o in bpy.data.objects if o.name.startswith("OPS_TEST_")]:
        me = ob.data
        bpy.data.objects.remove(ob)
        if me and me.users == 0:
            bpy.data.meshes.remove(me)


if bpy.context.object and bpy.context.object.mode != "OBJECT":
    bpy.ops.object.mode_set(mode="OBJECT")
cleanup()
print("OPSTEST context:", "viewport" if find_view3d() else "headless (no window)")
for label, fn in [("object.join", t_join), ("object.modifier_apply", t_modifier_apply),
                  ("mesh.bevel (profile)", t_bevel_profile), ("boolean (modifier_apply)", t_boolean),
                  ("mesh.inset", t_inset), ("mesh.knife_project", t_knife_project)]:
    check(label, fn)
cleanup()
for label, status, detail in results:
    print("OPSTEST %s %s %s" % (label, status, detail))
