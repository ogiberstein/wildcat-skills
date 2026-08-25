"""Classify TypeScript source without importing or executing it.

Absorbed from Horos's ``languages.typescript.typescript`` lexer at Wildcat
Skills commit b95f332379a9ed9fdacbbbd26fc194eb93ad757a.  The copy preserves the
``lex(source)`` span and error contract while keeping Hexaemeron independently
installable.  Horos remains the provenance source; changes here should be
reconciled against its tested lexer rather than redesigned in place.
Hexaemeron's ``comment_spans(source, tsx=...)`` wrapper keeps that API fixed
while opening template expressions and traversing JSX for comment consumers.
Its forward traversal accepts 64 recursively entered code, template, or JSX
regions and returns a named error at the 65th rather than depending on the
interpreter recursion limit. Iterative angle-group depth does not spend that
recursion budget.
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
ECMASCRIPT_LINE_TERMINATORS = frozenset("\r\n\u2028\u2029")
CONTROL_HEAD_KEYWORDS = frozenset({"catch", "for", "if", "switch", "while", "with"})
COMMENT_REGEX_ALLOWED_AFTER = REGEX_ALLOWED_AFTER | {"control)", "default"}
EXPRESSION_BRACE_AFTER = frozenset(
    {
        "(",
        "[",
        ",",
        ":",
        "=",
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
        "yield",
        "await",
        "throw",
        "default",
        "as",
        "satisfies",
    }
)
TYPE_LITERAL_BRACE_AFTER = frozenset(
    {"(", "[", ",", ":", "=", "=>", "&", "|", "?", "<", "extends"}
)


def _line_comment_end(source, start):
    """Return the first ECMAScript line terminator or the source end."""
    cursor = start
    while cursor < len(source) and source[cursor] not in ECMASCRIPT_LINE_TERMINATORS:
        cursor += 1
    return cursor


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


class _CommentScanError(ValueError):
    def __init__(self, offset, reason):
        super().__init__(reason)
        self.offset = offset
        self.reason = reason


def _scan_comment_safe_regex(source, start):
    """Scan one regex token without consuming its following slash token.

    The regex-closing slash can be immediately followed by division or by the
    first slash of a comment. Return just past the regex and let the forward
    scanner classify that next token from its own offset.
    """
    n = len(source)
    i = start + 1
    in_class = False
    while i < n:
        c = source[i]
        if c == "\\":
            if (
                i + 1 >= n
                or source[i + 1] in ECMASCRIPT_LINE_TERMINATORS
            ):
                return None
            i += 2
            continue
        if c in ECMASCRIPT_LINE_TERMINATORS:
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


JSX_NAME = re.compile(r"(?:[^\W\d]|[$])[\w.$:-]*")
TYPESCRIPT_IDENTIFIER = re.compile(r"(?:[^\W\d]|[$])[\w$]*")
MAX_COMMENT_NESTING = 64


class _CommentScanner:
    """Classify comments in one bounded forward traversal.

    Nested code, templates, and JSX return the offset after their closing
    delimiter, so their caller never rescans the consumed suffix. ``lex()``
    remains the stable complete-span API for its existing consumers.
    """

    def __init__(self, source, *, tsx):
        self.source = source
        self.tsx = tsx
        self.comments = []
        self.depth = 0
        self.furthest = 0

    def _error(self, offset, reason):
        return _CommentScanError(offset, reason)

    def _descend(self, offset, callback, *args, **kwargs):
        if self.depth >= MAX_COMMENT_NESTING:
            raise self._error(offset, "nesting exceeds supported depth")
        self.depth += 1
        try:
            return callback(*args, **kwargs)
        finally:
            self.depth -= 1

    def _mark(self, offset):
        self.furthest = max(self.furthest, offset)

    def _string_end(self, start):
        quote = self.source[start]
        cursor = start + 1
        while cursor < len(self.source):
            char = self.source[cursor]
            if char == "\\":
                cursor += 1
                if cursor >= len(self.source):
                    break
                if (
                    self.source[cursor] == "\r"
                    and cursor + 1 < len(self.source)
                    and self.source[cursor + 1] == "\n"
                ):
                    cursor += 1
                cursor += 1
                continue
            if char == quote:
                return cursor + 1
            if char in ECMASCRIPT_LINE_TERMINATORS:
                break
            cursor += 1
        raise self._error(start, "unterminated string")

    def _trivia_end(self, start, limit):
        """Skip whitespace and comments without consuming beyond ``limit``."""
        cursor = start
        while cursor < limit:
            if self.source[cursor].isspace():
                cursor += 1
                continue
            if self.source.startswith("//", cursor):
                cursor = min(_line_comment_end(self.source, cursor + 2), limit)
                continue
            if self.source.startswith("/*", cursor):
                end = self.source.find("*/", cursor + 2, limit)
                if end == -1:
                    return limit
                cursor = end + 2
                continue
            break
        return cursor

    def _template_end(self, start, record):
        cursor = start + 1
        while cursor < len(self.source):
            self._mark(cursor)
            if self.source[cursor] == "\\":
                cursor += 2
                continue
            if self.source[cursor] == "`":
                return cursor + 1
            if self.source.startswith("${", cursor):
                cursor = self._descend(
                    cursor,
                    self._code_end,
                    cursor + 2,
                    stop_on_brace=True,
                    record=record,
                    missing="unterminated template expression",
                    initial_previous="=",
                )
                continue
            cursor += 1
        raise self._error(start, "unterminated template literal")

    def _angle_end(self, start, record):
        """Scan one TypeScript angle group used by JSX type arguments."""
        depth = 1
        cursor = start + 1
        while cursor < len(self.source):
            self._mark(cursor)
            if self.source.startswith("//", cursor):
                end = _line_comment_end(self.source, cursor + 2)
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
                continue
            if char == "`":
                cursor = self._descend(
                    cursor,
                    self._template_end,
                    cursor,
                    record,
                )
                continue
            if char == "{":
                cursor = self._descend(
                    cursor,
                    self._code_end,
                    cursor + 1,
                    stop_on_brace=True,
                    record=record,
                    missing="unterminated type argument expression",
                    initial_previous="=",
                )
                continue
            if char == "<":
                depth += 1
            elif char == ">" and self.source[cursor - 1] != "=":
                depth -= 1
                if depth == 0:
                    return cursor + 1
            cursor += 1
        raise self._error(start, "unterminated type argument list")

    def _attribute_string_end(self, start):
        quote = self.source[start]
        cursor = start + 1
        while cursor < len(self.source):
            if self.source[cursor] == quote:
                return cursor + 1
            cursor += 1
        raise self._error(start, "unterminated JSX attribute string")

    def _jsx_prefix(self, start):
        cursor = start + 1
        if cursor < len(self.source) and self.source[cursor] == ">":
            return True
        match = JSX_NAME.match(self.source, cursor)
        if match is None:
            return False
        cursor = match.end()
        return cursor == len(self.source) or (
            self.source[cursor].isspace() or self.source[cursor] in "/> <"
        )

    def _generic_arrow_start(self, start):
        """Recognize the TSX forms that disambiguate a generic arrow."""
        try:
            end = self._angle_end(start, record=False)
        except _CommentScanError:
            return False
        after = self._trivia_end(end, len(self.source))
        if after >= len(self.source) or self.source[after] != "(":
            return False

        limit = end - 1
        cursor = self._trivia_end(start + 1, limit)
        match = TYPESCRIPT_IDENTIFIER.match(self.source, cursor, limit)
        if match is None:
            return False
        token = match.group(0)
        cursor = match.end()
        while token == "const":
            cursor = self._trivia_end(cursor, limit)
            match = TYPESCRIPT_IDENTIFIER.match(self.source, cursor, limit)
            if match is None:
                return False
            token = match.group(0)
            cursor = match.end()
        cursor = self._trivia_end(cursor, limit)
        if cursor >= limit:
            return False
        if self.source[cursor] == ",":
            return True
        if self.source[cursor] == "=" and not self.source.startswith("=>", cursor):
            return True
        keyword_end = cursor + len("extends")
        return (
            self.source.startswith("extends", cursor)
            and keyword_end <= limit
            and (
                keyword_end == limit
                or self.source[keyword_end] not in WORD_CHARS
            )
        )

    def _jsx_open(self, start, record):
        cursor = start + 1
        if cursor < len(self.source) and self.source[cursor] == ">":
            return cursor + 1, "", False
        match = JSX_NAME.match(self.source, cursor)
        if match is None:
            raise self._error(start, "invalid JSX opening tag")
        name = match.group(0)
        cursor = match.end()
        if cursor < len(self.source) and self.source[cursor] == "<":
            cursor = self._descend(
                cursor,
                self._angle_end,
                cursor,
                record,
            )
        if cursor < len(self.source) and not (
            self.source[cursor].isspace() or self.source[cursor] in "/>"
        ):
            raise self._error(start, "invalid JSX tag name")
        while cursor < len(self.source):
            self._mark(cursor)
            if self.source.startswith("//", cursor):
                end = _line_comment_end(self.source, cursor + 2)
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
            if self.source[cursor] in "'\"":
                cursor = self._attribute_string_end(cursor)
                continue
            if self.source[cursor] == "{":
                cursor = self._descend(
                    cursor,
                    self._code_end,
                    cursor + 1,
                    stop_on_brace=True,
                    record=record,
                    missing="unterminated JSX attribute expression",
                    initial_previous="=",
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
        cursor = start + 2
        if not self.source.startswith(name, cursor):
            return None
        cursor += len(name)
        while cursor < len(self.source) and self.source[cursor].isspace():
            cursor += 1
        return cursor + 1 if self.source.startswith(">", cursor) else None

    def _jsx_end(self, start, record):
        cursor, name, self_closing = self._jsx_open(start, record)
        if self_closing:
            return cursor
        while cursor < len(self.source):
            self._mark(cursor)
            if self.source.startswith("</", cursor):
                close_end = self._jsx_close_end(cursor, name)
                if close_end is not None:
                    return close_end
                raise self._error(cursor, "mismatched JSX closing tag")
            if self.source[cursor] == "<" and self._jsx_prefix(cursor):
                cursor = self._descend(
                    cursor,
                    self._jsx_end,
                    cursor,
                    record,
                )
                continue
            if self.source[cursor] == "{":
                cursor = self._descend(
                    cursor,
                    self._code_end,
                    cursor + 1,
                    stop_on_brace=True,
                    record=record,
                    missing="unterminated JSX child expression",
                    initial_previous="=",
                )
                continue
            cursor += 1
        raise self._error(start, "unterminated JSX element")

    def _code_end(
        self,
        start,
        *,
        stop_on_brace,
        record,
        missing,
        initial_previous="",
        object_context=False,
    ):
        cursor = start
        previous = initial_previous
        before_previous = ""
        paren_contexts = []
        pending_ternaries = 0
        colon_starts_expression = False
        pending_expression_body = None
        pending_body_angle_depth = 0
        pending_function_return_type = False
        type_alias_state = 0
        line_break_since_token = False
        while cursor < len(self.source):
            self._mark(cursor)
            if stop_on_brace and self.source[cursor] == "}":
                return cursor + 1
            if self.source.startswith("//", cursor):
                end = _line_comment_end(self.source, cursor + 2)
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
                if any(
                    char in ECMASCRIPT_LINE_TERMINATORS
                    for char in self.source[cursor : end + 2]
                ):
                    line_break_since_token = True
                cursor = end + 2
                continue
            char = self.source[cursor]
            if pending_expression_body is not None:
                if char == "<" and (
                    pending_body_angle_depth
                    or previous == pending_expression_body
                    or before_previous
                    in {pending_expression_body, ":", "extends", "implements"}
                    or (
                        pending_expression_body == "function"
                        and pending_function_return_type
                    )
                ):
                    pending_body_angle_depth += 1
                elif (
                    char == ">"
                    and pending_body_angle_depth
                    and self.source[cursor - 1] != "="
                ):
                    pending_body_angle_depth -= 1
            if char in "'\"":
                cursor = self._string_end(cursor)
                before_previous = previous
                previous = "string"
                colon_starts_expression = False
                line_break_since_token = False
                continue
            if char == "`":
                cursor = self._descend(
                    cursor,
                    self._template_end,
                    cursor,
                    record,
                )
                before_previous = previous
                previous = "template"
                colon_starts_expression = False
                line_break_since_token = False
                continue
            if (
                self.tsx
                and char == "<"
                and previous in COMMENT_REGEX_ALLOWED_AFTER
                and self._jsx_prefix(cursor)
                and not self._generic_arrow_start(cursor)
            ):
                cursor = self._descend(
                    cursor,
                    self._jsx_end,
                    cursor,
                    record,
                )
                before_previous = previous
                previous = "jsx"
                colon_starts_expression = False
                line_break_since_token = False
                continue
            if char == "{":
                function_type_literal = (
                    pending_expression_body == "function"
                    and pending_function_return_type
                    and previous in TYPE_LITERAL_BRACE_AFTER
                )
                construct_body = (
                    pending_expression_body is not None
                    and not paren_contexts
                    and pending_body_angle_depth == 0
                    and not function_type_literal
                )
                closes_expression = construct_body or (
                    previous in EXPRESSION_BRACE_AFTER
                    and (
                        previous != ":"
                        or object_context
                        or colon_starts_expression
                    )
                )
                if construct_body:
                    pending_expression_body = None
                    pending_function_return_type = False
                if type_alias_state == 1:
                    type_alias_state = 0
                cursor = self._descend(
                    cursor,
                    self._code_end,
                    cursor + 1,
                    stop_on_brace=True,
                    record=record,
                    missing="unterminated brace expression",
                    object_context=(
                        closes_expression
                        and not construct_body
                        and previous != "=>"
                    ),
                )
                before_previous = previous
                previous = "expression" if closes_expression else "}"
                colon_starts_expression = False
                line_break_since_token = False
                continue
            regex_goal = previous in COMMENT_REGEX_ALLOWED_AFTER or (
                type_alias_state == 3 and line_break_since_token
            )
            if char == "/" and regex_goal:
                regex_end = _scan_comment_safe_regex(self.source, cursor)
                if regex_end is not None:
                    cursor = regex_end
                    before_previous = previous
                    previous = "regex"
                    colon_starts_expression = False
                    type_alias_state = 0
                    line_break_since_token = False
                    continue
            if char in WORD_CHARS:
                end = cursor + 1
                while end < len(self.source) and self.source[end] in WORD_CHARS:
                    end += 1
                token = self.source[cursor:end]
                type_alias_start = token == "type" and not object_context and (
                    previous in {"", ";", "}", "export", "declare"}
                    or (
                        line_break_since_token
                        and (
                            previous
                            in {
                                ")",
                                "]",
                                "expression",
                                "jsx",
                                "postfix",
                                "regex",
                                "return",
                                "string",
                                "template",
                            }
                            or (
                                previous
                                and all(char in WORD_CHARS for char in previous)
                                and previous
                                not in {
                                    "as",
                                    "extends",
                                    "implements",
                                    "infer",
                                    "keyof",
                                    "readonly",
                                    "satisfies",
                                    "typeof",
                                }
                            )
                        )
                    )
                )
                if type_alias_state == 1:
                    type_alias_state = 2
                elif type_alias_start:
                    type_alias_state = 1
                if token in {"class", "function"} and (
                    (
                        previous in EXPRESSION_BRACE_AFTER
                        and previous != "default"
                    )
                    or (
                        previous == "async"
                        and before_previous in EXPRESSION_BRACE_AFTER
                        and before_previous != "default"
                    )
                ):
                    pending_expression_body = token
                before_previous = previous
                previous = token
                colon_starts_expression = False
                line_break_since_token = False
                cursor = end
                continue
            if char.isspace():
                if char in ECMASCRIPT_LINE_TERMINATORS:
                    line_break_since_token = True
            else:
                if char == ";":
                    type_alias_state = 0
                elif char == "=" and not self.source.startswith(
                    ("=>", "=="), cursor
                ):
                    type_alias_state = 3 if type_alias_state == 2 else 0
                elif type_alias_state == 1:
                    type_alias_state = 0
                if self.source.startswith(("++", "--"), cursor):
                    before_previous = previous
                    previous = "postfix"
                    colon_starts_expression = False
                    line_break_since_token = False
                    cursor += 2
                    continue
                if (
                    char == "!"
                    and not self.source.startswith("!=", cursor)
                    and previous
                    and previous not in COMMENT_REGEX_ALLOWED_AFTER
                ):
                    before_previous = previous
                    previous = "postfix"
                    colon_starts_expression = False
                    line_break_since_token = False
                    cursor += 1
                    continue
                if char == "(":
                    paren_contexts.append(
                        (
                            previous in CONTROL_HEAD_KEYWORDS
                            and before_previous != "."
                        )
                        or (previous == "await" and before_previous == "for")
                    )
                    before_previous = previous
                    previous = "("
                    colon_starts_expression = False
                    line_break_since_token = False
                    cursor += 1
                    continue
                if char == ")":
                    control_head = paren_contexts.pop() if paren_contexts else False
                    before_previous = previous
                    previous = "control)" if control_head else ")"
                    colon_starts_expression = False
                    line_break_since_token = False
                    cursor += 1
                    continue
                if char == "?" and not self.source.startswith(("??", "?."), cursor):
                    pending_ternaries += 1
                if char == ":":
                    if (
                        pending_expression_body == "function"
                        and previous == ")"
                        and not paren_contexts
                        and pending_body_angle_depth == 0
                    ):
                        pending_function_return_type = True
                    colon_starts_expression = pending_ternaries > 0
                    if pending_ternaries:
                        pending_ternaries -= 1
                elif char != "?":
                    colon_starts_expression = False
                if (
                    previous
                    and previous[-1] == char
                    and previous + char in REGEX_ALLOWED_AFTER
                ):
                    before_previous = previous
                    previous += char
                elif char == ">" and previous == "=":
                    before_previous = previous
                    previous = "=>"
                else:
                    before_previous = previous
                    previous = char
                line_break_since_token = False
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

    The comment consumer shares one bounded forward scanner across TypeScript
    and TSX. TSX additionally traverses JSX so child text and tag syntax cannot
    masquerade as comments or regular expressions. The complete-span ``lex``
    contract remains unchanged for existing callers.
    """
    scanner = _CommentScanner(source, tsx=tsx)
    try:
        return scanner.scan(), []
    except _CommentScanError as exc:
        return scanner.comments, [(exc.offset, exc.reason)]
    except RecursionError:
        offset = min(scanner.furthest, max(len(source) - 1, 0))
        return scanner.comments, [(offset, "nesting exceeds supported depth")]
