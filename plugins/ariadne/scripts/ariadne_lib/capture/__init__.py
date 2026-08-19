"""Readers that turn something already on disk into a statement.

Two so far: a Foundry build, and a dataset release. A capture reads what a tool
already wrote down rather than re-running it, so what ends up in the statement is
what was actually produced.
"""

from . import dataset, foundry

__all__ = ["dataset", "foundry"]
