"""The language registry Horos's map verb dispatches through.

One folder per language. An extractor exposes outline(path, source, out)
and returns an exit code; the registry maps file suffixes onto it. A suffix
absent here is refused by map, never guessed at.
"""

from .cpp import cpp
from .go import go
from .python import python
from .typescript import typescript

EXTRACTORS = {
    ".cc": cpp.outline,
    ".cpp": cpp.outline,
    ".cxx": cpp.outline,
    ".go": go.outline,
    ".h": cpp.outline,
    ".hh": cpp.outline,
    ".hpp": cpp.outline,
    ".py": python.outline,
    ".ts": typescript.outline,
    ".tsx": typescript.outline,
}


def supported():
    return ", ".join(sorted(EXTRACTORS))
