"""Standard-library implementation package for Alexandria."""

__version__ = "0.1.0"

from .errors import AlexandriaError
from .derivation import derive
from .index import rebuild
from .query import query, query_bytes
from .release import ingest, verify

__all__ = [
    "AlexandriaError", "derive", "ingest", "query", "query_bytes", "rebuild", "verify"
]
