"""Input for the player on foot, and F to get out of the ship.

Editor closed:

    .\\Tools\\run_editor_python.ps1 Tools\\Assets\\add_character_input.py

Creates (skipped when they exist):
    IA_CharMove    Axis2D   W/S -> Y, D/A -> X
    IA_CharLook    Axis2D   mouse
    IA_CharJump    bool     Space
    IA_CharSprint  bool     Left Shift (held)
    IA_Interact    bool     F (Pressed)
    IMC_Character  the mappings above

and appends F -> IA_Interact to the hand-authored IMC_Spaceship with add_mappings(), which
never touches the existing mappings. Safe to re-run.
"""

import unreal

import gamespace_assets as ga

INPUT = "/Game/Input"

move = ga.input_action(INPUT + "/IA_CharMove", "axis2d", accumulation="cumulative", on_exists="skip")
look = ga.input_action(INPUT + "/IA_CharLook", "axis2d", on_exists="skip")
jump = ga.input_action(INPUT + "/IA_CharJump", "bool", on_exists="skip")
sprint = ga.input_action(INPUT + "/IA_CharSprint", "bool", on_exists="skip")
# Pressed on the action: one interaction per key press however long F is held.
interact = ga.input_action(INPUT + "/IA_Interact", "bool", triggers=["Pressed"], on_exists="skip")

if ga.existing_or_none(INPUT + "/IMC_Character") is None:
    ga.mapping_context(INPUT + "/IMC_Character", [
        ga.Map(move, "W", swizzle="YXZ"),
        ga.Map(move, "S", swizzle="YXZ", negate=True),
        ga.Map(move, "D"),
        ga.Map(move, "A", negate=True),
        ga.Map(look, "Mouse2D"),
        ga.Map(jump, "SpaceBar"),
        ga.Map(sprint, "LeftShift"),
        ga.Map(interact, "F"),
    ], description="Player on foot")
    unreal.log("add_character_input: created IMC_Character")
else:
    unreal.log("add_character_input: IMC_Character exists, left as it is")

added = ga.add_mappings(INPUT + "/IMC_Spaceship", [ga.Map(interact, "F")])
unreal.log("add_character_input: %d mapping(s) added to IMC_Spaceship" % added)
