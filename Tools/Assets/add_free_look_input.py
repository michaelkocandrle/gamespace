"""Free look for the ship: hold the right mouse button to look around without steering.

Editor closed:

    .\Tools\run_editor_python.ps1 Tools\Assets\add_free_look_input.py

Creates IA_FreeLook (bool, no trigger: Started on press, Completed on release) and appends
RightMouseButton -> IA_FreeLook to the hand-authored IMC_Spaceship with add_mappings(), which
never touches the existing mappings. Safe to re-run.
"""

import unreal

import gamespace_assets as ga

INPUT = "/Game/Input"

free_look = ga.input_action(INPUT + "/IA_FreeLook", "bool", on_exists="skip")
added = ga.add_mappings(INPUT + "/IMC_Spaceship", [ga.Map(free_look, "RightMouseButton")])
unreal.log("add_free_look_input: %d mapping(s) added to IMC_Spaceship" % added)
