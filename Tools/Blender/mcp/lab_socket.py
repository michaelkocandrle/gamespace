"""Send Python to the official Blender Lab MCP add-on directly (port 9877 here), without the MCP tools.

    python Tools/Blender/mcp/lab_socket.py "print(len(bpy.data.objects))"
    python Tools/Blender/mcp/lab_socket.py --file Tools/Blender/mcp/test_ops_context.py

Protocol (blmcp tools_helpers/connection.py): one JSON request {"type": "execute", "code", "strict_json"}
terminated by a NUL byte; the answer is JSON + NUL with status, result, stdout, stderr.
The community add-on on 9876 speaks a different protocol: use mcp_socket.py for that one.
"""
import json
import os
import socket
import sys

PORT = int(os.environ.get("BLENDER_MCP_PORT", "9877"))


def execute(code, timeout=300):
    request = json.dumps({"type": "execute", "code": code, "strict_json": False}) + "\0"
    with socket.create_connection(("localhost", PORT), timeout=timeout) as sock:
        sock.sendall(request.encode("utf-8"))
        buf = bytearray()
        while b"\0" not in buf:
            chunk = sock.recv(65536)
            if not chunk:
                break
            buf.extend(chunk)
    return json.loads(buf.split(b"\0", 1)[0].decode("utf-8"))


if __name__ == "__main__":
    if sys.argv[1] == "--file":
        src = open(sys.argv[2], encoding="utf-8").read()
    else:
        src = sys.argv[1]
    response = execute(src)
    print(response.get("stdout", ""), end="")
    if response.get("status") != "ok":
        print(json.dumps(response)[:3000])
