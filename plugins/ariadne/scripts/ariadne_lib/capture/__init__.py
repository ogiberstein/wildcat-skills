"""Readers that turn a build on disk into a statement.

One so far: Foundry. A capture reads what a tool already wrote down rather than
re-running it, so what ends up in the statement is what the compiler emitted.
"""

from . import foundry

__all__ = ["foundry"]
