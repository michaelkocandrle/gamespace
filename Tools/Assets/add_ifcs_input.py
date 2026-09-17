"""IFCS keys for the ship: master modes, speed limiter, G-Safe, ComStab (SC-1a), afterburner (SC-1b).

Editor closed:

    .\\Tools\\run_editor_python.ps1 Tools\\Assets\\add_ifcs_input.py

Creates the actions and appends their keys to the hand-authored IMC_Spaceship with
add_mappings(), which never touches the existing mappings. Safe to re-run.

    IA_MasterMode    bool    B               SCM / NAV
    IA_SpeedLimiter  axis1d  MouseWheelAxis  speed limiter (Alt + wheel stays camera zoom)
    IA_GSafe         bool    K               G-Safe on / off
    IA_ComStab       bool    L               ComStab on / off
    IA_Afterburner   bool    Tab             afterburner, held (SC-1b)

The wheel stays mapped to IA_CameraZoom as well; the ship picks one by whether Alt is held.
X (IA_AllStop) is now the spacebrake, held; its asset needs no change.
Without this script the ship maps the same keys at runtime (SpaceshipPawn's extras context).
"""

import unreal

import gamespace_assets as ga

INPUT = "/Game/Input"

master_mode = ga.input_action(INPUT + "/IA_MasterMode", "bool", on_exists="skip")
limiter = ga.input_action(INPUT + "/IA_SpeedLimiter", "axis1d", on_exists="skip")
gsafe = ga.input_action(INPUT + "/IA_GSafe", "bool", on_exists="skip")
comstab = ga.input_action(INPUT + "/IA_ComStab", "bool", on_exists="skip")
afterburner = ga.input_action(INPUT + "/IA_Afterburner", "bool", on_exists="skip")

added = ga.add_mappings(INPUT + "/IMC_Spaceship", [
    ga.Map(master_mode, "B"),
    ga.Map(limiter, "MouseWheelAxis"),
    ga.Map(gsafe, "K"),
    ga.Map(comstab, "L"),
    ga.Map(afterburner, "Tab"),
])
unreal.log("add_ifcs_input: %d mapping(s) added to IMC_Spaceship" % added)
