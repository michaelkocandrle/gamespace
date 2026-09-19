"""Cockpit display keys: the MFDs' pages and the dashboard focus.

Editor closed:

    .\\Tools\\run_editor_python.ps1 Tools\\Assets\\add_mfd_input.py

Creates the actions and appends their keys to the hand-authored IMC_Spaceship with
add_mappings(), which never touches the existing mappings. Safe to re-run.

    IA_MfdLeft   bool  F1 (and [)  the left MFD's next page (Alt+F1 the previous one)
    IA_MfdRight  bool  F2 (and ])  the right MFD's next page (Alt+F2 the previous one)
    IA_DashboardFocus bool  Z, middle mouse button (held)  lean in to the dashboard's displays

F1 / F2 because [ and ] are not keys of their own on a Czech keyboard (the author's: the key right of
P types "u with an acute"); [ and ] stay for a US keyboard. Config/DefaultInput.ini drops the engine's
debug views on F1 / F2. Alt, not Shift, goes back: Shift is the boost. Without this script the ship
maps F1 / F2 at runtime (SpaceshipPawn's extras context).
"""

import unreal

import gamespace_assets as ga

INPUT = "/Game/Input"

left = ga.input_action(INPUT + "/IA_MfdLeft", "bool", on_exists="skip")
right = ga.input_action(INPUT + "/IA_MfdRight", "bool", on_exists="skip")
focus = ga.input_action(INPUT + "/IA_DashboardFocus", "bool", on_exists="skip")

added = ga.add_mappings(INPUT + "/IMC_Spaceship", [
    ga.Map(left, "F1"),
    ga.Map(right, "F2"),
    ga.Map(left, "LeftBracket"),
    ga.Map(right, "RightBracket"),
    ga.Map(focus, "Z"),
    ga.Map(focus, "MiddleMouseButton"),
])
unreal.log("add_mfd_input: %d mapping(s) added to IMC_Spaceship" % added)
