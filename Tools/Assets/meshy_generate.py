"""Generate the kitbash detail parts with Meshy's text-to-3D API and download them.

    set MESHY_API_KEY=...            (never put the key in the repo)
    python Tools/Assets/meshy_generate.py              # every part in Tools/Assets/kitbash_parts.json
    python Tools/Assets/meshy_generate.py SwitchPanel  # one part
    python Tools/Assets/meshy_generate.py --refine     # also run the texture pass
    python Tools/Assets/meshy_generate.py --dry-run    # print the prompts, call nothing
    python Tools/Assets/meshy_generate.py --spec ArtSource/Ships/Steadfast/Kitbash/meshy_parts.json         --out ArtSource/Ships/Steadfast/Kitbash/Meshy --refine      # another ship's list

Why a script and not clicking the site: the four parts have to be regenerable with the same
prompts and the same sizes, and the recipe belongs next to the rest of the pipeline
(Docs/AssetPipeline_Modular.md). The models land in ArtSource/Ships/Vanguard/Kitbash/Meshy/ as
GLB, which is what Tools/Blender/build_ai_ship.py already reads.

API (docs.meshy.ai, checked 23. 9. 2026): POST https://api.meshy.ai/openapi/v2/text-to-3d with
mode "preview" returns {"result": "<task id>"}; GET .../text-to-3d/<id> returns status
(PENDING / IN_PROGRESS / SUCCEEDED / FAILED / CANCELED), progress and model_urls.glb. A second
POST with mode "refine" and preview_task_id textures the model it already made.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = "https://api.meshy.ai/openapi/v2/text-to-3d"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SPEC = os.path.join(ROOT, "Tools", "Assets", "kitbash_parts.json")
OUT = os.path.join(ROOT, "ArtSource", "Ships", "Vanguard", "Kitbash", "Meshy")
POLL_SECONDS = 10
GIVE_UP_AFTER = 20 * 60


def log(msg):
    print("meshy: %s" % msg, flush=True)


def call(method, url, key, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", "Bearer %s" % key)
    if data:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:400]
        # The key must never end up in a log or a traceback.
        raise SystemExit("meshy: %s %s -> HTTP %d %s" % (method, url, error.code, detail))


def wait_for(task_id, key):
    started = time.time()
    last = None
    while True:
        task = call("GET", "%s/%s" % (BASE, task_id), key)
        status, progress = task.get("status"), task.get("progress")
        if (status, progress) != last:
            log("  %s %s%%" % (status, progress))
            last = (status, progress)
        if status == "SUCCEEDED":
            return task
        if status in ("FAILED", "CANCELED"):
            raise SystemExit("meshy: task %s ended as %s: %s" % (task_id, status, task.get("task_error")))
        if time.time() - started > GIVE_UP_AFTER:
            raise SystemExit("meshy: task %s still %s after %d minutes" % (task_id, status, GIVE_UP_AFTER // 60))
        time.sleep(POLL_SECONDS)


def download(url, path):
    with urllib.request.urlopen(url, timeout=300) as response, open(path, "wb") as out:
        while True:
            chunk = response.read(1 << 16)
            if not chunk:
                break
            out.write(chunk)
    return os.path.getsize(path)


def main(argv):
    refine = "--refine" in argv
    dry_run = "--dry-run" in argv
    # --hi asks for geometry, not just a silhouette: the finest voxel grid Meshy offers and a much
    # higher triangle budget. Used to see how far the cheap route gets before paying for UltraShape.
    hi = "--hi" in argv
    # --spec <json> --out <folder>: another ship's part list (default: the Vanguard's kitbash parts).
    spec_path, out_dir = SPEC, OUT
    for flag in ("--spec", "--out"):
        if flag in argv:
            value = argv[argv.index(flag) + 1]
            argv = [a for i, a in enumerate(argv) if a != flag and (i == 0 or argv[i - 1] != flag)]
            if flag == "--spec":
                spec_path = os.path.join(ROOT, value)
            else:
                out_dir = os.path.join(ROOT, value)
    wanted = [a for a in argv if not a.startswith("-")]

    spec = json.load(open(spec_path, encoding="utf-8"))
    style = spec.get("style", "")
    parts = [p for p in spec["parts"] if not wanted or p["name"] in wanted]
    if not parts:
        raise SystemExit("meshy: no part called %s in %s" % (", ".join(wanted), spec_path))

    key = os.environ.get("MESHY_API_KEY", "").strip()
    if not key and not dry_run:
        raise SystemExit("meshy: set MESHY_API_KEY first (the key never goes in the repo)")

    os.makedirs(out_dir, exist_ok=True)
    report = {}
    for part in parts:
        prompt = "%s. Style: %s" % (part["prompt"], style) if style else part["prompt"]
        log("%s (%s cm)" % (part["name"], " x ".join("%.1f" % v for v in part["size_cm"])))
        log("  prompt: %s" % prompt)
        if dry_run:
            continue

        body = {
            "mode": "preview",
            "prompt": prompt[:800],
            "ai_model": "latest",
            "should_remesh": True,
            "target_polycount": 30000 if hi else int(part.get("target_polycount", 3000)),
        }
        if hi:
            body["geometry_resolution"] = "4k"
        task_id = call("POST", BASE, key, body)["result"]
        log("  preview task %s" % task_id)
        task = wait_for(task_id, key)

        if refine:
            refine_id = call("POST", BASE, key, {
                "mode": "refine",
                "preview_task_id": task_id,
                "enable_pbr": True,
                "texture_resolution": "2k",
            })["result"]
            log("  refine task %s" % refine_id)
            task = wait_for(refine_id, key)

        url = (task.get("model_urls") or {}).get("glb")
        if not url:
            raise SystemExit("meshy: task %s has no glb in model_urls" % task.get("id"))
        path = os.path.join(out_dir, "%s%s.glb" % (part["name"], "_hi" if hi else ""))
        size = download(url, path)
        log("  saved %s (%.1f MB, %s credits)" % (path, size / 1e6, task.get("consumed_credits")))
        report[part["name"] + ("_hi" if hi else "")] = {
            "task": task.get("id"),
            "glb": os.path.relpath(path, ROOT).replace("\\", "/"),
            "size_cm": part["size_cm"],
            "credits": task.get("consumed_credits"),
        }

    if report:
        path = os.path.join(out_dir, "meshy_report.json")
        json.dump(report, open(path, "w", encoding="utf-8"), indent=2)
        log("report %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
