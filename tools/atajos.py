#!/usr/bin/env python3
"""Read active keyboard bindings from the Niri KDL configuration."""

import glob
import json
import os
import re
import shlex

CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
NIRI_CONFIG = os.environ.get("NIRI_CONFIG", os.path.join(CONFIG_HOME, "niri", "config.kdl"))
INCLUDE_RE = re.compile(r'^\s*include\s+"((?:\\.|[^"\\])*)"', re.MULTILINE)
BIND_START_RE = re.compile(r"^\s*([A-Za-z0-9_+.-]+)(?:\s+[^{}\n]+)?\s*\{", re.MULTILINE)
SECTION_RE = re.compile(r"^\s*//\s*-{2,}\s*(.+?)\s*-{2,}\s*$")


def matching_brace(text, opening):
    depth = 0
    quoted = False
    escaped = False
    line_comment = False
    block_comment = False
    i = opening
    while i < len(text):
        char = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if line_comment:
            if char == "\n":
                line_comment = False
        elif block_comment:
            if char == "*" and nxt == "/":
                block_comment = False
                i += 1
        elif quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == "/" and nxt == "/":
            line_comment = True
            i += 1
        elif char == "/" and nxt == "*":
            block_comment = True
            i += 1
        elif char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def included_files(path, seen=None):
    if seen is None:
        seen = set()
    path = os.path.realpath(path)
    if path in seen or not os.path.isfile(path):
        return
    seen.add(path)
    yield path
    try:
        source = open(path, encoding="utf-8").read()
    except OSError:
        return
    for match in INCLUDE_RE.finditer(source):
        raw = match.group(1)
        try:
            include = bytes(raw, "utf-8").decode("unicode_escape")
        except UnicodeDecodeError:
            include = raw
        if not os.path.isabs(include):
            include = os.path.join(os.path.dirname(path), include)
        for candidate in sorted(glob.glob(include)):
            yield from included_files(candidate, seen)


def binding_blocks(source):
    binds_match = re.search(r"(?m)^\s*binds\s*\{", source)
    if not binds_match:
        return
    opening = source.find("{", binds_match.start())
    closing = matching_brace(source, opening)
    if closing < 0:
        return
    body = source[opening + 1:closing]
    offset = opening + 1
    cursor = 0
    while True:
        match = BIND_START_RE.search(body, cursor)
        if not match:
            break
        combo = match.group(1)
        if combo == "binds":
            cursor = match.end()
            continue
        open_at = body.find("{", match.start(), match.end())
        close_at = matching_brace(body, open_at)
        if close_at < 0:
            break
        before = body[:match.start()]
        section = "General"
        for line in before.splitlines():
            section_match = SECTION_RE.match(line)
            if section_match:
                section = section_match.group(1).strip().capitalize()
        yield combo, body[open_at + 1:close_at], section
        cursor = close_at + 1


def command_tokens(body):
    match = re.search(r"\bspawn\s+((?:\"(?:\\.|[^\"\\])*\"[ \t]*)+)", body)
    if not match:
        return []
    try:
        return shlex.split(match.group(1))
    except ValueError:
        return []


def describe(tokens, body):
    if tokens:
        if os.path.basename(tokens[0]) == "quickshell" and "ipc" in tokens:
            try:
                call = tokens.index("call")
                target, function = tokens[call + 1:call + 3]
                return "K4 · " + target + " · " + function
            except (ValueError, IndexError):
                pass
        return " ".join(tokens[:8])
    shell_spawn = re.search(r'\bspawn-sh\s+"((?:\\.|[^\"\\])*)"', body)
    if shell_spawn:
        return shell_spawn.group(1)
    action = re.search(
        r"\b(close-window|toggle-overview|focus-window|focus-workspace|"
        r"move-window-to-workspace-down|move-window-to-workspace-up|"
        r"switch-layout|consume-or-expel-window-left|consume-or-expel-window-right)\b",
        body,
    )
    return action.group(1).replace("-", " ") if action else "Niri action"


def read_bindings():
    result = []
    for path in included_files(NIRI_CONFIG):
        try:
            source = open(path, encoding="utf-8").read()
        except OSError:
            continue
        for combo, body, section in binding_blocks(source):
            detail = describe(command_tokens(body), body)
            result.append({
                "combo": combo,
                "hace": detail,
                "frase": "",
                "detalle": detail,
                "detalleFrase": "",
                "seccion": section,
                "archivo": os.path.basename(path),
            })
    return result


def main():
    bindings = read_bindings()
    print(json.dumps({"total": len(bindings), "atajos": bindings}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
