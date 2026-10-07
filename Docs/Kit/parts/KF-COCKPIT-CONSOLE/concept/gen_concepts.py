"""2D concept views of the left cockpit console (KF-COCKPIT-CONSOLE) through Scenario's GPT Image 2.5 Sunburst
(author 7. 10. 2026: the SC images are style and design references only, the sizes and layout are ours; generate
the angles the build needs). The SC references go in as style references; the views after the hero also get the
hero image, so they show the same object.

    python Docs/Kit/parts/KF-COCKPIT-CONSOLE/concept/gen_concepts.py hero
    python Docs/Kit/parts/KF-COCKPIT-CONSOLE/concept/gen_concepts.py views <hero asset id>
    python Docs/Kit/parts/KF-COCKPIT-CONSOLE/concept/gen_concepts.py sheets <hero asset id>   # orthographic + details
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
CLI = os.path.join(ROOT, "Tools", "Assets", "scenario_mcp.py")
MODEL = "model_openai-gpt-image-2-5-sunburst"
# Docs/Kit/etalon/sc: konzole_3, kreslo_2, konzole_1, konzole_2, kreslo_1 (uploaded 7. 10. 2026)
REFS = ["asset_frGDRNv6x7GBZQ4LeMzYyipD", "asset_k1CRXcWHCcH87rfoocbHyuxm", "asset_1mh2FKQcB5LRjhQijQdgwJd2",
        "asset_qn2JwZBCWgnqQnLvPneLL4NY", "asset_hpx5iiEUrx3mzCbFRLS5fkUS"]

STYLE = ("Game art concept render at Star Citizen production quality. Use the Star Citizen reference images ONLY for "
         "style, materials, level of detail and design language: layered painted metal parts, chunky bevelled "
         "housings, separate bolted modules, panel seams, screws, dark recessed fields with hatch decals, small white "
         "legends, warning stripes, light edge wear. Do not copy their logos; the maker is the fictional 'Halcyon "
         "Freightworks' (brand mark HALCYON), its accent colour is a warm orange instead of yellow.")
OBJECT = ("The object, our own design: the LEFT armrest control console that stands beside the single pilot seat of "
          "a small industrial cargo spaceship. A long pedestal about 1.2 m long and 0.65 m wide, its top at elbow "
          "height. Along its INNER edge (the side facing the seat) a raised forearm unit cantilevers over the pedestal "
          "on two short metal brackets, so a dark gap and shadow shows under it; it carries a padded perforated wrist "
          "rest and, at its front end, a flight stick (polished ball joint in a hatched orange-and-black boot ring, "
          "sculpted dark rubber grip, mid-grey head with two hat switches, a red button, a trigger, a flat metal guard "
          "bar). Ergonomic order from the rear (the seat back) to the front: the padded forearm rest first, the stick "
          "AHEAD of it where the seated pilot's hand falls, then the control face at the very front end. The OUTBOARD half is a slightly lower deck built from separate framed modules: an intake grille with "
          "louvres, a status strip with three small backlit lamp bars and legends, a 2x2 block of square backlit keys. "
          "The front end rises into a sloped control face with a red emergency key under a flip-up red cover framed in "
          "orange, three rocker switches with white legends and small LEDs. A grab handle with an orange grip band at "
          "the front outer corner. Body in mid-grey painted metal, darker gunmetal plinth and recessed fields, the "
          "forearm unit a lighter warm grey with a satin clear coat. Clearly in service: scuffed paint on contact "
          "edges, grime in the seams.")
STUDIO = ("Only this one object, whole in frame. Neutral grey studio backdrop, soft even key light from above with "
          "soft shadows. No seat, no other cockpit parts, no people, no text overlay, no watermark.")
VIEWS = {
    "hero_34": "View: three-quarter view from the front and above, from the seat side.",
    "front": "View: straight from the front (looking back along the console's length), camera at standing eye "
             "height, slightly above; the sloped control face and the stick in the middle of the image.",
    "top": "View: straight from above (top-down plan view, orthographic feel), the console's length running "
           "left to right, the seat side at the bottom of the image.",
    "side_inner": "View: from the seat side, perpendicular to the console's long side, camera at elbow height, so the "
                  "gap under the forearm unit and its two brackets read clearly.",
    "side_outer": "View: from the outboard side (the hull side, away from the seat), perpendicular to the long side, "
                  "camera slightly above; show the pedestal's outer face and its service panel.",
    "rear_34": "View: three-quarter view from behind and above, from the outboard side.",
    "face_close": "View: close-up of the sloped control face at the front end only: the covered red emergency key, "
                  "the rocker switches, their legends, screws and the grab handle, from the pilot's seated eye.",
    "stick_close": "View: close-up of the flight stick and the wrist rest on the forearm unit, three-quarter from the "
                   "front, the boot ring, grip, head buttons and guard bar sharp.",
}


def run(name, refs):
    args = {"prompt": "\n\n".join([STYLE, OBJECT, VIEWS[name], STUDIO]), "referenceImages": refs,
            "quality": "high", "width": 2048, "height": 1152, "numOutputs": 1}
    out = subprocess.run([sys.executable, CLI, "run", MODEL, json.dumps(args)], capture_output=True, text=True)
    res = json.loads(out.stdout[out.stdout.index("{"):])
    for k, a in enumerate(res["assets"]):
        path = os.path.join(HERE, "%s%s.png" % (name, "" if k == 0 else "_%d" % k))
        subprocess.run([sys.executable, CLI, "get", a, path], check=True)
        print(name, a, path, res.get("cu"))
    return res["assets"]


# single views of the hero's object keep its 3/4 composition (7. 10.: the side, rear and stick views came out as near
# copies of the hero) - the orthographic and detail views go on sheets, which the model lays out view by view
SHEETS = {
    "turnaround": "Make a product design TURNAROUND SHEET of exactly this console (the first reference image is the "
                  "object - keep every module, colour, decal and part identical). Four orthographic views on one "
                  "neutral grey sheet, each labelled in small caps under it, no perspective: TOP PLAN (looking straight "
                  "down, the console's length left to right, the forearm rest along the bottom edge), INNER SIDE "
                  "ELEVATION (the seat side, looking straight at the long side: the forearm rest on its two brackets "
                  "above the pedestal with the gap under it, the stick, the raised control face at the right end), "
                  "OUTER SIDE ELEVATION (the opposite long side, the hull side, its panels and service hatches), FRONT "
                  "ELEVATION (looking straight at the front end: the control face and the grab handle). Same scale "
                  "in all four, aligned in a 2 x 2 grid.",
    "details": "Make a DETAIL SHEET of exactly this console (the first reference image is the object - keep every "
               "part identical), four close-up views on one neutral grey sheet, labelled in small caps: STICK (the "
               "flight stick from the pilot's side at hand height: boot ring with orange hatch, ball joint, rubber "
               "grip with finger grooves, head with hat switches and red button, trigger, guard bar), FOREARM REST "
               "(the padded perforated rest and its bracket from below at an angle, showing the gap and the bolts), "
               "REAR END (the rear end of the console from behind and above), STATUS AND KEYS (the status strip and "
               "the 2 x 2 key block straight from above, legends readable). 2 x 2 grid.",
}


def run_sheet(name, hero):
    args = {"prompt": "\n\n".join([SHEETS[name], STYLE, OBJECT, "No text other than the view labels and the decals "
                                   "on the object. No people."]), "referenceImages": [hero] + REFS[:2],
            "quality": "high", "width": 2048, "height": 2048, "numOutputs": 1}
    out = subprocess.run([sys.executable, CLI, "run", MODEL, json.dumps(args)], capture_output=True, text=True)
    res = json.loads(out.stdout[out.stdout.index("{"):])
    path = os.path.join(HERE, "sheet_%s.png" % name)
    subprocess.run([sys.executable, CLI, "get", res["assets"][0], path], check=True)
    print(name, res["assets"][0], path, res.get("cu"))


def main(argv):
    with open(os.path.join(HERE, "prompt.txt"), "w", encoding="utf-8") as f:
        f.write("\n\n".join([STYLE, OBJECT, STUDIO]) + "\n\n" + "\n".join("%s: %s" % kv for kv in VIEWS.items()) + "\n")
    if argv[0] == "hero":
        run("hero_34", REFS)
    elif argv[0] == "views":
        for name in VIEWS:
            if name != "hero_34":
                run(name, [argv[1]] + REFS[:3])
    elif argv[0] == "sheets":
        for name in SHEETS:
            run_sheet(name, argv[1])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
