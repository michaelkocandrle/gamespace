"""Flight modes for the ship: flight assist, all stop and camera zoom.

Editor closed:

    .\\Tools\\run_editor_python.ps1 Tools\\Assets\\add_flight_modes_input.py

Creates the actions and appends their keys to the hand-authored IMC_Spaceship with
add_mappings(), which never touches the existing mappings. Safe to re-run.

    IA_FlightAssist  bool    V               flight assist on / off
    IA_AllStop       bool    X               throttle lever to 0
    IA_CameraZoom    axis1d  MouseWheelAxis  chase camera distance, cockpit zoom

Without this script the ship maps the same keys at runtime (SpaceshipPawn's extras context);
with it they show up in the IMC and can be rebound there. The cruise drive (J) it used to add
was replaced by the quantum drive (Tools/Assets/add_quantum_input.py).
"""

import unreal

import gamespace_assets as ga

INPUT = "/Game/Input"

flight_assist = ga.input_action(INPUT + "/IA_FlightAssist", "bool", on_exists="skip")
all_stop = ga.input_action(INPUT + "/IA_AllStop", "bool", on_exists="skip")
zoom = ga.input_action(INPUT + "/IA_CameraZoom", "axis1d", on_exists="skip")

added = ga.add_mappings(INPUT + "/IMC_Spaceship", [
    ga.Map(flight_assist, "V"),
    ga.Map(all_stop, "X"),
    ga.Map(zoom, "MouseWheelAxis"),
])
unreal.log("add_flight_modes_input: %d mapping(s) added to IMC_Spaceship" % added)
