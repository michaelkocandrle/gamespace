"""Landing keys for the ship (SC-2a): landing gear and precision mode.

Editor closed:

    .\Tools\run_editor_python.ps1 Tools\Assets\add_landing_input.py

Creates the actions and appends their keys to the hand-authored IMC_Spaceship with
add_mappings(), which never touches the existing mappings. Safe to re-run.

    IA_LandingGear  bool  N  gear down / up (down also switches precision mode on, up off)
    IA_Precision    bool  P  precision mode on / off by hand

Without this script the ship maps the same keys at runtime (SpaceshipPawn's extras context).
"""

import unreal

import gamespace_assets as ga

INPUT = "/Game/Input"

gear = ga.input_action(INPUT + "/IA_LandingGear", "bool", on_exists="skip")
precision = ga.input_action(INPUT + "/IA_Precision", "bool", on_exists="skip")

added = ga.add_mappings(INPUT + "/IMC_Spaceship", [
    ga.Map(gear, "N"),
    ga.Map(precision, "P"),
])
unreal.log("add_landing_input: %d mapping(s) added to IMC_Spaceship" % added)
