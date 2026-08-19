"""Whether a string a person will read actually shows them something.

A name, a path segment or a label that renders as nothing satisfies every length
and presence check ever written and identifies nothing to the reader it was put
there for. Two shapes do it:

- Whitespace. `"   "` is a legal POSIX filename and an unreadable one.
- Format and control characters. `str.strip` does not treat U+200B as
  whitespace, so `"a"` and `"a​"` are two different strings that look
  identical in any listing, in any terminal, in any review.

The second is the one worth a module. It has been recorded as a lead twice
across this marketplace and closed nowhere until it turned up in a document
format being written rather than in one being read.

This is deliberately narrow. It answers whether anything is visible, not whether
the text is sensible, and it is applied to identifiers rather than to prose. A
reason field explaining why a capture was skipped may contain whatever a person
needs to write; a path segment may not be invisible.
"""

from __future__ import annotations

import unicodedata

INVISIBLE_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Co", "Cn", "Zl", "Zp"})
"""Unicode general categories that show a reader nothing.

Control, format, surrogate, private use, unassigned, and the line and paragraph
separators. `Zs` is not here: an ordinary space between two visible characters is
legitimate, and `str.isspace` already covers a string made only of those.
"""


def visible(value: object) -> bool:
    """True when the string contains at least one character a reader can see.

    Not a validator. Callers decide what to do about an invisible identifier;
    this decides only whether it is one.
    """
    if not isinstance(value, str) or not value:
        return False
    for character in value:
        if character.isspace():
            continue
        if unicodedata.category(character) in INVISIBLE_CATEGORIES:
            continue
        return True
    return False
