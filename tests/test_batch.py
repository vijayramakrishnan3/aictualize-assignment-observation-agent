"""Batch packing and index tests."""

from __future__ import annotations

import json
import os
from pathlib import Path

from pipeline import batch, cache


def entry(id_: str, body: str, mailbox: str = "m", date: str | None = "2001-01-01") -> dict:
    return {
        "id": id_,
        "date": date,
        "from": "a@x",
        "to": ["b@x"],
        "subject": "s",
        "mailbox": mailbox,
        "body": body,
        "truncated": False,
    }


def test_pack_respects_the_cap():
    overhead = batch.header_chars(entry("1", ""))
    cap = overhead * 3 + 300
    entries = [entry(str(i), "x" * 100) for i in range(7)]
    batches = batch.pack(entries, cap=cap)
    # Each entry costs overhead + 100, so three fit and the fourth spills.
    assert [len(b) for b in batches] == [3, 3, 1]
    for b in batches:
        assert sum(batch.entry_chars(e) for e in b) <= cap
    # Order is preserved.
    assert [e["id"] for b in batches for e in b] == [str(i) for i in range(7)]


def test_oversized_entry_is_truncated_alone():
    cap = 500
    entries = [entry("small", "a" * 10), entry("big", "b" * 5000), entry("after", "c" * 10)]
    batches = batch.pack(entries, cap=cap)
    assert [[e["id"] for e in b] for b in batches] == [["small"], ["big"], ["after"]]
    big = batches[1][0]
    assert big["truncated"] is True
    assert batch.entry_chars(big) <= cap
    assert big["body"] == "b" * (cap - batch.header_chars(big))
    assert batches[0][0]["truncated"] is False
    # The original entry object was not mutated.
    assert entries[1]["truncated"] is False


def test_pack_empty():
    assert batch.pack([]) == []


def test_run_writes_batches_and_index(parsed, data_dir):
    index = batch.run(data_dir)
    assert index["total"] == 1
    assert index["batches"][0]["batch_id"] == "batch_001"
    # Non-duplicate messages only: 6 parsed, 1 duplicate.
    assert index["batches"][0]["messages"] == 5
    assert index["batches"][0]["done"] is False
    assert index["corpus_hash"] == parsed["corpus_hash"]

    doc = json.loads((data_dir / "batches" / "batch_001.json").read_text())
    assert doc["batch_id"] == "batch_001"
    assert doc["corpus_hash"] == parsed["corpus_hash"]
    ids = [m["id"] for m in doc["messages"]]
    assert len(ids) == len(set(ids)) == 5
    for m in doc["messages"]:
        assert set(m) == {"id", "date", "from", "to", "subject", "mailbox", "body", "truncated"}
        assert m["truncated"] is False


def test_batches_are_ordered_by_mailbox_then_date_with_undated_last(parsed, data_dir):
    batch.run(data_dir)
    doc = json.loads((data_dir / "batches" / "batch_001.json").read_text())
    msgs = doc["messages"]
    mailboxes = [m["mailbox"] for m in msgs]
    assert mailboxes == sorted(mailboxes)
    alpha = [m for m in msgs if m["mailbox"] == "alpha-a"]
    dated = [m["date"] for m in alpha if m["date"]]
    assert dated == sorted(dated)
    assert alpha[-1]["date"] is None  # the malformed-header message sorts last


def test_done_flag_tracks_extraction_files(parsed, data_dir):
    batch.run(data_dir)
    ext = data_dir / "extractions"
    ext.mkdir()
    cache.write_json_atomic(ext / "batch_001.json", {"batch_id": "batch_001", "corpus_hash": "stale", "observations": []})
    assert batch.run(data_dir)["batches"][0]["done"] is False
    cache.write_json_atomic(
        ext / "batch_001.json",
        {"batch_id": "batch_001", "corpus_hash": parsed["corpus_hash"], "observations": []},
    )
    index = batch.run(data_dir)
    assert index["batches"][0]["done"] is True
    assert index["done"] == 1


def test_second_run_does_not_rewrite_batch_files(parsed, data_dir):
    batch.run(data_dir)
    path = data_dir / "batches" / "batch_001.json"
    before = os.stat(path).st_mtime_ns
    batch.run(data_dir)
    assert os.stat(path).st_mtime_ns == before


def test_small_cap_splits_fixture_into_several_batches(parsed, data_dir):
    index = batch.run(data_dir, cap=250)
    assert index["total"] > 1
    files = sorted((data_dir / "batches").glob("batch_*.json"))
    assert [f.stem for f in files] == [b["batch_id"] for b in index["batches"]]
    assert sum(b["messages"] for b in index["batches"]) == 5
