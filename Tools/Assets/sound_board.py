"""Build the sound board page (author picks the takes by ear): every candidate of Tools/Assets/sound_candidates.py
next to the sound now in the game, as mp3 under <out>/audio/, and <out>/sound_board.html for the Artifact tool.

    python Tools/Assets/sound_board.py <out dir>
"""
import html
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CAND = os.path.join(ROOT, "ArtSource", "Audio", "Candidates")
EL = os.path.join(ROOT, "ArtSource", "Audio", "ElevenLabs")
GEN = os.path.join(ROOT, "Intermediate", "GeneratedAssets")

# sound -> (Czech label, where it plays in the game, the file it replaces now)
SOUNDS = [
    ("engine_loop", "Motor – tah", "smyčka za letu, výška a hlasitost podle plynu", os.path.join(GEN, "engine_loop.wav")),
    ("engine_hum", "Motor – volnoběh", "tichá smyčka reaktoru, když motory běží bez tahu", os.path.join(GEN, "engine_hum.wav")),
    ("engine_start", "Start motorů", "klávesa I nebo spínač ENG", os.path.join(EL, "engine_start.wav")),
    ("engine_stop", "Vypnutí motorů", "klávesa I nebo spínač ENG", os.path.join(EL, "engine_stop.wav")),
    ("power_up", "Zapnutí lodi", "klávesa U nebo otočný PWR", os.path.join(EL, "power_up.wav")),
    ("power_down", "Vypnutí lodi", "klávesa U nebo otočný PWR", os.path.join(EL, "power_down.wav")),
    ("holo_deploy", "MFD se otevírá", "holo obraz vyjede z emitoru po zapnutí", os.path.join(EL, "holo_deploy.wav")),
    ("holo_retract", "MFD se zavírá", "holo obraz zajede při vypnutí", os.path.join(EL, "holo_retract.wav")),
    ("holo_tick", "Klik na MFD", "přepnutí stránky F1/F2, klik na holo prvek", os.path.join(EL, "holo_tick.wav")),
    ("switch_click", "Páčkový spínač", "PWR, ENG a kryté spínače", os.path.join(EL, "switch_click.wav")),
    ("button_press", "Tlačítko konzole", "klik na tlačítko v režimu interakce (dnes zvuk menu)", os.path.join(GEN, "ui_confirm.wav")),
]
TAKES = {"a": "A – ElevenLabs", "b": "B – ElevenLabs, jiné zadání", "c": "C – Sonilo"}


def mp3(src, dst):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ac", "1", "-b:a", "128k", dst], check=True)


def main(out):
    audio = os.path.join(out, "audio")
    os.makedirs(audio, exist_ok=True)
    manifest = json.load(open(os.path.join(CAND, "candidates.json"), encoding="utf-8"))
    rows = []
    files = {}
    for name, label, where, now in SOUNDS:
        takes = []
        if os.path.exists(now):
            mp3(now, os.path.join(audio, "%s_now.mp3" % name))
            takes.append(("now", "Teď ve hře", "audio/%s_now.mp3" % name, ""))
        for t in "abc":
            for ext in ("mp3", "wav"):
                f = "%s_%s.%s" % (name, t, ext)
                if f in manifest and os.path.exists(os.path.join(CAND, f)):
                    mp3(os.path.join(CAND, f), os.path.join(audio, "%s_%s.mp3" % (name, t)))
                    takes.append((t, TAKES[t], "audio/%s_%s.mp3" % (name, t), manifest[f]["prompt"]))
        rows.append((name, label, where, takes))
    for f in os.listdir(audio):
        files["audio/" + f] = os.path.join(audio, f)
    tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sound_board_template.html"), encoding="utf-8").read()
    body = []
    for name, label, where, takes in rows:
        cards = []
        for t, tl, src, prompt in takes:
            pick = "" if t == "now" else ('<label class="pick"><input type="radio" name="%s" value="%s" id="%s_%s"> vybrat</label>' % (name, t, name, t))
            cards.append('<div class="take%s"><div class="tl">%s</div><audio controls preload="none" src="%s"></audio>%s%s</div>'
                         % (" now" if t == "now" else "", html.escape(tl), src, pick,
                            '<details><summary>zadání</summary><p>%s</p></details>' % html.escape(prompt) if prompt else ""))
        body.append('<section class="snd" data-sound="%s"><header><h2>%s</h2><p>%s</p><code>%s</code></header><div class="takes">%s</div></section>'
                    % (name, html.escape(label), html.escape(where), name, "".join(cards)))
    page = tpl.replace("<!--ROWS-->", "\n".join(body))
    open(os.path.join(out, "sound_board.html"), "w", encoding="utf-8").write(page)
    json.dump(files, open(os.path.join(out, "files.json"), "w"), indent=1)
    print("BOARD", os.path.join(out, "sound_board.html"), len(files), "audio files")


if __name__ == "__main__":
    main(sys.argv[1])
