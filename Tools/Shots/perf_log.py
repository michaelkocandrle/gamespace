"""Prints the shot runner's per-shot GPU and frame times ('SHOTS perf <name> gpu_ms=.. frame_ms=..') from a game log,
grouped by shot name with the mean and the spread (29. 9. 2026).

    python Tools/Shots/perf_log.py [log ...]     (default: the packaged game's log and the project's log)

Several logs (several runs) pool their samples per shot-name prefix (interior_1..3 -> interior).
"""
import os
import re
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT = [os.path.join("C:/gamespace/Builds/Gamespace/Windows/gamespace/Saved/Logs/gamespace.log"),
           os.path.join(ROOT, "Saved", "Logs", "gamespace.log")]
LINE = re.compile(r"SHOTS perf (\S+) gpu_ms=([\d.]+) frame_ms=([\d.]+) frames=(\d+)")


def main():
    logs = sys.argv[1:] or [p for p in DEFAULT if os.path.exists(p)]
    groups = {}
    for log in logs:
        for m in LINE.finditer(open(log, encoding="utf-8", errors="replace").read()):
            name = re.sub(r"_\d+$", "", m.group(1))
            groups.setdefault(name, []).append((float(m.group(2)), float(m.group(3))))
    for name, vals in groups.items():
        gpu = [v[0] for v in vals]
        frame = [v[1] for v in vals]
        spread = (max(gpu) - min(gpu)) if len(gpu) > 1 else 0.0
        print("PERF %-14s n=%d  gpu %.2f ms (min %.2f, max %.2f, spread %.2f)  frame %.2f ms" % (
            name, len(gpu), statistics.mean(gpu), min(gpu), max(gpu), spread, statistics.mean(frame)))


if __name__ == "__main__":
    main()
