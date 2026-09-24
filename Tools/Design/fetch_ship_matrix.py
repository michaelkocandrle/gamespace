"""RSI Ship Matrix -> local reference: the full JSON, a comparison table and one image per ship.

    python Tools/Design/fetch_ship_matrix.py --class small_multirole \
        --ships "Avenger Titan" "Mustang Alpha" "Aurora Mk I MR" 100i Cutter "C8X Pisces Expedition" Nomad Syulen

Writes into starcitizenreference/ship_matrix/:
  ship_matrix_index.json       the whole matrix (https://robertsspaceindustries.com/ship-matrix/index)
  <class>.md                   comparison table (dimensions, mass, cargo, crew, speeds, rotation, components)
  <class>.json                 the same numbers, machine readable (the spec of a new ship cites them)
  <class>/<ship>.jpg           the ship's catalogue image (slideshow_wide, 1200 x 800)

The images are CIG material: study references only. Never send them to an AI generator (Higgsfield,
Meshy, Scenario) and never ship them; our ships take the vibe, not the design.
--offline reuses an existing ship_matrix_index.json.
"""
import argparse
import json
import os
import re
import statistics
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "starcitizenreference", "ship_matrix")
URL = "https://robertsspaceindustries.com/ship-matrix/index"
UA = {"User-Agent": "Mozilla/5.0 (gamespace reference fetch)"}

FIELDS = [("length", "L m"), ("beam", "B m"), ("height", "H m"), ("mass", "mass kg"),
          ("cargocapacity", "SCU"), ("max_crew", "crew"), ("scm_speed", "SCM m/s"),
          ("afterburner_speed", "AB m/s"), ("pitch_max", "pitch °/s"), ("yaw_max", "yaw °/s"),
          ("roll_max", "roll °/s")]


def fetch(url, path):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as f:
        f.write(r.read())


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def components(ship):
    """{group: ["2x S1 Bulwark", ...]} from the matrix's 'compiled' block."""
    out = {}
    for cls in (ship.get("compiled") or {}).values():
        for group, items in cls.items():
            rows = []
            for it in items or []:
                size = ("S%s " % it["size"]) if it.get("size") else ""
                n = int(it.get("mounts") or 1) * int(it.get("quantity") or 1)
                load = ", ".join("%s S%s" % (l["name"], l["size"]) for l in (it.get("loadout") or []))
                rows.append("%s%s%s%s" % ("%dx " % n if n > 1 else "", size, it["name"],
                                          " (%s)" % load if load else ""))
            if rows:
                out[group] = rows
    return out


def slug(name):
    return re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--class", dest="klass", required=True, help="name of the reference set")
    ap.add_argument("--ships", nargs="+", required=True, help="exact Ship Matrix names")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--no-images", action="store_true")
    args = ap.parse_args()

    os.makedirs(os.path.join(OUT, args.klass), exist_ok=True)
    index = os.path.join(OUT, "ship_matrix_index.json")
    if not args.offline or not os.path.exists(index):
        fetch(URL, index)
    data = json.load(open(index, encoding="utf-8"))["data"]
    by_name = {s["name"].strip(): s for s in data}
    missing = [n for n in args.ships if n not in by_name]
    if missing:
        close = [s for s in by_name if any(m.lower() in s.lower() for m in missing)]
        raise SystemExit("not in the matrix: %s (similar: %s)" % (missing, close[:10]))

    rows = []
    for name in args.ships:
        s = by_name[name]
        row = {"name": name, "manufacturer": s["manufacturer"]["name"], "focus": s.get("focus"),
               "size": s.get("size"), "status": s.get("production_status"), "url": s.get("url"),
               "description": s.get("description"), "components": components(s)}
        row.update({k: num(s.get(k)) for k, _ in FIELDS})
        media = (s.get("media") or [{}])[0].get("images", {})
        row["image_url"] = media.get("slideshow_wide")
        if row["image_url"] and not args.no_images:
            path = os.path.join(OUT, args.klass, slug(name) + ".jpg")
            if not os.path.exists(path):
                fetch(row["image_url"], path)
            row["image"] = os.path.relpath(path, ROOT).replace("\\", "/")
        rows.append(row)

    stats = {}
    for k, label in FIELDS:
        vals = [r[k] for r in rows if r[k]]
        if vals:
            stats[k] = {"min": min(vals), "median": statistics.median(vals), "max": max(vals)}
    with open(os.path.join(OUT, args.klass + ".json"), "w", encoding="utf-8") as f:
        json.dump({"class": args.klass, "source": URL, "ships": rows, "stats": stats}, f, indent=1,
                  ensure_ascii=False)

    md = ["# Ship Matrix reference set: %s" % args.klass, "",
          "Generated by `Tools/Design/fetch_ship_matrix.py` from %s. Images are CIG material:" % URL,
          "study only, never into an AI generator, never in the game.", "",
          "| Ship | Maker | Focus | " + " | ".join(l for _, l in FIELDS) + " |",
          "| --- | --- | --- | " + " | ".join("---" for _ in FIELDS) + " |"]
    for r in rows:
        md.append("| %s | %s | %s | %s |" % (r["name"], r["manufacturer"], r["focus"],
                  " | ".join("%g" % r[k] if r[k] is not None else "–" for k, _ in FIELDS)))
    md.append("| **median** | | | %s |" % " | ".join(
        "%g" % stats[k]["median"] if k in stats else "–" for k, _ in FIELDS))
    md += ["", "## Components", ""]
    for r in rows:
        md.append("### %s" % r["name"])
        if r.get("image"):
            md.append("![%s](%s/%s.jpg)" % (r["name"], args.klass, slug(r["name"])))
        for g, items in r["components"].items():
            md.append("- **%s**: %s" % (g, "; ".join(items)))
        md.append("")
    with open(os.path.join(OUT, args.klass + ".md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("wrote %s.md / .json, %d ships" % (os.path.join(OUT, args.klass), len(rows)))


if __name__ == "__main__":
    main()
