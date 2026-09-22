"""Shared fixtures. Everything runs against tests/fixtures/corpus, never the real corpus."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pipeline import parse

FIXTURE_CORPUS = Path(__file__).parent / "fixtures" / "corpus"
NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.fixture
def corpus_dir(tmp_path: Path) -> Path:
    """A private copy of the fixture corpus so tests can add files to it."""
    dst = tmp_path / "corpus"
    shutil.copytree(FIXTURE_CORPUS, dst)
    return dst


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    d = tmp_path / "data"
    d.mkdir()
    return d


@pytest.fixture
def parsed(corpus_dir: Path, data_dir: Path) -> dict:
    """Run the parser on the fixture corpus. Returns the stats dict."""
    return parse.parse_corpus(corpus_dir, data_dir, now=NOW)


@pytest.fixture
def rows(parsed, data_dir: Path) -> dict[str, dict]:
    """Every parsed row keyed by relative path."""
    con = parse.open_db(data_dir / "messages.db")
    try:
        out = {r["path"]: dict(r) for r in con.execute("SELECT * FROM messages")}
    finally:
        con.close()
    return out
