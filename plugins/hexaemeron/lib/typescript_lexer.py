"""Classify TypeScript source without importing or executing it.

Absorbed from Horos's ``languages.typescript.typescript`` lexer at Wildcat
Skills commit b95f332379a9ed9fdacbbbd26fc194eb93ad757a.  The copy preserves the
``lex(source)`` span and error contract while keeping Hexaemeron independently
installable.  Horos remains the provenance source; changes here should be
reconciled against its tested lexer rather than redesigned in place.
Hexaemeron's ``comment_spans(source, tsx=...)`` wrapper keeps that API fixed
while opening template expressions and traversing JSX for comment consumers.
"""

import re

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

    Returns ``(spans, errors)``. Each span is ``(kind, start, end)`` with kind
    one of code, line_comment, block_comment, string, template, regex; spans
    cover the source in order. Each error is ``(offset, reason)`` for a
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
            # Horos's original scanner treats a raw newline as proof that a
            # JavaScript string is unterminated. TSX quoted attribute values
            # are the one source form that permits that newline, so retain the
            # normal rule and widen only after the attribute boundary is
            # established from the surrounding tag.
            if end is None and _is_jsx_attribute_string(source, i):
                end = _scan_jsx_attribute_string(source, i)
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
    """From the opening quote past the closing one; None if it never closes."""
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


def _is_jsx_attribute_string(source, start):
    """Whether a quote follows an attribute assignment inside an open tag."""
    cursor = start - 1
    while cursor >= 0 and source[cursor].isspace():
        cursor -= 1
    if cursor < 0 or source[cursor] != "=":
        return False
    cursor -= 1
    while cursor >= 0 and (source[cursor].isalnum() or source[cursor] in "_:$-"):
        cursor -= 1
    if cursor >= 0 and not source[cursor].isspace():
        return False

    opening = source.rfind("<", 0, start)
    closing = source.rfind(">", 0, start)
    if opening <= closing:
        return False
    tag = opening + 1
    if tag < len(source) and source[tag] == "/":
        tag += 1
    while tag < len(source) and source[tag].isspace():
        tag += 1
    return tag < len(source) and (source[tag].isalpha() or source[tag] in "_$")


def _scan_jsx_attribute_string(source, start):
    """Scan a TSX quoted attribute, whose value may contain raw newlines."""
    quote = source[start]
    i = start + 1
    while i < len(source):
        if source[i] == quote:
            return i + 1
        i += 1
    return None


def _scan_template(source, start):
    """Scan a template and its nested substitutions through the closing tick."""
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
    """From just after ``${`` past the balancing brace; None if unbalanced."""
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


def _comment_contents(spans):
    """Return only comment spans, with their delimiters still attached."""
    return [
        (kind, start, end)
        for kind, start, end in spans
        if kind in ("line_comment", "block_comment")
    ]


class _CommentScanError(ValueError):
    def __init__(self, offset, reason):
        super().__init__(reason)
        self.offset = offset
        self.reason = reason


def _template_expression_comments(source, start, limit):
    """Find one `${...}` close and its nested comments."""
    spans, _ = lex(source[start:limit])
    depth = 1
    comments = []
    for kind, relative_start, relative_end in spans:
        span_start = start + relative_start
        span_end = start + relative_end
        if kind in ("line_comment", "block_comment"):
            comments.append((kind, span_start, span_end))
            continue
        if kind == "template":
            comments.extend(_template_comments(source, span_start, span_end))
            continue
        if kind != "code":
            continue
        for offset in range(span_start, span_end):
            if source[offset] == "{":
                depth += 1
            elif source[offset] == "}":
                depth -= 1
                if depth == 0:
                    return offset + 1, comments
    return None, comments


def _template_comments(source, start, end):
    """Return comments inside a template's substitution expressions."""
    comments = []
    cursor = start + 1
    while cursor < end - 1:
        if source[cursor] == "\\":
            cursor += 2
            continue
        if source.startswith("${", cursor):
            expression_end, nested = _template_expression_comments(
                source, cursor + 2, end - 1
            )
            if expression_end is None:
                raise _CommentScanError(cursor, "unterminated template expression")
            comments.extend(nested)
            cursor = expression_end
            continue
        cursor += 1
    return comments


JSX_NAME = re.compile(r"[A-Za-z_$][\w.$:-]*")


class _TsxCommentScanner:
    """Classify comments while treating JSX markup and child text as data."""

    def __init__(self, source):
        self.source = source
        self.comments = []

    def _error(self, offset, reason):
        return _CommentScanError(offset, reason)

    def _string_end(self, start):
        end = _scan_string(self.source, start)
        if end is None:
            raise self._error(start, "unterminated string")
        return end

    def _template_end(self, start, record):
        cursor = start + 1
        while cursor < len(self.source):
            if self.source[cursor] == "\\":
                cursor += 2
                continue
            if self.source[cursor] == "`":
                return cursor + 1
            if self.source.startswith("${", cursor):
                cursor = self._code_end(
                    cursor + 2,
                    stop_on_brace=True,
                    record=record,
                    missing="unterminated template expression",
                )
                continue
            cursor += 1
        raise self._error(start, "unterminated template literal")

    def _attribute_string_end(self, start):
        quote = self.source[start]
        cursor = start + 1
        while cursor < len(self.source):
            if self.source[cursor] == quote:
                return cursor + 1
            cursor += 1
        raise self._error(start, "unterminated JSX attribute string")

    def _jsx_open(self, start, record):
        cursor = start + 1
        if cursor < len(self.source) and self.source[cursor] == ">":
            return cursor + 1, "", False
        match = JSX_NAME.match(self.source, cursor)
        if match is None:
            raise self._error(start, "invalid JSX opening tag")
        name = match.group(0)
        cursor = match.end()
        if cursor < len(self.source) and not (
            self.source[cursor].isspace() or self.source[cursor] in "/>"
        ):
            raise self._error(start, "invalid JSX tag name")
        while cursor < len(self.source):
            if self.source[cursor] in "'\"":
                cursor = self._attribute_string_end(cursor)
                continue
            if self.source[cursor] == "{":
                cursor = self._code_end(
                    cursor + 1,
                    stop_on_brace=True,
                    record=record,
                    missing="unterminated JSX attribute expression",
                )
                continue
            if self.source.startswith("/>", cursor):
                return cursor + 2, name, True
            if self.source[cursor] == ">":
                return cursor + 1, name, False
            cursor += 1
        raise self._error(start, "unterminated JSX opening tag")

    def _jsx_close_end(self, start, name):
        if name == "":
            return start + 3 if self.source.startswith("</>", start) else None
        match = re.match(
            r"</" + re.escape(name) + r"\s*>", self.source[start:]
        )
        return start + match.end() if match is not None else None

    def _jsx_candidate(self, start):
        try:
            end, name, self_closing = self._jsx_open(start, record=False)
        except _CommentScanError:
            return False
        if self_closing:
            return True
        if name == "":
            return "</>" in self.source[end:]
        return re.search(
            r"</" + re.escape(name) + r"\s*>", self.source[end:]
        ) is not None

    def _jsx_end(self, start, record):
        cursor, name, self_closing = self._jsx_open(start, record)
        if self_closing:
            return cursor
        while cursor < len(self.source):
            close_end = self._jsx_close_end(cursor, name)
            if close_end is not None:
                return close_end
            if self.source[cursor] == "<" and self._jsx_candidate(cursor):
                cursor = self._jsx_end(cursor, record)
                continue
            if self.source[cursor] == "{":
                cursor = self._code_end(
                    cursor + 1,
                    stop_on_brace=True,
                    record=record,
                    missing="unterminated JSX child expression",
                )
                continue
            cursor += 1
        raise self._error(start, "unterminated JSX element")

    def _code_end(self, start, *, stop_on_brace, record, missing):
        cursor = start
        previous = ""
        while cursor < len(self.source):
            if stop_on_brace and self.source[cursor] == "}":
                return cursor + 1
            if self.source.startswith("//", cursor):
                end = self.source.find("\n", cursor + 2)
                end = len(self.source) if end == -1 else end
                if record:
                    self.comments.append(("line_comment", cursor, end))
                cursor = end
                continue
            if self.source.startswith("/*", cursor):
                end = self.source.find("*/", cursor + 2)
                if end == -1:
                    raise self._error(cursor, "unterminated block comment")
                if record:
                    self.comments.append(("block_comment", cursor, end + 2))
                cursor = end + 2
                continue
            char = self.source[cursor]
            if char in "'\"":
                cursor = self._string_end(cursor)
                previous = "string"
                continue
            if char == "`":
                cursor = self._template_end(cursor, record)
                previous = "template"
                continue
            if (
                char == "<"
                and previous in REGEX_ALLOWED_AFTER
                and self._jsx_candidate(cursor)
            ):
                cursor = self._jsx_end(cursor, record)
                previous = "jsx"
                continue
            if char == "{":
                cursor = self._code_end(
                    cursor + 1,
                    stop_on_brace=True,
                    record=record,
                    missing="unterminated brace expression",
                )
                previous = "}"
                continue
            if char == "/" and previous in REGEX_ALLOWED_AFTER:
                regex_end = _scan_regex(self.source, cursor)
                if regex_end is not None:
                    cursor = regex_end
                    previous = "regex"
                    continue
            if char in WORD_CHARS:
                end = cursor + 1
                while end < len(self.source) and self.source[end] in WORD_CHARS:
                    end += 1
                previous = self.source[cursor:end]
                cursor = end
                continue
            if not char.isspace():
                if (
                    previous
                    and previous[-1] == char
                    and previous + char in REGEX_ALLOWED_AFTER
                ):
                    previous += char
                elif char == ">" and previous == "=":
                    previous = "=>"
                else:
                    previous = char
            cursor += 1
        if stop_on_brace:
            raise self._error(start, missing)
        return cursor

    def scan(self):
        self._code_end(
            0,
            stop_on_brace=False,
            record=True,
            missing="",
        )
        return self.comments


def comment_spans(source, *, tsx=False):
    """Return genuine comment spans plus named lexical errors.

    Plain TypeScript keeps ``lex`` as its outer classifier and opens template
    substitutions only to recover comments. TSX adds a bounded JSX traversal
    so child text and tag syntax cannot masquerade as comments or regexes.
    """
    if tsx:
        scanner = _TsxCommentScanner(source)
        try:
            return scanner.scan(), []
        except _CommentScanError as exc:
            return scanner.comments, [(exc.offset, exc.reason)]

    spans, errors = lex(source)
    comments = _comment_contents(spans)
    if errors:
        return comments, errors
    try:
        for kind, start, end in spans:
            if kind == "template":
                comments.extend(_template_comments(source, start, end))
    except _CommentScanError as exc:
        return comments, [(exc.offset, exc.reason)]
    comments.sort(key=lambda span: (span[1], span[2]))
    return comments, []
