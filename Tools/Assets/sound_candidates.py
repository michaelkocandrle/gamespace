"""Sound candidates for the author to choose by ear (author 9. 10. 2026: "no sound in the game sounds good enough -
the engine, the engine start, clicks on the MFD sound like a phone notification, MFD open / close, ship power on /
off"). Each sound gets several takes from text-to-SFX models on Scenario (ElevenLabs Sound Effects 2 at two prompt
wordings, Sonilo 1.1), written to ArtSource/Audio/Candidates/<sound>_<take>.<ext> with candidates.json (prompt,
model, file). The plan allows two jobs at once: this keeps two in flight.

    python Tools/Assets/sound_candidates.py            # generate what is missing
    python Tools/Assets/sound_candidates.py --list     # the specs

Credentials and REST as Tools/Assets/scenario_mcp.py (C:/gamespace/secrets/scenario.key, never in the repository).
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scenario_mcp as sc  # noqa: E402

OUT = os.path.join(sc.ROOT, "ArtSource", "Audio", "Candidates")
EL = "model_elevenlabs-sound-effects-v2"
SO = "model_sonilo-v1-1-text-to-sound-effects"
STYLE = " Cinematic sci-fi game sound like Star Citizen, physical and mechanical, no music, no beeps, no notification chime."

# (sound, seconds, loop, [prompt A, prompt B]) - take a/b: ElevenLabs (influence 0.7 / 0.5), take c: Sonilo on prompt A
SOUNDS = [
    ("engine_loop", 8, True, [
        "Inside a spaceship cockpit: the main thruster engines running under power, a deep heavy rumbling roar with a low turbine whine layered on top, felt through the hull, steady and powerful, seamless loop.",
        "Spaceship engine thrust heard from the pilot seat: massive low-frequency roar of plasma thrusters, rhythmic subtle pulsing, metal hull resonance and vibration, a soft high turbine whistle, dense and mechanical, seamless loop."]),
    ("engine_hum", 8, True, [
        "Spaceship idling, heard in the cockpit: a smooth low reactor drone, faint electrical hum of systems, soft air circulation hiss, calm and steady, very low pitch, seamless loop.",
        "Idle spaceship engines heard from inside: warm deep reactor hum with a slow subtle throb, quiet mechanical whir of pumps and fans, hull ambience, seamless loop."]),
    ("engine_start", 5, False, [
        "Spaceship engines igniting, heard from inside the cockpit: a heavy mechanical clunk of fuel valves, igniter ticking, turbines spooling up with a rising whine, a deep thump as the thrusters catch, building into a powerful steady rumble.",
        "Starting large spacecraft engines heard through the hull: starter motor whirring, rising turbine spool, pressure hiss, a low boom of ignition, then a deep throbbing engine rumble settling to idle."]),
    ("engine_stop", 4, False, [
        "Spaceship engines shutting down, heard from the cockpit: the deep rumble cutting off, turbines spooling down with a falling whine, a pressure release hiss, metal ticking as the engines cool.",
        "Large spacecraft thrusters powering down: falling turbine whine, rumble fading out, a heavy valve clunk, then quiet creaks of cooling metal."]),
    ("power_up", 3.5, False, [
        "Spaceship systems powering on in the cockpit: a heavy main breaker clunk, relays clicking in sequence, a rising electrical hum as power flows through the ship, fans starting, ending in a steady low hum.",
        "Cockpit power-up of a large spacecraft: thick mechanical switch throw, cascading relay clacks, capacitors charging with a rising tone, ventilation spinning up, settles to a low electrical drone."]),
    ("power_down", 3, False, [
        "Spaceship systems powering off in the cockpit: a heavy breaker clunk, electrical hum falling and dying, fans spinning down, a last relay click, silence.",
        "Cockpit power-down of a large spacecraft: switch thrown, descending electrical drone, ventilation winding down, soft relay clacks fading out."]),
    ("holo_deploy", 1.2, False, [
        "Holographic cockpit display projector turning on: a soft servo whir and a quick rising glassy energy shimmer, subtle crackle, settles quietly, short and refined, not a beep.",
        "Sci-fi hologram screen materialising from a projector: brief electrical hum swelling with a light airy shimmer and a soft low click at the end, subtle."]),
    ("holo_retract", 1.0, False, [
        "Holographic cockpit display projector turning off: a quick descending glassy shimmer collapsing into a soft low thump, servo whir, subtle and short.",
        "Sci-fi hologram screen dissolving: falling airy energy sweep and a soft muffled click as the projector shuts, subtle."]),
    ("holo_tick", 0.5, False, [
        "Pressing a button on a holographic cockpit display: a soft, dry, short tactile tick with a faint low electrical body, subtle and quiet, not a beep, not a notification.",
        "A single quiet sci-fi interface select sound: muted soft click with a tiny low thump, very short, subtle, dry."]),
    ("switch_click", 0.5, False, [
        "A heavy-duty metal toggle switch in a spaceship cockpit flipped: solid mechanical snap and clack, short and dry, close up.",
        "Rugged military aircraft rocker switch pressed: firm plastic and metal click with a slight spring, short, close up."]),
    ("button_press", 0.5, False, [
        "Pressing a backlit physical push button on a spaceship console: a firm, short, muted mechanical click with a soft rubber dampening, close up, no electronic tone.",
        "A chunky cockpit console key pressed and released: two soft mechanical clicks, short, close up, no beep."]),
    # batch 2 (9. 10. 2026, "no sound in the game sounds good"): the procedural rest and the sounds the game lacks
    ("boost_start", 1.5, False, [
        "Spaceship afterburner kicking in, heard from the cockpit: a sudden deep whoosh and a hard thump of extra thrust, the engine roar surging louder.",
        "Sci-fi fighter boost engaging: a punchy low-frequency burst, rushing air and a rising turbine howl, short and powerful."]),
    ("boost_loop", 6, True, [
        "Spaceship afterburner running at full power from inside the cockpit: an intense deep roaring rush, strong hull vibration, aggressive and dense, seamless loop.",
        "Sustained sci-fi boost thrust: a powerful throaty roar with a high turbine scream on top, heavy and continuous, seamless loop."]),
    ("cruise_charge", 4, False, [
        "Spaceship quantum drive spooling up: a deep rising electrical hum building in pitch and intensity, energy crackles, a tense swell before the jump.",
        "Sci-fi jump drive charging: a low throb rising into a powerful harmonic whine, capacitors charging, building tension."]),
    ("cruise_engage", 2.5, False, [
        "Spaceship quantum jump engaging: a massive deep boom and a whoosh of space bending, followed by a rushing roar.",
        "Sci-fi warp drive launch: a heavy sub-bass impact with a reversed swell and a bright energy tear, cinematic."]),
    ("cruise_loop", 8, True, [
        "Inside a spaceship traveling in a quantum tunnel: a smooth deep rushing drone with a soft shimmering harmonic layer, steady and hypnotic, seamless loop.",
        "Sustained sci-fi warp travel ambience: low rumble with airy energy wash and a subtle pulsing tone, seamless loop."]),
    ("cruise_drop", 2.5, False, [
        "Spaceship dropping out of quantum travel: an energy whoosh collapsing into a deep thud, rumble fading to quiet engines.",
        "Sci-fi warp exit: a reverse swell into a soft heavy impact and a fading shimmer."]),
    ("touchdown", 1.5, False, [
        "Heavy spaceship landing gear touching down on the ground, heard from inside: deep hydraulic thud, metal struts compressing with a groan, a settling creak.",
        "Spacecraft landing contact: a solid low impact through the hull, suspension hiss and metal clunk."]),
    ("gear_deploy", 3, False, [
        "Spaceship landing gear extending, heard from the cockpit: hydraulic whine, bay doors opening with a clunk, the gear struts locking down with a heavy mechanical thunk.",
        "Aircraft-style landing gear lowering: motor whir, hydraulic hiss, a firm lock clank at the end."]),
    ("gear_retract", 3, False, [
        "Spaceship landing gear retracting, heard from the cockpit: hydraulic whine, struts folding up, bay doors closing with a heavy clunk.",
        "Landing gear raising into the hull: motor hum, hydraulic hiss, a solid door thud at the end."]),
    ("door_open", 1.2, False, [
        "A sliding metal door on a spaceship opening: a pneumatic hiss and a smooth fast mechanical slide ending with a soft thump.",
        "Sci-fi interior door opening: a short motor whir, air release and a sliding metal panel."]),
    ("door_close", 1.2, False, [
        "A sliding metal door on a spaceship closing: a smooth fast mechanical slide and a firm sealing thud with a short air hiss.",
        "Sci-fi interior door shutting: sliding panel, a solid clunk and a soft pressure seal."]),
    ("footstep", 0.5, False, [
        "A single footstep of a boot on a metal spaceship deck plate: a firm heel strike with a slight hollow metallic ring, close up, dry.",
        "One boot step on a grated metal floor in a spacecraft: a solid tap with a little metal resonance, short."]),
    ("ui_hover", 0.5, False, [
        "Game menu hover sound: a very soft, short, low muted tick, subtle and refined, not a beep.",
        "Subtle sci-fi menu cursor move: a tiny soft airy tick, quiet and dry."]),
    ("ui_confirm", 0.6, False, [
        "Game menu confirm sound in a sci-fi style: a soft, deep, short mechanical click with a low warm resonance, refined, not a phone notification.",
        "Sci-fi menu select: a muted solid click with a gentle low swell, short and premium."]),
    ("menu_ambience", 20, True, [
        "Ambient background for a space game main menu: a deep slow evolving drone, distant hum of a spacecraft, faint airy space atmosphere, calm and vast, seamless loop.",
        "Calm sci-fi menu ambience: soft low pads of distant machinery and space wind, slowly breathing, seamless loop."]),
]


def specs():
    out = []
    for name, sec, loop, prompts in SOUNDS:
        # (take c on Sonilo: the author's Scenario plan refuses that model - left out)
        for take, (model, prompt, extra) in zip("ab", (
                (EL, prompts[0], {"promptInfluence": 0.7}), (EL, prompts[1], {"promptInfluence": 0.5}))):
            if model == EL:
                params = dict({"text": (prompt + STYLE)[:450], "durationSeconds": sec, "loop": loop, "outputFormat": "mp3_44100_192"}, **extra)
                ext = "mp3"
            else:
                params = {"prompt": prompt + STYLE, "duration": max(1, int(round(sec))), "audioFormat": "wav"}
                ext = "wav"
            out.append({"sound": name, "take": take, "model": model, "params": params, "prompt": prompt,
                        "file": "%s_%s.%s" % (name, take, ext), "loop": loop})
    return out


def start(spec):
    job = sc.rest("POST", "/generate/custom/%s" % spec["model"], spec["params"])
    return job.get("job", {}).get("jobId") or job.get("jobId")


def main(argv):
    os.makedirs(OUT, exist_ok=True)
    manifest_path = os.path.join(OUT, "candidates.json")
    manifest = json.load(open(manifest_path, encoding="utf-8")) if os.path.exists(manifest_path) else {}
    todo = [s for s in specs() if not os.path.exists(os.path.join(OUT, s["file"]))]
    if "--list" in argv:
        for s in specs():
            print(s["file"], s["model"])
        return 0
    # jobs already started from the MCP tools (engine_loop a/b), picked up instead of paying twice
    resume = {"engine_loop_a.mp3": "job_Kpgg6NEQCmVwuumhXPdxkQpa", "engine_loop_b.mp3": "job_jjYUEC7UuY12yFrJH7rg8K1H"}
    running = {}
    for s in todo:
        if s["file"] in resume:
            running[resume[s["file"]]] = s
    queue = [s for s in todo if s["file"] not in resume]
    while queue or running:
        while queue and len(running) < 2:
            s = queue.pop(0)
            try:
                running[start(s)] = s
            except SystemExit as e:
                s["tries"] = s.get("tries", 0) + 1
                # (two jobs at once is the plan's limit - wait; any other refusal three times, e.g. Sonilo needs a
                # higher plan: give that take up instead of retrying for ever)
                sc.log("start %s failed (%d): %s" % (s["file"], s["tries"], str(e)[:160]))
                if "parallel" in str(e) or s["tries"] < 3:
                    queue.append(s)
                break
        time.sleep(6)
        for jid, s in list(running.items()):
            job = sc.rest("GET", "/jobs/%s" % jid)["job"]
            if job.get("status") not in ("success", "failure", "canceled", "error"):
                continue
            del running[jid]
            meta = job.get("metadata", {}) or {}
            assets = meta.get("assetIds") or (meta.get("output", {}) or {}).get("assetIds") or []
            if job.get("status") != "success" or not assets:
                sc.log("%s: %s" % (s["file"], job.get("status")))
                continue
            sc.download_asset(assets[0], os.path.join(OUT, s["file"]))
            manifest[s["file"]] = {"sound": s["sound"], "take": s["take"], "model": s["model"], "prompt": s["prompt"],
                                   "loop": s["loop"], "asset": assets[0], "cu": (job.get("billing") or {}).get("cuCost")}
            json.dump(manifest, open(manifest_path, "w", encoding="utf-8"), indent=1)
    print("CANDIDATES", len(manifest), "files in", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
