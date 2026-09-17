"""Imports the placeholder sounds: ship sounds into /Game/Ships/Audio, menu sounds into /Game/UI/Audio.

Two steps, editor closed:

    python Tools/Assets/generate_ship_sounds.py Intermediate/GeneratedAssets
    .\Tools\run_editor_python.ps1 Tools\Assets\build_ship_audio.py

SpaceshipPawn loads the sounds from these paths (see its Audio properties) and mixes the loops
from what the ship does. To swap in real recordings later, reimport a mono WAV onto the same
asset: loops must loop seamlessly, one-shots should start at once.
Re-running reimports the generated files in place.
"""

import os

import unreal

import gamespace_assets as ga

FOLDER = "/Game/Ships/Audio"
UI_FOLDER = "/Game/UI/Audio"
GENERATED = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_intermediate_dir()), "GeneratedAssets")

# asset name, generated file, looping
SOUNDS = (
    ("SW_EngineLoop", "engine_loop.wav", True),
    ("SW_EngineHum", "engine_hum.wav", True),
    ("SW_BoostLoop", "boost_loop.wav", True),
    ("SW_CruiseLoop", "cruise_loop.wav", True),
    ("SW_BoostStart", "boost_start.wav", False),
    ("SW_CruiseCharge", "cruise_charge.wav", False),
    ("SW_CruiseEngage", "cruise_engage.wav", False),
    ("SW_CruiseDrop", "cruise_drop.wav", False),
    ("SW_Touchdown", "touchdown.wav", False),
    (UI_FOLDER + "/SW_UiHover", "ui_hover.wav", False),
    (UI_FOLDER + "/SW_UiConfirm", "ui_confirm.wav", False),
    (UI_FOLDER + "/SW_MenuAmbience", "menu_ambience.wav", True),
)

missing = [f for _, f, _ in SOUNDS if not os.path.isfile(os.path.join(GENERATED, f))]
if missing:
    raise RuntimeError("missing %s in %s - run Tools/Assets/generate_ship_sounds.py first" % (", ".join(missing), GENERATED))

for name, source, looping in SOUNDS:
    path = name if name.startswith("/") else "%s/%s" % (FOLDER, name)
    sound = ga.import_file(path, os.path.join(GENERATED, source), on_exists="update", properties={"looping": looping})
    if not isinstance(sound, unreal.SoundWave):
        raise RuntimeError("%s imported as %s, expected SoundWave" % (path, sound.get_class().get_name()))
    unreal.log("build_ship_audio: %s, %.1f s, looping=%s" % (
        sound.get_path_name(), sound.get_editor_property("duration"), sound.get_editor_property("looping")))
