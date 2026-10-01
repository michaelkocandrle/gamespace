"""Tools/HeavyLock.ps1 on a temporary lock file (GAMESPACE_HEAVY_LOCK): take, busy, the 20-minute takeover, the
heartbeat watcher, release at the end of a response (release-idle keeps a lock whose operation still runs) and the
run wrapper (author 1. 10. 2026: a session waited 8 hours for a lock nobody released).

    python Tools/Tests/test_heavy_lock.py      (Windows PowerShell or pwsh)

Prints LOCKTEST PASS|FAIL lines and LOCKTEST SUMMARY.
"""
import datetime
import os
import shutil
import subprocess
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(REPO, "Tools", "HeavyLock.ps1")
SHELL = shutil.which("powershell") or shutil.which("pwsh")
failures = []


def check(name, ok, detail=""):
    print("LOCKTEST %s %s%s" % ("PASS" if ok else "FAIL", name, (" (%s)" % detail) if detail else ""))
    if not ok:
        failures.append(name)


def lock(env, *args):
    r = subprocess.run([SHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", SCRIPT] + list(args),
                       capture_output=True, text=True, env=env, timeout=120)
    return r.returncode, (r.stdout + r.stderr).strip()


def read(path):
    info = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            if ":" in line:
                k, v = line.split(":", 1)
                info[k.strip()] = v.strip()
    return info


def write_aged(path, session, minutes, pid=0):
    t = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=minutes)).isoformat()
    with open(path, "w", encoding="utf-8") as f:
        f.write("session: %s\ntask: old\ntime: %s\nrefreshed: %s\npid: %d\nwatcher: 0\n" % (session, t, t, pid))


def main():
    if not SHELL:
        check("PowerShell available", False)
        print("LOCKTEST SUMMARY FAIL (1 failures)")
        return 1
    tmp = tempfile.mkdtemp(prefix="heavylock_")
    path = os.path.join(tmp, "heavy.lock")
    env = dict(os.environ, GAMESPACE_HEAVY_LOCK=path)
    try:
        code, out = lock(env, "status")
        check("free at the start", code == 0 and "FREE" in out, out)
        code, out = lock(env, "take", "-Task", "test A", "-Session", "A")
        check("take a free lock", code == 0 and os.path.exists(path) and read(path).get("session") == "A", out)
        code, out = lock(env, "take", "-Task", "test B", "-Session", "B")
        check("another session gets BUSY", code == 1 and "BUSY" in out, out)
        code, out = lock(env, "release", "-Session", "B")
        check("another session cannot release it", code == 1 and os.path.exists(path), out)

        write_aged(path, "A", 19)
        code, out = lock(env, "take", "-Task", "test B", "-Session", "B")
        check("19 minutes without a refresh is still held", code == 1, out)
        write_aged(path, "A", 21)
        code, out = lock(env, "take", "-Task", "test B", "-Session", "B")
        check("21 minutes without a refresh is abandoned and taken over", code == 0 and read(path).get("session") == "B", out)

        before = read(path).get("refreshed")
        time.sleep(1.1)
        code, out = lock(env, "refresh", "-Session", "B")
        check("refresh renews the time", code == 0 and read(path).get("refreshed") != before, out)

        # release-idle (the Stop hook): keep while the recorded operation runs, release when it ended
        sleeper = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        write_aged(path, "B", 0, sleeper.pid)
        code, out = lock(env, "release-idle", "-Session", "B")
        check("release-idle keeps the lock while its operation runs", code == 0 and os.path.exists(path), out)
        code, out = lock(env, "release-idle", "-Session", "A")
        check("release-idle of another session leaves it", code == 0 and os.path.exists(path), out)

        # heartbeat: the watcher refreshes every second while the owner runs and stops after it
        code, out = lock(env, "beat", "-Session", "B", "-OwnerPid", str(sleeper.pid), "-Seconds", "1")
        first = read(path).get("refreshed")
        watcher = int(read(path).get("watcher", "0") or 0)
        time.sleep(4.0)
        check("beat starts a watcher that refreshes the lock", watcher > 0 and read(path).get("refreshed") != first,
              out)
        sleeper.kill()
        sleeper.wait()
        time.sleep(3.5)
        alive = subprocess.run([SHELL, "-NoProfile", "-Command", "if (Get-Process -Id %d -ErrorAction SilentlyContinue) "
                                "{ 'alive' } else { 'gone' }" % watcher], capture_output=True, text=True).stdout.strip()
        check("the watcher stops when its operation ends", alive == "gone", alive)
        code, out = lock(env, "release-idle", "-Session", "B")
        check("release-idle releases when the operation ended", code == 0 and not os.path.exists(path), out)

        # run: holds the lock while the command runs, passes its exit code, releases after
        inner = os.path.join(tmp, "inner.ps1")
        with open(inner, "w", encoding="utf-8") as f:
            f.write("& '%s' status\nexit 3\n" % SCRIPT.replace("'", "''"))
        exec_line = "& '%s' -NoProfile -ExecutionPolicy Bypass -File '%s'" % (SHELL, inner)
        code, out = lock(env, "run", "-Task", "wrapped", "-Session", "C", "-Exec", exec_line)
        check("run holds the lock during the command", "HEAVYLOCK HELD C" in out, out[-300:])
        check("run passes the command's exit code and releases", code == 3 and not os.path.exists(path), "exit %d" % code)
        write_aged(path, "A", 1)
        code, out = lock(env, "run", "-Task", "wrapped", "-Session", "C", "-Exec", "exit 0")
        check("run does not start when the lock is busy", code == 1 and read(path).get("session") == "A", out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("LOCKTEST SUMMARY %s (%d failures)" % ("PASS" if not failures else "FAIL", len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
