"""
Lists the lines a commit added or changed in its .lua files, so the per-commit Lua report can stay on
the commit author's own lines.

Usage: python3 changed_lines.py <commit> <output.json>

Writes a JSON object mapping each .lua file the commit added or edited to the line numbers it added or
changed there, numbered as in the commit. Renames are detected, so a moved file only counts the lines
edited along the way; files that end up with no added or changed lines are left out.
"""

import codecs
import json
import re
import subprocess
import sys

HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def unquote_path(path: str) -> str:
    """Undo git's C-style quoting, which it applies to paths holding quotes, backslashes, or control characters."""
    if not path.startswith('"'):
        return path

    return codecs.escape_decode(path[1:-1].encode("utf-8"))[0].decode("utf-8")


def parse_diff(diff: str) -> dict[str, list[int]]:
    changed: dict[str, set[int]] = {}
    current = None
    in_header = False

    for line in diff.split("\n"):
        if line.startswith("diff --git "):
            current = None
            in_header = True
            continue

        # Only the file header carries the "+++" line; inside a hunk the same prefix is an added line.
        if in_header and line.startswith("+++ "):
            # git ends the path with a tab when it contains a space.
            target = line[4:].removesuffix("\t")
            current = None if target == "/dev/null" else unquote_path(target)
            continue

        match = HUNK_HEADER.match(line)

        if match:
            in_header = False

            if current is None:
                continue

            start = int(match.group(1))
            count = 1 if match.group(2) is None else int(match.group(2))
            changed.setdefault(current, set()).update(range(start, start + count))

    return {path: sorted(numbers) for path, numbers in sorted(changed.items()) if numbers}


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python3 changed_lines.py <commit> <output.json>")
        sys.exit(1)

    commit, output_path = sys.argv[1], sys.argv[2]

    diff = subprocess.run(
        ["git", "-c", "core.quotePath=false", "diff-tree", "-p", "-U0", "-M", "--no-prefix", "--no-color",
         "--no-ext-diff", "--no-textconv", "--root", "-r", commit, "--", "*.lua"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    ).stdout

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(parse_diff(diff), file, ensure_ascii=False)


if __name__ == "__main__":
    main()
