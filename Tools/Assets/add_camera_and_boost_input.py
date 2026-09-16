"""Adds IA_ToggleCamera and IA_Boost and maps them in the existing IMC_Spaceship.

Run with the editor closed:
    .\Tools\run_editor_python.ps1 Tools\Assets\add_camera_and_boost_input.py

Safe to re-run: existing actions are left as they are and add_mappings() skips mappings
that are already present. The 14 hand-authored flight mappings are never modified.
"""

import unreal

import gamespace_assets as ga

INPUT = "/Game/Input"

# Pressed on the action itself: the camera toggles once per key press, whatever key is bound.
toggle_camera = ga.input_action(INPUT + "/IA_ToggleCamera", "bool", triggers=["Pressed"], on_exists="skip")

# No trigger: Triggered fires every frame while held and Completed on release, which is what
# a hold-to-boost needs.
boost = ga.input_action(INPUT + "/IA_Boost", "bool", on_exists="skip")

added = ga.add_mappings(INPUT + "/IMC_Spaceship", [
    ga.Map(toggle_camera, "C"),
    ga.Map(boost, "LeftShift"),
])
unreal.log("add_camera_and_boost_input: %d mapping(s) added to IMC_Spaceship" % added)
