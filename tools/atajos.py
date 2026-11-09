#!/usr/bin/env python3
"""Read keyboard bindings from the active Niri KDL configuration."""

import glob
import json
import os
import re
import shlex

CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
NIRI_CONFIG = os.environ.get("NIRI_CONFIG", os.path.join(CONFIG_HOME, "niri", "config.kdl"))
BIND_RE = re.compile(r"(?m)^\s*([A-Za-z0-9_+.-]+)\s*\{([^{}]*)\}", re.S)
SECTION_RE = re.compile(r"^\s*//\s*-{2,}\s*(.+?)\s*-{2,}\s*$")


def config_files():
    paths = [NIRI_CONFIG]
    paths.extend(sorted(glob.glob(os.path.join(os.path.dirname(NIRI_CONFIG), "config.d", "*.kdl"))))
    paths.extend(sorted(glob.glob(os.path.join(os.path.dirname(NIRI_CONFIG), "*.kdl"))))
    seen = set()
    for path in paths:
        if path not in seen and os.path.isfile(path):
            seen.add(path)
            yield path


def command_tokens(body):
    match = re.search(r"\bspawn\s+((?:\"(?:\\.|[^\"\\])*\"\s*)+)", body)
    if not match:
        return []
    try:
        return shlex.split(match.group(1))
    except ValueError:
        return []


def describe(tokens, body):
    if tokens:
        if "quickshell" in os.path.basename(tokens[0]) and "ipc" in tokens:
            try:
                call = tokens.index("call")
                target, function = tokens[call + 1:call + 3]
                return "", "K4 · " + target + " · " + function
            except (ValueError, IndexError):
                pass
        return "", " ".join(tokens[:8])

    action = re.search(r"\b(close-window|toggle-overview|focus-window|focus-workspace|move-window-to-workspace|switch-layout|consume-or-expel-window-left|consume-or-expel-window-right)\b", body)
    if action:
        return "", action.group(1).replace("-", " ")
    return "", "Niri action"


def read_bindings():
    result = []
    for path in config_files():
        section = "General"
        try:
            lines = open(path, encoding="utf-8").read().splitlines()
        except OSError:
            continue

        # Parse line-oriented KDL comments for human-readable groups.
        for line in lines:
            section_match = SECTION_RE.match(line)
            if section_match:
                section = section_match.group(1).strip().capitalize()

            for match in BIND_RE.finditer(line):
                combo, body = match.groups()
                tokens = command_tokens(body)
                phrase, detail = describe(tokens, body)
                result.append({
                    "combo": combo.strip(),
                    "hace": detail,
                    "frase": phrase,
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
