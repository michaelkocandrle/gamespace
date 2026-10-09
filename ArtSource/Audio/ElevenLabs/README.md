# Ship system sound effects (ElevenLabs Sound Effects 2 via Scenario, 5. 10. 2026)

Generated with the author's Scenario plan (model `model_elevenlabs-sound-effects-v2`, 30 CU each), the generated
audio may be used commercially under that plan (Docs/Credits.md). `*.mp3` = the download, `*.wav` = 48 kHz mono
16-bit made by ffmpeg (5 ms fade in, 30 ms fade out, `dynaudnorm`), imported by `Tools/Assets/build_ship_audio.py`.

| File | Length | Prompt (prompt influence 0.5-0.6) |
| --- | --- | --- |
| power_up | 3.2 s | sci-fi spaceship cockpit power-up: relay clunks, rising reactor spool-up whine, capacitor charge hum, electronics coming alive with soft beeps, ends in a steady low hum |
| power_down | 2.2 s | systems winding down, descending reactor whine, a final relay clunk, electronics hiss dying |
| holo_deploy | 1.3 s | holographic display projecting on: airy electronic shimmer rising, subtle digital crackle, glassy energy sweep, clean lock tone |
| holo_retract | 0.9 s | holographic display switching off: descending shimmer collapsing into a soft digital blip |
| holo_flicker | 0.5 s | short electrical flicker crackle of a hologram projector catching |
| holo_tick | 0.5 s | modern sci-fi touchscreen confirm tick, glassy holographic UI click |
| engine_start | 4.5 s | thruster engines starting up from inside the cockpit: igniter clicks, turbine spool, deep rumble into a steady idle roar |
| engine_stop | 3.5 s | engines shutting down: spool winding down, rumble fading, metallic ticking |
| switch_click | 0.6 s | heavy-duty cockpit toggle switch with a guarded cover: solid metal snap and clack |

## Redone 9. 10. 2026 (the author's choice by ear)

The author: no sound in the game sounded good enough. Two takes per sound from `Tools/Assets/sound_candidates.py`
(ElevenLabs Sound Effects 2, influence 0.7 / 0.5, SC style suffix: physical, mechanical, no music, no beeps, no
notification chime), all kept in `ArtSource/Audio/Candidates/`, chosen on the sound board (`sound_board.py`).
These files replace the 5. 10. ones of the same name; the engine loops are new here (were procedural) and level
matched to the old ones (mean -18 dB, no fades: seamless), the one-shots trimmed of leading silence, faded, `dynaudnorm`.

| File | Take | Prompt |
| --- | --- | --- |
| engine_loop | a | Inside a spaceship cockpit: the main thruster engines running under power, a deep heavy rumbling roar with a low turbine whine layered on top, felt through the hull, steady and powerful, seamless loop. |
| engine_hum | b | Idle spaceship engines heard from inside: warm deep reactor hum with a slow subtle throb, quiet mechanical whir of pumps and fans, hull ambience, seamless loop. |
| engine_start | b | Starting large spacecraft engines heard through the hull: starter motor whirring, rising turbine spool, pressure hiss, a low boom of ignition, then a deep throbbing engine rumble settling to idle. |
| engine_stop | a | Spaceship engines shutting down, heard from the cockpit: the deep rumble cutting off, turbines spooling down with a falling whine, a pressure release hiss, metal ticking as the engines cool. |
| power_up | b | Cockpit power-up of a large spacecraft: thick mechanical switch throw, cascading relay clacks, capacitors charging with a rising tone, ventilation spinning up, settles to a low electrical drone. |
| power_down | b | Cockpit power-down of a large spacecraft: switch thrown, descending electrical drone, ventilation winding down, soft relay clacks fading out. |
| holo_deploy | b | Sci-fi hologram screen materialising from a projector: brief electrical hum swelling with a light airy shimmer and a soft low click at the end, subtle. |
| holo_retract | a | Holographic cockpit display projector turning off: a quick descending glassy shimmer collapsing into a soft low thump, servo whir, subtle and short. |
| holo_tick | a | Pressing a button on a holographic cockpit display: a soft, dry, short tactile tick with a faint low electrical body, subtle and quiet, not a beep, not a notification. |
| switch_click | a | A heavy-duty metal toggle switch in a spaceship cockpit flipped: solid mechanical snap and clack, short and dry, close up. |
| button_press | a | Pressing a backlit physical push button on a spaceship console: a firm, short, muted mechanical click with a soft rubber dampening, close up, no electronic tone. |
