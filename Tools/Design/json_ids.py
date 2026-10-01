"""Insert "id" keys into JSON objects of hand-formatted data files without reformatting them.

The drawings (Tools/Design/draw_exterior_sheet.py) and the build read the same data; every decal, light,
functional part and greeble carries an "id" in its own data (author 1. 10. 2026: one source of data). The builders
ignore the key. This module finds the objects by path in the original text and inserts the key right after the
object's opening brace, keeping the file's own layout (one-line or multi-line objects).

    python Tools/Design/json_ids.py --check ArtSource/Ships/Wayfarer/HardSurface/Wayfarer_hs.json
"""
import json
import re
import sys

_WS = re.compile(r"\s*")
_STR = re.compile(r'"(?:[^"\\]|\\.)*"')
_NUM = re.compile(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?")


class Node:
    __slots__ = ("start", "end", "value", "children")

    def __init__(self, start, end, value, children):
        self.start, self.end, self.value, self.children = start, end, value, children


def _skip(text, i):
    return _WS.match(text, i).end()


def parse(text, i=0):
    """A Node tree with the text span of every value; children: dict key -> Node, or list of Nodes."""
    i = _skip(text, i)
    c = text[i]
    if c == "{":
        start, i, children, value = i, i + 1, {}, {}
        i = _skip(text, i)
        if text[i] == "}":
            return Node(start, i + 1, value, children)
        while True:
            i = _skip(text, i)
            m = _STR.match(text, i)
            key = json.loads(m.group(0))
            i = _skip(text, m.end())
            assert text[i] == ":"
            node = parse(text, i + 1)
            children[key], value[key] = node, node.value
            i = _skip(text, node.end)
            if text[i] == ",":
                i += 1
                continue
            assert text[i] == "}", text[i:i + 30]
            return Node(start, i + 1, value, children)
    if c == "[":
        start, i, children = i, i + 1, []
        i = _skip(text, i)
        if text[i] == "]":
            return Node(start, i + 1, [], children)
        while True:
            node = parse(text, i)
            children.append(node)
            i = _skip(text, node.end)
            if text[i] == ",":
                i += 1
                continue
            assert text[i] == "]", text[i:i + 30]
            return Node(start, i + 1, [n.value for n in children], children)
    if c == '"':
        m = _STR.match(text, i)
        return Node(i, m.end(), json.loads(m.group(0)), None)
    for word, val in (("true", True), ("false", False), ("null", None)):
        if text.startswith(word, i):
            return Node(i, i + len(word), val, None)
    m = _NUM.match(text, i)
    return Node(i, m.end(), json.loads(m.group(0)), None)


def at(root, path):
    node = root
    for key in path:
        node = node.children[key]
    return node


def insert_ids(text, assignments):
    """assignments: [(node, id)] with node an object Node; returns the new text. An object that already has an
    "id" is left alone."""
    edits = []
    for node, ident in assignments:
        if "id" in node.value:
            continue
        brace = node.start
        after = text[brace + 1:node.end]
        nl = after.find("\n")
        first_key = after.lstrip()
        if nl != -1 and after[:nl].strip() == "":                  # multi-line object: keep its indent
            line = after[nl + 1:]
            indent = line[:len(line) - len(line.lstrip(" "))]
            edits.append((brace + 1, "\n%s\"id\": %s," % (indent, json.dumps(ident))))
        else:
            edits.append((brace + 1, "\"id\": %s, " % json.dumps(ident) if first_key[:1] != "}" else
                          "\"id\": %s" % json.dumps(ident)))
    for pos, s in sorted(edits, reverse=True):
        text = text[:pos] + s + text[pos:]
    return text


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--check":
        raw = open(sys.argv[2], encoding="utf-8").read()
        assert parse(raw).value == json.loads(raw)
        print("JSONIDS parse OK", sys.argv[2])
