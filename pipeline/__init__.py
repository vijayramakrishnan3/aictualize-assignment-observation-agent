"""Deterministic pipeline for the observation agent.

Every stage is a module runnable as ``uv run python -m pipeline.<stage>``. Stages read
and write JSON and SQLite under ``data/`` and skip work whose inputs have not changed.
See SPEC.md for the contracts.
"""
