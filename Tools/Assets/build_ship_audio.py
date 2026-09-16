"""Imports the placeholder engine loop as /Game/Ships/Audio/SW_EngineLoop.

Two steps, editor closed:

    python Tools/Assets/generate_engine_sound.py Intermediate/GeneratedAssets/engine_loop.wav
    .\\Tools\\run_editor_python.ps1 Tools\\Assets\\build_ship_audio.py

SpaceshipPawn loads the sound from that path and drives its volume and pitch from throttle.
To swap in a real recording later, reimport a looping mono WAV onto the same asset.
Re-running reimports the generated file in place.
"""

import os

import unreal

import gamespace_assets as ga

SOUND = "/Game/Ships/Audio/SW_EngineLoop"
GENERATED = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_intermediate_dir()), "GeneratedAssets")

wav = os.path.join(GENERATED, "engine_loop.wav")
if not os.path.isfile(wav):
    raise RuntimeError("%s missing - run Tools/Assets/generate_engine_sound.py first" % wav)

sound = ga.import_file(SOUND, wav, on_exists="update", properties={"looping": True})
if not isinstance(sound, unreal.SoundWave):
    raise RuntimeError("%s imported as %s, expected SoundWave" % (SOUND, sound.get_class().get_name()))
unreal.log("build_ship_audio: %s, %.1f s, looping=%s" % (
    sound.get_path_name(), sound.get_editor_property("duration"), sound.get_editor_property("looping")))
