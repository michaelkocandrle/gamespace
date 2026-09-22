"""Talk to Scenario through its MCP server: upload a mesh, run a model, download the result.

    python Tools/Assets/scenario_mcp.py tools                       # what the server offers
    python Tools/Assets/scenario_mcp.py upload <file> [kind]        # -> asset id
    python Tools/Assets/scenario_mcp.py run <modelId> '<json args>' # -> job, waits, downloads
    python Tools/Assets/scenario_mcp.py get <assetId> <out file>

Why not plain REST: uploading a 3D file goes through a multipart upload whose completing call is
not in the public documentation (Docs/WORKFLOW.md 3.1b). The MCP server does that step, so the
upload runs through it; everything else (jobs, assets) is read over the ordinary REST API.

Credentials: C:/gamespace/secrets/scenario.key, one line "<api key>:<api secret>", never in the
repository. Both interfaces use the same pair - MCP over HTTP JSON-RPC with Basic auth, REST the
same way.
"""

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

MCP = "https://mcp.scenario.com/mcp"
REST = "https://api.cloud.scenario.com/v1"
KEY_FILE = r"C:/gamespace/secrets/scenario.key"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KINDS = {".glb": ("3d", "model/gltf-binary"), ".gltf": ("3d", "model/gltf+json"),
         ".obj": ("3d", "model/obj"), ".fbx": ("3d", "application/octet-stream"),
         ".png": ("image", "image/png"), ".jpg": ("image", "image/jpeg")}


def log(msg):
    print("scenario: %s" % msg, flush=True)


def credentials():
    pair = open(KEY_FILE, encoding="utf-8").read().strip()
    if ":" not in pair:
        raise SystemExit("scenario: %s must hold '<api key>:<api secret>'" % KEY_FILE)
    return "Basic " + base64.b64encode(pair.encode()).decode()


def rest(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(REST + path, data=data, method=method)
    request.add_header("Authorization", credentials())
    if data:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        raise SystemExit("scenario: %s %s -> HTTP %d %s"
                         % (method, path, error.code, error.read().decode("utf-8", "replace")[:300]))


class Mcp:
    """One JSON-RPC session: initialize, then tools/call. The session id comes back as a header."""

    def __init__(self):
        self.session = None
        self.next_id = 0
        result = self.send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "gamespace", "version": "1.0"},
        })
        log("server %s" % json.dumps(result.get("serverInfo", {})))
        self.send("notifications/initialized", None, notify=True)

    def send(self, method, params, notify=False):
        self.next_id += 1
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        if not notify:
            payload["id"] = self.next_id
        request = urllib.request.Request(MCP, data=json.dumps(payload).encode(), method="POST")
        request.add_header("Authorization", credentials())
        request.add_header("Content-Type", "application/json")
        request.add_header("Accept", "application/json, text/event-stream")
        if self.session:
            request.add_header("Mcp-Session-Id", self.session)
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                self.session = self.session or response.headers.get("Mcp-Session-Id")
                raw = response.read().decode()
        except urllib.error.HTTPError as error:
            raise SystemExit("scenario: MCP %s -> HTTP %d %s"
                             % (method, error.code, error.read().decode("utf-8", "replace")[:300]))
        if notify or not raw.strip():
            return {}
        # The server may answer as an SSE stream ("data: {...}") or as plain JSON.
        for line in raw.splitlines():
            line = line[5:].strip() if line.startswith("data:") else line.strip()
            if not line.startswith("{"):
                continue
            message = json.loads(line)
            if "error" in message:
                raise SystemExit("scenario: MCP %s -> %s" % (method, json.dumps(message["error"])[:300]))
            if "result" in message:
                return message["result"]
        return {}

    def call(self, tool, arguments):
        result = self.send("tools/call", {"name": tool, "arguments": arguments})
        for item in result.get("content", []):
            if item.get("type") == "text":
                text = item["text"]
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"text": text}
        return result


def upload(mcp, path, kind=None):
    ext = os.path.splitext(path)[1].lower()
    guess_kind, content_type = KINDS.get(ext, ("image", "application/octet-stream"))
    kind = kind or guess_kind
    size = os.path.getsize(path)
    started = mcp.call("upload_asset", {
        "file_name": os.path.basename(path),
        "content_type": content_type,
        "kind": kind,
        "file_size": size,
    })
    upload_id = started.get("upload_id") or started.get("uploadId") or (started.get("upload") or {}).get("id")
    parts = started.get("parts") or (started.get("upload") or {}).get("parts") or []
    if not upload_id or not parts:
        raise SystemExit("scenario: upload_asset gave no parts: %s" % json.dumps(started)[:300])
    blob = open(path, "rb").read()
    chunk = -(-size // len(parts))
    done = []
    for index, part in enumerate(parts):
        url = part.get("upload_url") or part.get("url")
        piece = blob[index * chunk:(index + 1) * chunk]
        request = urllib.request.Request(url, data=piece, method="PUT")
        with urllib.request.urlopen(request, timeout=600) as response:
            etag = response.headers.get("ETag", "").strip('"')
        done.append({"part_number": part.get("number", index + 1), "etag": etag})
        log("  part %d/%d, %.1f kB" % (index + 1, len(parts), len(piece) / 1024))
    finished = mcp.call("upload_asset_complete", {"upload_id": upload_id, "parts": done})
    asset = (finished.get("asset") or {}).get("id") or finished.get("asset_id") or finished.get("assetId")
    if not asset:
        raise SystemExit("scenario: upload_asset_complete gave no asset id: %s" % json.dumps(finished)[:300])
    log("uploaded %s -> %s" % (os.path.basename(path), asset))
    return asset


def wait_for_job(job_id):
    while True:
        job = rest("GET", "/jobs/%s" % job_id)["job"]
        status = job.get("status")
        if status in ("success", "failure", "canceled", "error"):
            log("job %s: %s" % (job_id, status))
            return job
        time.sleep(10)


def download_asset(asset_id, path):
    asset = rest("GET", "/assets/%s" % asset_id)["asset"]
    with urllib.request.urlopen(asset["url"], timeout=600) as response, open(path, "wb") as out:
        out.write(response.read())
    log("saved %s (%.1f kB, %s)" % (path, os.path.getsize(path) / 1024, asset.get("mimeType")))
    return path


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    command = argv[0]
    if command == "tools":
        mcp = Mcp()
        for tool in mcp.send("tools/list", {}).get("tools", []):
            print("%-34s %s" % (tool["name"], (tool.get("description") or "").splitlines()[0][:90]))
        return 0
    if command == "upload":
        mcp = Mcp()
        print(upload(mcp, argv[1], argv[2] if len(argv) > 2 else None))
        return 0
    if command == "get":
        download_asset(argv[1], argv[2])
        return 0
    if command == "run":
        model, arguments = argv[1], json.loads(argv[2])
        job = rest("POST", "/generate/custom/%s" % model, arguments)
        job_id = job.get("job", {}).get("jobId") or job.get("jobId")
        log("job %s" % job_id)
        finished = wait_for_job(job_id)
        # The result ids sit straight under metadata, not under metadata.output.
        meta = finished.get("metadata", {}) or {}
        assets = meta.get("assetIds") or (meta.get("output", {}) or {}).get("assetIds") or []
        print(json.dumps({"status": finished.get("status"), "assets": assets,
                          "cu": finished.get("billing", {}).get("cuCost")}, indent=2))
        return 0
    raise SystemExit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
