"""Talk to the Blender MCP addon's socket directly: python mcp_socket.py <type> [json params]."""
import json, socket, sys

def send(kind, params=None, timeout=120):
    s = socket.create_connection(("localhost", 9876), timeout=timeout)
    s.sendall(json.dumps({"type": kind, "params": params or {}}).encode())
    buf = b""
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        buf += chunk
        try:
            return json.loads(buf.decode())
        except ValueError:
            continue
    return json.loads(buf.decode())

if __name__ == "__main__":
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    result = send(sys.argv[1], params)
    text = json.dumps(result)
    print(text[:3000])
