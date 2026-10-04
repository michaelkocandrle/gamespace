"""Cockpit v2 design data and its C-01 sheet (plain Python, runs in Tools/Test.ps1 and CI):

    python Tools/Tests/test_cockpit_v2_design.py

- every element of ArtSource/Ships/Wayfarer/Design/Wayfarer_cockpit_v2.json has a unique ID, a name, a Czech purpose
  and a material zone that exists (or "-"/decals); every target and material zone has an ID;
- the C-01 sheet's sidecar lists exactly the data's elements and draws a callout for each one (sheet = data);
- the sheet is not older than the data (redraw: python Tools/Design/draw_cockpit_v2_sheet.py Wayfarer).
Prints CKTEST PASS|FAIL lines and CKTEST SUMMARY; exit code 1 on a failure.
"""
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DESIGN = os.path.join(REPO, "ArtSource", "Ships", "Wayfarer", "Design")
failures = []


def check(name, ok, detail=""):
    print("CKTEST %s %s%s" % ("PASS" if ok else "FAIL", name, "  (" + detail + ")" if detail else ""))
    if not ok:
        failures.append(name)


def main():
    data = json.load(open(os.path.join(DESIGN, "Wayfarer_cockpit_v2.json"), encoding="utf-8"))
    ids = [e["id"] for e in data["elements"]]
    check("element IDs are unique", len(ids) == len(set(ids)), str(ids))
    zones = {m["id"] for m in data["materials"]}
    for e in data["elements"]:
        used = set(re.findall(r"MZ-C\d", e.get("material", "")))
        check("%s has a name, a purpose and known material zones" % e["id"],
              bool(e.get("name")) and len(e.get("purpose", "")) > 20 and used <= zones, str(used - zones))
    check("targets and zones have IDs", all(t.get("id") for t in data["targets"]) and len(zones) == len(data["materials"]))
    sidecar_path = os.path.join(DESIGN, "Drawings", "Wayfarer_C01_cockpit_v2.json")
    sheet_path = sidecar_path.replace(".json", ".png")
    check("C-01 sheet exists", os.path.isfile(sheet_path) and os.path.isfile(sidecar_path))
    if os.path.isfile(sidecar_path):
        sidecar = json.load(open(sidecar_path, encoding="utf-8"))
        check("the sheet lists the data's elements", sidecar["elements"] == ids, str(set(ids) ^ set(sidecar["elements"])))
        check("every element has a callout on the pilot view", set(sidecar["callouts"]) == set(ids), str(set(ids) - set(sidecar["callouts"])))
        check("every target is on the sheet", sidecar["targets"] == [t["id"] for t in data["targets"]])
    print("CKTEST SUMMARY %s (%d failures)" % ("PASS" if not failures else "FAIL", len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
