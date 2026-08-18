"""TypeScript outline extraction for Horos's map verb.

This module lexes rather than parses. The lexer classifies every character
of the source into code, comments, strings, template literals and regex
literals; the outliner (a later step) works only over the code spans. It
never imports or executes what it reads.
"""

# Tokens after which a slash starts a regex literal rather than division.
# After an identifier, a number, or a closing ) ] } the slash divides.
REGEX_ALLOWED_AFTER = frozenset(
    {
        "",
        "(",
        "[",
        "{",
        "}",
        ",",
        ";",
        ":",
        "=",
        "=>",
        "==",
        "===",
        "!",
        "!=",
        "!==",
        "&",
        "&&",
        "|",
        "||",
        "?",
        "??",
        "+",
        "-",
        "*",
        "/",
        "%",
        "<",
        ">",
        "<=",
        ">=",
        "~",
        "^",
        "return",
        "case",
        "typeof",
        "instanceof",
        "in",
        "of",
        "new",
        "delete",
        "void",
        "do",
        "else",
        "yield",
        "await",
        "throw",
    }
)

WORD_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_$"
)


def lex(source):
    """Classify the whole source into spans; fail-open on what it cannot end.

    Returns (spans, errors). Each span is (kind, start, end) with kind one
    of code, line_comment, block_comment, string, template, regex; spans
    cover the source in order. Each error is (offset, reason) for a
    construct that never terminated; the span still covers the remainder so
    the caller can confess it.
    """
    spans = []
    errors = []
    n = len(source)
    i = 0
    code_start = 0
    prev = ""  # last significant code token, for the regex decision

    def flush_code(end):
        if end > code_start:
            spans.append(("code", code_start, end))

    while i < n:
        c = source[i]

        if c == "/" and i + 1 < n and source[i + 1] == "/":
            flush_code(i)
            end = source.find("\n", i)
            end = n if end == -1 else end
            spans.append(("line_comment", i, end))
            i = end
            code_start = i
            continue

        if c == "/" and i + 1 < n and source[i + 1] == "*":
            flush_code(i)
            end = source.find("*/", i + 2)
            if end == -1:
                errors.append((i, "unterminated block comment"))
                spans.append(("block_comment", i, n))
                return spans, errors
            spans.append(("block_comment", i, end + 2))
            i = end + 2
            code_start = i
            continue

        if c in "'\"":
            flush_code(i)
            end = _scan_string(source, i)
            if end is None:
                errors.append((i, "unterminated string"))
                spans.append(("string", i, n))
                return spans, errors
            spans.append(("string", i, end))
            i = end
            code_start = i
            prev = "string"
            continue

        if c == "`":
            flush_code(i)
            end = _scan_template(source, i)
            if end is None:
                errors.append((i, "unterminated template literal"))
                spans.append(("template", i, n))
                return spans, errors
            spans.append(("template", i, end))
            i = end
            code_start = i
            prev = "template"
            continue

        if c == "/" and prev in REGEX_ALLOWED_AFTER:
            end = _scan_regex(source, i)
            if end is not None:
                flush_code(i)
                spans.append(("regex", i, end))
                i = end
                code_start = i
                prev = "regex"
                continue
            # A regex cannot hold an unescaped newline; the scan failing
            # means this slash divides after all, so fall through as code.

        if c in WORD_CHARS:
            j = i
            while j < n and source[j] in WORD_CHARS:
                j += 1
            prev = source[i:j]
            i = j
            continue

        if not c.isspace():
            # Fold repeated operator characters so `=>` and `===` count as
            # one significant token for the regex decision.
            if prev and prev[-1] == c and (prev + c) in REGEX_ALLOWED_AFTER:
                prev += c
            elif c == ">" and prev == "=":
                prev = "=>"
            else:
                prev = c
        i += 1

    flush_code(n)
    return spans, errors


def _scan_string(source, start):
    """From the opening quote past the closing one; None if it never closes.

    An escape consumes the next character, which legally includes a newline
    (line continuation); a raw newline ends the literal unterminated.
    """
    quote = source[start]
    n = len(source)
    i = start + 1
    while i < n:
        c = source[i]
        if c == "\\":
            i += 2
            continue
        if c == quote:
            return i + 1
        if c == "\n":
            return None
        i += 1
    return None


def _scan_template(source, start):
    """From the opening backtick past its match, through nested ${...}
    expressions that may themselves hold strings, templates and comments.
    None if it never closes."""
    n = len(source)
    i = start + 1
    while i < n:
        c = source[i]
        if c == "\\":
            i += 2
            continue
        if c == "`":
            return i + 1
        if c == "$" and i + 1 < n and source[i + 1] == "{":
            i = _scan_template_expression(source, i + 2)
            if i is None:
                return None
            continue
        i += 1
    return None


def _scan_template_expression(source, start):
    """From just after `${` past the balancing `}`; None if unbalanced."""
    n = len(source)
    depth = 1
    i = start
    while i < n:
        c = source[i]
        if c in "'\"":
            i = _scan_string(source, i)
            if i is None:
                return None
            continue
        if c == "`":
            i = _scan_template(source, i)
            if i is None:
                return None
            continue
        if c == "/" and i + 1 < n and source[i + 1] == "/":
            end = source.find("\n", i)
            if end == -1:
                return None
            i = end
            continue
        if c == "/" and i + 1 < n and source[i + 1] == "*":
            end = source.find("*/", i + 2)
            if end == -1:
                return None
            i = end + 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return None


def _scan_regex(source, start):
    """From the opening slash past the closing one and its flags; None when
    a newline arrives first, which proves this slash was division."""
    n = len(source)
    i = start + 1
    in_class = False
    while i < n:
        c = source[i]
        if c == "\\":
            i += 2
            continue
        if c == "\n":
            return None
        if c == "[":
            in_class = True
        elif c == "]":
            in_class = False
        elif c == "/" and not in_class:
            i += 1
            while i < n and source[i] in "dgimsuvy":
                i += 1
            return i
        i += 1
    return None
