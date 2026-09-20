"""VTOL (SC-2b): the key that stands the ship on its lift thrusters.

Editor closed:

    .\\Tools\\run_editor_python.ps1 Tools\\Assets\\add_vtol_input.py

Creates the action and appends its key to the hand-authored IMC_Spaceship with add_mappings(),
which never touches the existing mappings. Safe to re-run.

    IA_Vtol  bool  G  VTOL on / off (SCM only)

G because it sits next to the landing keys the ship already uses (N gear, P precision) and is free
on a Czech keyboard. Without this script the ship maps G at runtime (SpaceshipPawn's extras context),
so the key works either way; the asset is what makes it show up in a rebindable list later.
"""

import unreal

import gamespace_assets as ga

INPUT = "/Game/Input"

vtol = ga.input_action(INPUT + "/IA_Vtol", "bool", on_exists="skip")
added = ga.add_mappings(INPUT + "/IMC_Spaceship", [ga.Map(vtol, "G")])
unreal.log("add_vtol_input: %d mapping(s) added to IMC_Spaceship" % added)
