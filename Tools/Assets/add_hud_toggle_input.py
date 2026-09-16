"""HUD toggle: H cycles the debug HUD between compact, full and hidden (CVar space.Hud).

Editor closed:

    .\Tools\run_editor_python.ps1 Tools\Assets\add_hud_toggle_input.py

Creates IA_ToggleHud (bool, Started on press) and appends H -> IA_ToggleHud to the hand-authored
IMC_Spaceship and IMC_Character with add_mappings(), which never touches the existing mappings.
Safe to re-run.
"""

import unreal

import gamespace_assets as ga

INPUT = "/Game/Input"

toggle = ga.input_action(INPUT + "/IA_ToggleHud", "bool", on_exists="skip")
for context in ("IMC_Spaceship", "IMC_Character"):
    added = ga.add_mappings(INPUT + "/" + context, [ga.Map(toggle, "H")])
    unreal.log("add_hud_toggle_input: %d mapping(s) added to %s" % (added, context))
