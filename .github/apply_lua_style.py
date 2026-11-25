"""
------------------------------------------------------------------------------------------------------
"Lua Style Suggestions", copyright 2025-2026 Eetu Rantanen; MIT License.
------------------------------------------------------------------------------------------------------

The indentation engine is based on "Lua beautifier", written in Perl, copyright 2011 Paul Kulchenko;
MIT License. Source: https://notebook.kulchenko.com/programming/lua-beautifier-in-55-lines-of-perl

Rewrites a Lua file in place so that CI can diff the result against the original and post the diff as
a suggestion. The script never touches version control itself. With --lines-json, only the listed lines
of each file are restyled and every other line is kept byte for byte, so a report can stay on the lines
a commit actually changed; a local is then renamed only when every line it appears on is listed.

What it does:
    - recalculates the indentation of every code line and applies it using tabs
        - one level per line that opens blocks or brackets, so a callback such as
          timer.performWithDelay( 100, function() indents its body once, not once per opener
        - handles logical operators (and/or/not) that split an expression across lines
    - collapses whitespace runs in code to single spaces
    - converts snake_case locals in code to camelCase: names the file declares with local, as function
      parameters, or as loop variables; globals stay as they are, because other files may use them

What it never touches:
    - string literals and comment text, including long brackets of any level ([[ ]], [==[ ]==]) and
      strings continued onto the next line with a backslash, are preserved verbatim
    - identifiers in ALL CAPS (constants)
    - identifiers starting with one underscore and containing no other underscores (private naming)
    - identifiers starting with two underscores (Lua reserved names such as __index)
    - identifiers directly after "." or ":" (table fields and methods; external modules and plugins
      may rely on snake_case names, e.g. Solar2D's OpenSSL plugin uses openssl.get_cipher())
    - identifiers used as keys in table constructors, so keys stay aligned with the protected
      field-access sites that read them
    - identifiers whose camelCase form would be a Lua keyword, such as end_
    - identifiers whose camelCase form already appears in the file's code, or that would become the same
      camelCase name as another identifier, because the rename would merge two variables into one

Files whose blocks and brackets do not balance, which usually means a syntax error, are left untouched,
because every indentation suggestion after the error would be a guess.

Known limitations:
    - table-key detection is line-based; a statement assignment at line start inside a multiline table
      constructor (e.g. inside an onComplete function value) looks like a key, so a name seen in a key
      position is never renamed anywhere in the file

------------------------------------------------------------------------------------------------------
"""

import argparse
import json
import re
import sys
from collections import Counter

INDENT = "\t"

IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
STARTS_WITH_LOGICAL = re.compile(r"^(and|or|not)\b")
ENDS_WITH_LOGICAL = re.compile(r"\b(and|or|not)$")

LONG_BRACKET_OPEN = re.compile(r"\[(=*)\[")

NAME_LIST = r"[A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*"
LOCAL_FUNCTION = re.compile(r"\blocal\s+function\s+([A-Za-z_][A-Za-z0-9_]*)")
LOCAL_NAMES = re.compile(rf"\blocal\s+(?!function\b)({NAME_LIST})")
FOR_NAMES = re.compile(rf"\bfor\s+({NAME_LIST})\s*(?:=|in\b)")
PARAMETERS = re.compile(r"\bfunction\b[\w.:\s]*\(([^)]*)\)")
NAMED_FUNCTION = re.compile(r"\b(local\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")

STRUCTURE_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|[(){}]")
OPENERS = {"(", "{", "function", "then", "do", "repeat"}
CLOSERS = {")", "}", "end", "until", "elseif"}
STARTS_WITH_CLOSER = re.compile(r"(?:end|until|else|elseif)\b|[)}]")

KEYWORDS = {
    "and", "break", "do", "else", "elseif", "end", "false", "for", "function", "if", "in", "local", "nil", "not",
    "or", "repeat", "return", "then", "true", "until", "while",
}


def find_string_end(line: str, start: int, quote: str) -> tuple[int, bool]:
    """Return the index of the closing quote of a string whose content starts at line[start], or -1, and
    whether the string continues on the next line because the line ends in a backslash escape."""
    index = start

    while index < len(line):
        char = line[index]

        if char == "\\":
            if index == len(line) - 1:
                return -1, True

            index += 2
            continue

        if char == quote:
            return index, False

        index += 1

    return -1, False


def split_segments(line: str, pending_close: str) -> tuple[list[tuple[str, str]], str]:
    """Split a line into (kind, text) segments and return them with the text that closes a string or long
    bracket still open at line end ("" when nothing is open).

    Kinds: "code", "string" (quoted literal), "comment" (line comment), and "longbracket" (long bracket
    content of any level, both multiline strings and --[[ ]] comments, and the part of a quoted string
    that a backslash at the end of the previous line continued onto this one).
    """
    segments = []
    index = 0

    if pending_close in ("\"", "'"):
        closer, continues = find_string_end(line, 0, pending_close)

        if closer == -1:
            return [("longbracket", line)], pending_close if continues else ""

        segments.append(("longbracket", line[:closer + 1]))
        index = closer + 1
    elif pending_close:
        closer = line.find(pending_close)

        if closer == -1:
            return [("longbracket", line)], pending_close

        segments.append(("longbracket", line[:closer + len(pending_close)]))
        index = closer + len(pending_close)

    code_start = index

    while index < len(line):
        char = line[index]

        if char in "\"'":
            if index > code_start:
                segments.append(("code", line[code_start:index]))

            end, continues = find_string_end(line, index + 1, char)

            if end == -1:
                segments.append(("string", line[index:]))
                return segments, char if continues else ""

            segments.append(("string", line[index:end + 1]))
            index = end + 1
            code_start = index
            continue

        is_comment = line.startswith("--", index)
        opener = LONG_BRACKET_OPEN.match(line, index + 2 if is_comment else index)

        if is_comment or opener:
            if index > code_start:
                segments.append(("code", line[code_start:index]))

            if not opener:
                segments.append(("comment", line[index:]))
                return segments, ""

            long_close = f"]{opener.group(1)}]"
            closer = line.find(long_close, opener.end())

            if closer == -1:
                segments.append(("longbracket", line[index:]))
                return segments, long_close

            segments.append(("longbracket", line[index:closer + len(long_close)]))
            index = closer + len(long_close)
            code_start = index
            continue

        index += 1

    if code_start < len(line):
        segments.append(("code", line[code_start:]))

    return segments, ""


class CodeContext:
    """Carries conversion state across code segments: the last two non-whitespace characters seen on
    the current line, the number of table-constructor braces still open across the file, and the
    renames planned for the file."""

    def __init__(self, renames: dict[str, str]) -> None:
        self.prev = ""
        self.depth = 0
        self.renames = renames

    def feed(self, text: str) -> None:
        self.depth += text.count("{") - text.count("}")
        non_whitespace = re.sub(r"\s+", "", text)

        if non_whitespace:
            self.prev = (self.prev + non_whitespace)[-2:]


def camel_case_word(word: str) -> str:
    """Convert one snake_case identifier to camelCase, or return it unchanged if it is protected."""
    if word.isupper() or word.startswith("__") or "_" not in word:
        return word

    # A single leading underscore with no other underscores marks a private name.
    if word.startswith("_") and word.count("_") == 1:
        return word

    components = [part for part in word.lstrip("_").lower().split("_") if part]

    if not components:
        return word

    camel_case = components[0] + "".join(part.capitalize() for part in components[1:])
    camel_case = f"_{camel_case}" if word.startswith("_") else camel_case

    # "end_" would become "end", which no longer parses.
    return word if camel_case in KEYWORDS else camel_case


def is_protected_position(text: str, end_index: int, context: CodeContext) -> bool:
    """Check whether the identifier ending at end_index sits in a position that must not be renamed."""
    # Field or method access: names after "." or ":" (but not after the ".." concat operator).
    if context.prev.endswith(":"):
        return True

    if context.prev.endswith(".") and not context.prev.endswith(".."):
        return True

    return is_table_key(text, end_index, context)


def is_table_key(text: str, end_index: int, context: CodeContext) -> bool:
    """Table-constructor keys: "name =" directly after "{", ",", or at line start inside an open constructor.
    The same shape is also an assignment inside a function written in a constructor, which a line-based
    reader cannot tell apart, so plan_renames never renames a name seen here."""
    if context.depth > 0:
        follower = text[end_index:].lstrip()

        if follower.startswith("=") and not follower.startswith("=="):
            if context.prev == "" or context.prev.endswith("{") or context.prev.endswith(","):
                return True

    return False


def table_keys(text: str, context: CodeContext) -> set[str]:
    """Return the names in one code segment that sit where a table-constructor key can, feeding the context."""
    keys = set()
    position = 0

    for match in IDENTIFIER.finditer(text):
        start, end = match.span()
        context.feed(text[position:start])

        if is_table_key(text, end, context):
            keys.add(match.group())

        context.feed(match.group())
        position = end

    context.feed(text[position:])
    return keys


def convert_code_text(text: str, context: CodeContext) -> str:
    """Apply the camelCase conversion to one code segment, leaving protected identifiers as is."""
    output = []
    position = 0

    for match in IDENTIFIER.finditer(text):
        start, end = match.span()
        before = text[position:start]
        context.feed(before)

        word = match.group()
        output.append(before)

        if is_protected_position(text, end, context):
            output.append(word)
        else:
            output.append(context.renames.get(word, word))

        context.feed(word)
        position = end

    output.append(text[position:])
    context.feed(text[position:])
    return "".join(output)


def declared_locals(code_text: str) -> set[str]:
    """Return the names one line's code declares as locals: local statements, local functions, function
    parameters, and loop variables."""
    declared = set(LOCAL_FUNCTION.findall(code_text))

    for pattern in (LOCAL_NAMES, FOR_NAMES, PARAMETERS):
        for name_list in pattern.findall(code_text):
            declared.update(IDENTIFIER.findall(name_list))

    return declared


def plan_renames(lines: list[str], allowed_lines: set[int] | None) -> dict[str, str]:
    """Map each snake_case local the file declares to its camelCase form. Globals are left out, because
    other files may use them under the old name, and so are names seen in a table-key position. So is
    every rename that would merge two names: one whose camelCase form already appears in the code, and two
    names that would both become the same name. When only allowed_lines are restyled, a name is renamed
    only if every line it appears on is allowed, since renaming some of its uses and not the others would
    break the code."""
    occurrences: dict[str, set[int]] = {}
    declared: set[str] = set()
    global_functions: set[str] = set()
    keys: set[str] = set()
    context = CodeContext({})
    pending_close = ""

    for number, line in enumerate(lines, start=1):
        segments, pending_close = split_segments(line, pending_close)
        code_text = " ".join(text for kind, text in segments if kind == "code")
        context.prev = ""

        for kind, text in segments:
            if kind == "code":
                keys.update(table_keys(text, context))

        declared.update(declared_locals(code_text))
        global_functions.update(name for is_local, name in NAMED_FUNCTION.findall(code_text) if not is_local)

        for word in IDENTIFIER.findall(code_text):
            occurrences.setdefault(word, set()).add(number)

    # A global function that shares its name with a local elsewhere in the file is still a global, and a
    # name that also sits in a table-key position may be an assignment to the local that must keep its name.
    renames = {word: camel_case_word(word) for word in declared - global_functions - keys}
    renames = {word: camel for word, camel in renames.items() if camel != word and camel not in occurrences}

    if allowed_lines is not None:
        renames = {word: camel for word, camel in renames.items() if occurrences[word] <= allowed_lines}

    targets = Counter(renames.values())
    return {word: camel for word, camel in renames.items() if targets[camel] == 1}


def collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def structure_tokens(code_text: str) -> list[bool]:
    """Return the block and bracket openers (True) and closers (False) in a line's code, in order."""
    tokens = []

    for match in STRUCTURE_TOKEN.finditer(code_text):
        word = match.group()

        if word == "else":
            tokens.extend([False, True])
        elif word in OPENERS:
            tokens.append(True)
        elif word in CLOSERS:
            tokens.append(False)

    return tokens


class Nesting:
    """Tracks open blocks and brackets as one group per line that opened them, so the indentation depth
    is the number of lines whose openers are still unclosed."""

    def __init__(self) -> None:
        self.groups: list[int] = []
        self.unbalanced = False

    def open_group(self) -> None:
        self.groups.append(1)

    def feed(self, code_text: str) -> int:
        """Consume one line's code and return the depth the line itself belongs at."""
        leading_close = bool(STARTS_WITH_CLOSER.match(code_text))
        line_depth = len(self.groups)
        opened_here = 0
        seen_opener = False

        for is_opener in structure_tokens(code_text):
            if is_opener:
                opened_here += 1
                seen_opener = True
            elif opened_here:
                opened_here -= 1
            elif self.groups:
                # A line that starts by closing, like "end )", "end, 1 )" or "end } )", sits at its opener's depth.
                if leading_close and not seen_opener:
                    line_depth = min(line_depth, len(self.groups) - 1)

                self.groups[-1] -= 1

                if not self.groups[-1]:
                    self.groups.pop()
            else:
                self.unbalanced = True

        if opened_here:
            # "end, function()" reopens the group it closed into, so its body is not nested a level deeper.
            if leading_close and len(self.groups) == line_depth + 1:
                self.groups[-1] += opened_here
            else:
                self.groups.append(opened_here)

        return line_depth


def read_lines(filename: str) -> tuple[list[str], list[str], bool]:
    """Return the lines without their endings, each line's own ending, and whether the file had a BOM."""
    with open(filename, "rb") as file:
        has_bom = file.read(3) == b"\xef\xbb\xbf"

    with open(filename, "r", encoding="utf-8-sig", newline="") as file:
        raw_lines = file.readlines()

    lines = [raw_line.rstrip("\r\n") for raw_line in raw_lines]
    endings = [raw_line[len(line):] for raw_line, line in zip(raw_lines, lines)]
    return lines, endings, has_bom


def style_lines(filename: str, lines: list[str],
                allowed_lines: set[int] | None = None) -> tuple[list[str | None], dict[int, int]] | None:
    """Restyle every line, renaming only what stays consistent when just allowed_lines are kept. Returns the
    styled lines (None where a line is dropped because its leading "then" moved up) and, for each line that
    receives that "then", the number of the line it came from. Returns None when the file's blocks and
    brackets do not balance."""
    styled: list[str | None] = [None] * len(lines)
    receives_then: dict[int, int] = {}
    nesting = Nesting()
    pending_close = ""
    previous_visible = ""
    previous_ends_with_code = False
    previous_index = -1
    context = CodeContext(plan_renames(lines, allowed_lines))

    for index, line in enumerate(lines):
        line_num = index + 1
        started_inside = bool(pending_close)
        segments, pending_close = split_segments(line, pending_close)

        if started_inside:
            # Long-bracket content is data: keep the line as written, apart from renaming locals in any code
            # between the bracket that closes here and one that opens again, which also gets bracket bookkeeping.
            previous_index = index
            context.prev = ""
            code_text = ""
            rebuilt = []

            for kind, text in segments:
                if kind == "code":
                    text = convert_code_text(text, context)
                    code_text += text

                rebuilt.append(text)

            styled[index] = "".join(rebuilt)
            code_text = code_text.strip()
            nesting.feed(code_text)

            if not pending_close:
                previous_visible = "".join(text for kind, text in segments if kind in ("code", "string")).strip()
                previous_ends_with_code = bool(segments) and segments[-1][0] == "code" and bool(code_text)

            continue

        context.prev = ""
        converted_segments = []

        for kind, text in segments:
            if kind == "code":
                text = collapse_whitespace(convert_code_text(text, context))

            converted_segments.append((kind, text))

        assembled = "".join(text for _, text in converted_segments).lstrip()
        last_kind = converted_segments[-1][0] if converted_segments else "code"

        if last_kind in ("code", "comment"):
            assembled = assembled.rstrip()

        code_text = "".join(text for kind, text in converted_segments if kind == "code").strip()
        # Strings stay in the continuation check so an operator mid-line (e.g. x or "y") does not count.
        visible_text = "".join(text for kind, text in converted_segments if kind in ("code", "string")).strip()
        indent_offset = 0

        # Move a line-leading "then" onto the previous line, when the previous line ends in code.
        if re.match(r"then\b", assembled) and previous_ends_with_code and previous_index >= 0 and styled[previous_index].strip():
            assembled = assembled[len("then"):].lstrip()
            code_text = code_text[len("then"):].lstrip()
            visible_text = visible_text[len("then"):].lstrip()
            receives_then[previous_index] = line_num

            # The moved "then" opens its block on the previous line.
            nesting.open_group()

            if not assembled:
                previous_visible = ""
                previous_ends_with_code = False
                continue

        # Indent continuation lines of conditions/expressions split at a logical operator.
        if STARTS_WITH_LOGICAL.match(visible_text) or ENDS_WITH_LOGICAL.search(previous_visible):
            indent_offset = 1

        depth = nesting.feed(code_text)

        # Don't add indentation to empty lines, i.e. trailing whitespace.
        if not assembled:
            styled[index] = ""
        else:
            styled[index] = f"{INDENT * max(depth + indent_offset, 0)}{assembled}"

        previous_index = index
        previous_visible = visible_text
        previous_ends_with_code = last_kind == "code" and bool(assembled)

    # Usually a syntax error, such as a missing "end": every depth after it would be a guess.
    if nesting.unbalanced or nesting.groups:
        print(f"WARNING: {filename}: blocks or brackets do not balance, so no style changes are suggested for it", file=sys.stderr)
        return None

    return styled, receives_then


def process_file(filename: str, allowed_lines: set[int] | None = None) -> None:
    """Apply the style rules to a file in place, or only to allowed_lines when given."""
    lines, endings, has_bom = read_lines(filename)

    if not lines:
        return

    result = style_lines(filename, lines, allowed_lines)

    if result is None:
        return

    styled, receives_then = result
    output: list[tuple[int, str]] = []

    for index, original in enumerate(lines):
        restyle = allowed_lines is None or index + 1 in allowed_lines
        text = styled[index] if restyle else original

        if text is None:
            continue

        source_line = receives_then.get(index)

        if source_line is not None and (allowed_lines is None or source_line in allowed_lines):
            text = text.rstrip() + " then"

        output.append((index, text))

    if allowed_lines is None:
        newline = "\r\n" if {ending for ending in endings if ending} == {"\r\n"} else "\n"

        with open(filename, "w", encoding="utf-8", newline="") as file:
            file.write(newline.join(text for _, text in output) + newline)

        return

    if [text for _, text in output] == lines:
        return

    # Untouched lines keep their own endings and the BOM, so the diff shows only the restyled lines.
    with open(filename, "w", encoding="utf-8-sig" if has_bom else "utf-8", newline="") as file:
        file.write("".join(text + endings[index] for index, text in output))


def load_allowed_lines(path: str) -> dict[str, set[int]]:
    with open(path, "r", encoding="utf-8") as file:
        return {name: set(numbers) for name, numbers in json.load(file).items()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Restyle Lua files in place.")
    parser.add_argument("--lines-json", help="JSON object mapping each file to the line numbers to restyle; other lines are kept")
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()

    allowed = load_allowed_lines(args.lines_json) if args.lines_json else None

    for name in args.files:
        process_file(name, None if allowed is None else allowed.get(name, set()))
