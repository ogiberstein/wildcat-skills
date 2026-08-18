"""The language registry Horos's map verb dispatches through.

One folder per language. An extractor exposes outline(path, source, out)
and returns an exit code; the registry maps file suffixes onto it. A suffix
absent here is refused by map, never guessed at.
"""

from .go import go
from .python import python
from .typescript import typescript

EXTRACTORS = {
    ".go": go.outline,
    ".py": python.outline,
    ".ts": typescript.outline,
    ".tsx": typescript.outline,
}


def supported():
    return ", ".join(sorted(EXTRACTORS))
