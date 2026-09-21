"""Quantum drive (SC-4): the jump button, and the cruise drive's key gone.

Editor closed:

    .\Tools\run_editor_python.ps1 Tools\Assets\add_quantum_input.py

    IA_QuantumEngage  bool  LeftMouseButton  held: quantum jump when the drive is READY (NAV)

Star Citizen jumps on the left mouse button held (the reference video, 4:08). The ship times the
hold itself (QuantumEngageHoldSeconds), so the action has no hold trigger. The cruise drive it
replaces (IA_CruiseDrive on J) is unmapped from IMC_Spaceship and deleted. Safe to re-run.
Without this script the ship maps the left mouse button at runtime (SpaceshipPawn's extras context).
"""

import unreal

import gamespace_assets as ga

INPUT = "/Game/Input"
IMC = INPUT + "/IMC_Spaceship"

engage = ga.input_action(INPUT + "/IA_QuantumEngage", "bool", on_exists="skip")
added = ga.add_mappings(IMC, [ga.Map(engage, "LeftMouseButton")])
unreal.log("add_quantum_input: %d mapping(s) added to %s" % (added, IMC))

cruise = ga.existing_or_none(INPUT + "/IA_CruiseDrive")
if cruise is not None:
    # Edited the way add_mappings does: the IMC keeps its mappings in default_key_mappings (UE 5.8).
    imc = unreal.load_asset(IMC)
    data = imc.get_editor_property("default_key_mappings")
    current = list(data.get_editor_property("mappings"))
    kept = [m for m in current if m.get_editor_property("action") != cruise]
    before, after = len(current), len(kept)
    data.set_editor_property("mappings", kept)
    imc.set_editor_property("default_key_mappings", data)
    unreal.EditorAssetLibrary.save_loaded_asset(imc, only_if_is_dirty=False)
    unreal.log("add_quantum_input: IA_CruiseDrive unmapped (%d -> %d mappings)" % (before, after))
    if not unreal.EditorAssetLibrary.delete_asset(INPUT + "/IA_CruiseDrive"):
        unreal.log_warning("add_quantum_input: could not delete IA_CruiseDrive (still referenced?)")
