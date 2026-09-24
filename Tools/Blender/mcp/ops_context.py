"""Run Blender operators with a proper context, from the MCP socket or a headless script.

Operators fail with "poll() failed, context is incorrect" over MCP because the code runs from a
timer or socket handler, outside any window. This helper finds a window with a 3D view and runs the
operator inside bpy.context.temp_override(window, area, region, ...), with the objects to act on.

Headless (blender -b) there are no windows. Operators that only need objects (object.join,
object.modifier_apply, mesh.bevel, mesh.inset...) still run with an object-only override; the ones
that need a real view (mesh.knife_project and anything projecting from the viewport) raise
OpsContextError with a clear message instead of a vague poll() failure.

    import sys; sys.path.insert(0, r"C:\\gamespace\\gamespace\\Tools\\Blender\\mcp")
    from ops_context import run_op, edit_mode
    run_op("object.join", active=hull, selected=[hull, fin])
    with edit_mode(panel):
        run_op("mesh.select_all", action="SELECT")
        run_op("mesh.bevel", offset=0.02, segments=3, profile=0.7)
"""
import contextlib

import bpy

# Operators that project from the viewport: no sensible headless stand-in.
NEEDS_VIEW = {"mesh.knife_project", "view3d.", "mesh.loopcut_slide", "transform."}


class OpsContextError(RuntimeError):
    pass


def find_view3d():
    """(window, area, region) of the first 3D viewport, or None when there is none (headless).

    blender -b still has the startup file's window and areas, but they are never drawn, so their
    view matrices are empty: operators that project from the view silently do nothing there."""
    if bpy.app.background:
        return None
    wm = bpy.context.window_manager
    for window in (wm.windows if wm else []):
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                region = next((r for r in area.regions if r.type == "WINDOW"), None)
                if region:
                    return window, area, region
    return None


def _resolve(op_id):
    module, name = op_id.split(".", 1)
    return getattr(getattr(bpy.ops, module), name)


def override(active=None, selected=None, view=True):
    """The keyword dict for temp_override: viewport (if any) plus the objects to act on."""
    kw = {}
    if view:
        found = find_view3d()
        if found is None and bpy.app.background:
            # The undrawn startup window still gives window-level operators (mode_set) a home.
            wm = bpy.context.window_manager
            win = wm.windows[0] if wm and wm.windows else None
            area = next((a for a in win.screen.areas if a.type == "VIEW_3D"), None) if win else None
            region = next((r for r in area.regions if r.type == "WINDOW"), None) if area else None
            found = (win, area, region) if region else None
        if found:
            kw["window"], kw["area"], kw["region"] = found
    if active is not None:
        kw["active_object"] = active
        kw["object"] = active
        kw["edit_object"] = active if active.mode == "EDIT" else None
    if selected is not None:
        kw["selected_objects"] = list(selected)
        kw["selected_editable_objects"] = list(selected)
    return {k: v for k, v in kw.items() if v is not None}


def run_op(op_id, active=None, selected=None, **props):
    """Runs bpy.ops.<op_id>(**props) with a working context and returns its result set.

    active / selected: the objects the operator should see as active and selected (the real
    selection is set too, since some operators read select_get() instead of the context)."""
    if any(op_id.startswith(p) for p in NEEDS_VIEW) and find_view3d() is None:
        raise OpsContextError("%s needs a 3D viewport; headless there is none - use bmesh, or run it "
                              "through MCP with Blender's GUI open" % op_id)
    if selected is not None:
        for ob in bpy.context.view_layer.objects:
            ob.select_set(ob in selected)
    if active is not None:
        bpy.context.view_layer.objects.active = active
    op = _resolve(op_id)
    with bpy.context.temp_override(**override(active, selected)):
        if not op.poll():
            raise OpsContextError("%s: poll() failed even with the override (mode %s, active %s)"
                                  % (op_id, bpy.context.mode, getattr(active, "name", None)))
        return op(**props)


@contextlib.contextmanager
def edit_mode(obj):
    """Edit mode on obj for mesh operators, back to object mode afterwards (also on errors)."""
    for ob in bpy.context.view_layer.objects:
        ob.select_set(ob == obj)
    bpy.context.view_layer.objects.active = obj
    with bpy.context.temp_override(**override(obj, [obj])):
        bpy.ops.object.mode_set(mode="EDIT")
    try:
        yield obj
    finally:
        with bpy.context.temp_override(**override(obj, [obj])):
            bpy.ops.object.mode_set(mode="OBJECT")
