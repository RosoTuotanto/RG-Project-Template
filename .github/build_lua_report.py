"""
Builds the markdown body for a Lua report, used by the Lua report workflows.

Takes a luacheck report and a suggested style diff (either may be empty) and assembles either a
commit comment body or a job summary section. Prints "content" or "empty" to stdout so the caller
can skip posting when there is nothing to report.

In comment mode, --changed-lines limits the luacheck findings to the lines the commit added or
changed; syntax errors are always kept, because they stop the game wherever they are. Findings are
listed one per line with a link to the line and a plain-language explanation of each warning code.

The comment body starts with an HTML marker comment that the push workflow uses to detect commits
that already have a report, keeping re-runs from posting duplicates.
"""

import argparse
import json
import re
import sys
from urllib.parse import quote

MARKER = "<!-- lua-report -->"

# Stay well under GitHub's comment size limit; job summaries allow 1 MiB per step.
COMMENT_MAX_CHARS = 60000
SUMMARY_MAX_CHARS = 900 * 1024

TRUNCATION_NOTICE = "... (truncated; see the workflow run log for the full output)"

# Codes that mean Lua 5.1 cannot load the file. Luacheck's other E codes (E021 to E023) are about its own
# "-- luacheck:" comments and do not affect the game.
LOAD_ERRORS = {"E011", "E033"}

TOTAL_LINE = re.compile(r"Total:\s*(\d+)\s+warnings?\s*/\s*(\d+)\s+errors?", re.IGNORECASE)
FINDING = re.compile(r"^\s*(?P<path>.+?):(?P<line>\d+):(?P<column>\d+): \((?P<code>[EW]\d+)\) (?P<message>.*)$")
ROUTINE_LINE = re.compile(r"^\s*$|^Checking |^Total: ")

WHITESPACE_HELP = "Extra spaces or tabs at the end of a line, or a line with only spaces. Harmless; many editors can remove them automatically."
SHADOWING_HELP = "A new local with the same name as a variable that already exists here hides the old one, which makes it easy to change the wrong one. A different name avoids mix-ups."
EMPTY_BLOCK_HELP = "This block is empty. Remove it, or add the code that was meant to go in it."
SYNTAX_HINT = "The cause is often a missing `end`, bracket, or quote at or just before the reported line."
UNDEFINED_FIELD_HELP = "This uses a field of a built-in library that does not exist, such as `string.lenght`. Usually a typo in the function name."
READ_ONLY_HELP = "This overwrites a built-in Lua or Solar2D name, which can break other code that relies on it. Pick a different name."
COMPOUND_HINT = "Solar2D runs Lua 5.1, which has no `+=`, `-=` or similar operators: write `score = score + 1` instead of `score += 1`."
LUACHECK_COMMENT_HELP = "This is about a `-- luacheck:` comment, which only tells luacheck what to check. It does not affect the game."
UNBALANCED_HELP = "The two sides of this assignment have a different number of values"

EXPLANATIONS = {
    "E011": f"Lua cannot read the file from this point on, so the game stops with an error when it loads the file. {SYNTAX_HINT}",
    "E021": f"{LUACHECK_COMMENT_HELP} Luacheck did not understand it, so check its spelling.",
    "E022": f"{LUACHECK_COMMENT_HELP} A `push` needs a matching `pop` later in the file.",
    "E023": f"{LUACHECK_COMMENT_HELP} A `pop` needs a matching `push` earlier in the file.",
    "E033": f"Lua cannot read the file from this point on, so the game stops with an error when it loads the file. {COMPOUND_HINT}",
    "W111": "This creates a global variable, which every file can see and overwrite by accident. If only this file needs it, add `local` in front of the first assignment.",
    "W112": "This changes a global variable that is not defined anywhere luacheck can see. If it should belong to this file only, create it with `local`.",
    "W113": "This uses a name that is not defined anywhere luacheck can see. Check the spelling, or whether a `local` or `require` is missing.",
    "W121": READ_ONLY_HELP,
    "W122": READ_ONLY_HELP,
    "W142": UNDEFINED_FIELD_HELP,
    "W143": UNDEFINED_FIELD_HELP,
    "W211": "This local variable is created but never used. You can remove it if it is not needed.",
    "W212": "This function argument is never used. Harmless; you can remove it, or name it `_` to show it is not needed.",
    "W213": "This loop variable is never used. You can name it `_` to show it is not needed.",
    "W214": "A name that starts with `_` marks something as unused, but this one is used. Remove the `_` from the start of the name.",
    "W221": "This local variable is read but never given a value, so it is always `nil`.",
    "W231": "This local variable is given a value that is never read. You can remove it if it is not needed.",
    "W232": "This function argument is given a new value that is never read. You can remove that line if it is not needed.",
    "W233": "This loop variable is given a new value that is never read. You can remove that line if it is not needed.",
    "W241": "This local variable is changed, for example by setting a field, but never read, so the change has no effect. You can remove it if it is not needed.",
    "W311": "The value given to this variable is replaced or dropped before anything uses it.",
    "W312": "The value passed in for this argument is replaced before anything uses it, so whatever the caller passed is lost.",
    "W313": "The value of this loop variable is replaced before anything uses it.",
    "W314": "This table field is given a value twice, and the first value is lost before anything uses it. Often one of the two names is a typo.",
    "W321": "This reads a local variable before it has been given a value, so it is still `nil` here.",
    "W331": "This variable is given a value that is then changed but never read, so the work has no effect.",
    "W341": "This changes a field of a local variable that has no value yet, which stops the game with an error. Give the variable a value first, such as `{}`.",
    "W411": SHADOWING_HELP,
    "W412": SHADOWING_HELP,
    "W413": SHADOWING_HELP,
    "W421": SHADOWING_HELP,
    "W422": SHADOWING_HELP,
    "W423": SHADOWING_HELP,
    "W431": SHADOWING_HELP,
    "W432": SHADOWING_HELP,
    "W433": SHADOWING_HELP,
    "W511": "This code can never run, usually because a `return` or `break` comes before it.",
    "W512": "This loop always stops during its first round, usually because of a `return` or `break` inside it.",
    "W521": "Solar2D runs Lua 5.1, which has no labels or `goto`, so Lua cannot read this file and the game stops with an error when it loads it.",
    "W531": f"{UNBALANCED_HELP}: the extra values on the right are dropped.",
    "W532": f"{UNBALANCED_HELP}: the extra names on the left get `nil`.",
    "W541": EMPTY_BLOCK_HELP,
    "W542": EMPTY_BLOCK_HELP,
    "W551": "An extra `;` that does nothing. You can remove it.",
    "W571": "This loop counts down from a bigger number to a smaller one, but without a negative step it never runs. Add `, -1` as the step.",
    "W581": "This `not ( ... )` comparison can be written more simply with the opposite operator, for example `x ~= y` instead of `not ( x == y )`.",
    "W582": "`not` applies before the comparison here, so `not x == y` means `( not x ) == y`, which is rarely what was meant. Write `x ~= y`, or put brackets around the comparison.",
    "W611": WHITESPACE_HELP,
    "W612": WHITESPACE_HELP,
    "W613": WHITESPACE_HELP,
    "W614": WHITESPACE_HELP,
    "W621": "The indentation mixes spaces and tabs. Use tabs only.",
    "W631": "The line is longer than the project's line length limit. Splitting it makes it easier to read.",
}


def read_text(path: str) -> str:
    if not path:
        return ""

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as file:
            return file.read().strip("\n")
    except FileNotFoundError:
        return ""


def luacheck_counts(report: str) -> tuple[int, int]:
    """Return (warnings, errors) from the last luacheck Total line, or (0, 0) if none exists."""
    counts = TOTAL_LINE.findall(report)

    if not counts:
        return 0, 0

    warnings, errors = counts[-1]
    return int(warnings), int(errors)


def luacheck_has_content(report: str) -> bool:
    if not report.strip():
        return False

    warnings, errors = luacheck_counts(report)

    if warnings > 0 or errors > 0:
        return True

    # Unreadable files and other tool failures do not show up in the totals; fail open so they are visible.
    if "I/O error" in report or not TOTAL_LINE.search(report):
        return True

    return False


def parse_findings(report: str) -> tuple[list[dict], list[str]]:
    """Split a luacheck report into findings and any lines that are neither findings nor routine output."""
    findings = []
    unexpected = []

    for line in report.split("\n"):
        match = FINDING.match(line)

        if match:
            finding = match.groupdict()
            finding["line"] = int(finding["line"])
            findings.append(finding)
        elif not ROUTINE_LINE.match(line):
            unexpected.append(line.strip())

    return findings, unexpected


def load_changed_lines(path: str) -> dict[str, set[int]] | None:
    if not path:
        return None

    with open(path, "r", encoding="utf-8") as file:
        return {name: set(numbers) for name, numbers in json.load(file).items()}


def fence(content: str, language: str) -> str:
    """Wrap content in a code fence longer than any backtick run inside it."""
    longest_run = max((len(run) for run in re.findall(r"`+", content)), default=0)
    ticks = "`" * max(3, longest_run + 1)
    return f"{ticks}{language}\n{content}\n{ticks}"


def code_span(text: str) -> str:
    """Wrap text in an inline code span that survives backticks inside it."""
    longest_run = max((len(run) for run in re.findall(r"`+", text)), default=0)
    ticks = "`" * (longest_run + 1)
    padding = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{ticks}{padding}{text}{padding}{ticks}"


def truncate(content: str, max_chars: int) -> str:
    if len(content) <= max_chars:
        return content

    cut = content.rfind("\n", 0, max(max_chars - len(TRUNCATION_NOTICE) - 1, 0))

    if cut <= 0:
        cut = max(max_chars - len(TRUNCATION_NOTICE) - 1, 0)

    return f"{content[:cut]}\n{TRUNCATION_NOTICE}"


def section(summary: str, body: str) -> str:
    return f"<details>\n<summary>{summary}</summary>\n\n{body}\n\n</details>"


def plural(count: int, word: str) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def format_finding(finding: dict, blob_url: str) -> str:
    location = f"{code_span(finding['path'])} line {finding['line']}"

    if blob_url:
        location = f"[{location}]({blob_url}/{quote(finding['path'])}#L{finding['line']})"

    return f"- {location}: {code_span(finding['message'])} ({finding['code']})"


def format_explanations(findings: list[dict]) -> str:
    codes = sorted({finding["code"] for finding in findings if finding["code"] in EXPLANATIONS})
    return "\n".join(f"- **{code}**: {EXPLANATIONS[code]}" for code in codes)


def build_comment(luacheck_report: str, style_diff: str, changed_lines: dict[str, set[int]] | None, sha: str,
                  author_username: str, author_name: str, run_url: str, blob_url: str) -> tuple[str, bool]:
    findings, unexpected = parse_findings(luacheck_report)

    if changed_lines is not None:
        findings = [
            finding for finding in findings
            if finding["code"] in LOAD_ERRORS or finding["line"] in changed_lines.get(finding["path"], set())
        ]

    errors = [finding for finding in findings if finding["code"] in LOAD_ERRORS]
    warnings = [finding for finding in findings if finding["code"] not in LOAD_ERRORS]
    include_diff = bool(style_diff.strip())

    if not errors and not warnings and not unexpected and not include_diff:
        return "", False

    # A code span keeps a bare git name from mentioning anyone or rendering its own Markdown.
    mention = f"@{author_username}" if author_username else (code_span(author_name) if author_name else "")
    greeting = f"{mention} " if mention else ""
    scope = " It looks only at the lines this commit added or changed." if changed_lines is not None else ""

    lines = [
        MARKER,
        f"{greeting}Automated Lua check for commit {sha[:7]}.{scope} "
        "Everything below is a suggestion: nothing was changed, and you are free to ignore it.",
    ]

    if errors:
        lines.append("")
        lines.append("**Syntax error:** Lua cannot read the file below, so the game stops with an error when it loads that file.")
        lines.append("")
        lines.extend(format_finding(finding, blob_url) for finding in errors)
        lines.append("")
        lines.append(" ".join(hint for code, hint in (("E011", SYNTAX_HINT), ("E033", COMPOUND_HINT))
                              if any(finding["code"] == code for finding in errors)))

    if unexpected:
        lines.append("")
        lines.append("Luacheck also printed this:")
        lines.append("")
        lines.append(fence("\n".join(unexpected), "text"))

    footer = f"\nFull log: {run_url}" if run_url else ""
    warning_list = "\n".join(format_finding(finding, blob_url) for finding in warnings)
    explanations = format_explanations(warnings)

    # Fit the body under the size cap: overhead first, then shrink the diff, then the warning list.
    overhead = sum(len(line) + 1 for line in lines) + len(explanations) + len(footer) + 400
    budget = COMMENT_MAX_CHARS - overhead

    if len(warning_list) + len(style_diff) > budget:
        if include_diff and len(warning_list) > budget // 2:
            warning_list = truncate(warning_list, budget // 2)

        style_diff = truncate(style_diff, max(budget - len(warning_list), 0))
        warning_list = truncate(warning_list, budget)

    if warnings:
        body = warning_list

        if explanations:
            body += f"\n\nWhat these mean:\n\n{explanations}"

        lines.append("")
        lines.append(section(f"Luacheck: {plural(len(warnings), 'warning')}", body))

    if include_diff:
        lines.append("")
        lines.append(section("Suggested style changes", fence(style_diff, "diff")))

    if footer:
        lines.append(footer)

    return "\n".join(lines) + "\n", True


def build_summary(luacheck_report: str, style_diff: str, title: str) -> tuple[str, bool]:
    include_luacheck = luacheck_has_content(luacheck_report)
    include_diff = bool(style_diff.strip())

    if not include_luacheck and not include_diff:
        return "", False

    lines = [title or "## Lua report"]
    sections = []

    if include_luacheck:
        warnings, errors = luacheck_counts(luacheck_report)
        heading = f"Luacheck report ({plural(warnings, 'warning')}, {plural(errors, 'error')})"
        sections.append(("luacheck", heading, luacheck_report, "text"))

    if include_diff:
        sections.append(("diff", "Suggested style changes", style_diff, "diff"))

    findings, _ = parse_findings(luacheck_report)
    explanations = format_explanations(findings)

    # Fit the body under the size cap: overhead first, then shrink the diff, then the luacheck report.
    overhead = sum(len(line) + 2 for line in lines) + len(explanations) + 200
    budget = SUMMARY_MAX_CHARS - overhead
    contents = {name: content for name, _, content, _ in sections}

    if sum(len(content) for content in contents.values()) > budget:
        if "luacheck" in contents and len(contents["luacheck"]) > budget // 2 and "diff" in contents:
            contents["luacheck"] = truncate(contents["luacheck"], budget // 2)

        used_by_luacheck = len(contents.get("luacheck", ""))

        if "diff" in contents:
            contents["diff"] = truncate(contents["diff"], max(budget - used_by_luacheck, 0))

        if "luacheck" in contents and "diff" not in contents:
            contents["luacheck"] = truncate(contents["luacheck"], budget)

    for name, heading, _, language in sections:
        body = fence(contents[name], language)

        if name == "luacheck" and explanations:
            body += f"\n\nWhat these mean:\n\n{explanations}"

        lines.append("")
        lines.append(section(heading, body))

    return "\n".join(lines) + "\n", True


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Lua report comment or summary body.")
    parser.add_argument("mode", choices=["comment", "summary"])
    parser.add_argument("--luacheck", default="", help="path to the luacheck report file")
    parser.add_argument("--diff", default="", help="path to the suggested style diff file")
    parser.add_argument("--changed-lines", default="", help="JSON of the lines the commit changed, from changed_lines.py (comment mode)")
    parser.add_argument("--sha", default="", help="full commit sha (comment mode)")
    parser.add_argument("--author-username", default="", help="GitHub username to mention (comment mode)")
    parser.add_argument("--author-name", default="", help="fallback author display name (comment mode)")
    parser.add_argument("--run-url", default="", help="URL of the workflow run (comment mode)")
    parser.add_argument("--blob-url", default="", help="URL prefix for linking findings to file lines at the commit (comment mode)")
    parser.add_argument("--title", default="", help="heading line (summary mode)")
    parser.add_argument("--output", required=True, help="path to write the body to")
    args = parser.parse_args()

    luacheck_report = read_text(args.luacheck)
    style_diff = read_text(args.diff)

    if args.mode == "comment":
        body, has_content = build_comment(
            luacheck_report=luacheck_report,
            style_diff=style_diff,
            changed_lines=load_changed_lines(args.changed_lines),
            sha=args.sha,
            author_username=args.author_username,
            author_name=args.author_name,
            run_url=args.run_url,
            blob_url=args.blob_url,
        )
    else:
        body, has_content = build_summary(luacheck_report, style_diff, args.title)

    with open(args.output, "w", encoding="utf-8") as file:
        file.write(body)

    print("content" if has_content else "empty")


if __name__ == "__main__":
    main()
    sys.exit(0)
