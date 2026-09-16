"""Adds IA_LookMouse and IMC_SpaceshipMouse for frame-rate independent mouse steering.

Run with the editor closed:
    .\\Tools\\run_editor_python.ps1 Tools\\Assets\\add_mouse_look_input.py

Why a separate action and context: IA_Look carries both the gamepad stick (a position in
[-1, 1]) and the mouse (pixels moved this frame). The pawn must treat those differently, but an
action value does not say which key produced it. IMC_SpaceshipMouse maps the mouse to its own
action and is added one priority above IMC_Spaceship, so it consumes the mouse there: IA_Look
then only ever sees the stick. IMC_Spaceship itself is not modified.

Safe to re-run: both assets are skipped if they already exist.
"""

import unreal

import gamespace_assets as ga

INPUT = "/Game/Input"

mouse_look = ga.input_action(INPUT + "/IA_LookMouse", "axis2d", on_exists="skip")
ga.mapping_context(INPUT + "/IMC_SpaceshipMouse", [ga.Map(mouse_look, "Mouse2D")],
                   description="Mouse steering, above IMC_Spaceship", on_exists="skip")
unreal.log("add_mouse_look_input: done")
