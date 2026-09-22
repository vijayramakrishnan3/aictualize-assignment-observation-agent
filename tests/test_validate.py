"""Validator tests: accept and reject cases, whitespace tolerance, file modes."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from pipeline import cache, validate

BODIES = {
    "m1": (
        "Please confirm the nomination for tomorrow. Thanks, Alice",
        "Please confirm the nomination for tomorrow. Thanks, Alice -----Original Message----- Old quoted text here",
    ),
}


# ---------------------------------------------------------------------------
# check_quote
# ---------------------------------------------------------------------------


def test_exact_substring_passes():
    assert validate.check_quote("confirm the nomination", "m1", BODIES) is None


def test_whitespace_differences_pass():
    assert validate.check_quote("confirm   the\n\tnomination", "m1", BODIES) is None
    assert validate.check_quote("  confirm the nomination  ", "m1", BODIES) is None
    assert validate.check_quote("Please confirm the nomination for tomorrow.\nThanks, Alice", "m1", BODIES) is None


def test_case_difference_fails():
    assert validate.check_quote("Confirm The Nomination", "m1", BODIES) is not None


def test_quote_found_only_in_raw_passes():
    assert validate.check_quote("Old quoted text", "m1", BODIES) is None


def test_reject_reasons():
    assert validate.check_quote("not in there", "m1", BODIES) == "quote is not a substring of the message"
    assert validate.check_quote("confirm", "nope", BODIES) == "unknown message_id"
    assert validate.check_quote("", "m1", BODIES) == "empty quote"
    assert validate.check_quote("   \n ", "m1", BODIES) == "empty quote"
    assert validate.check_quote(None, "m1", BODIES) == "quote is not a string"
    assert validate.check_quote("confirm", None, BODIES) == "missing message_id"
    assert validate.check_quote("confirm", "", BODIES) == "missing message_id"


# ---------------------------------------------------------------------------
# validate_items
# ---------------------------------------------------------------------------


def test_partial_evidence_survives_and_bad_is_rejected():
    items = [
        {
            "process": "Nominations",
            "evidence": [
                {"message_id": "m1", "quote": "confirm the nomination"},
                {"message_id": "m1", "quote": "this was never written"},
                "not an object",
            ],
        }
    ]
    kept, rejects, passed, failed = validate.validate_items(items, BODIES, {"batch_id": "b"})
    assert passed == 1
    assert failed == 2
    assert len(kept) == 1
    assert kept[0]["evidence"] == [{"message_id": "m1", "quote": "confirm the nomination"}]
    assert kept[0]["process"] == "Nominations"
    assert {r["reason"] for r in rejects} == {
        "quote is not a substring of the message",
        "evidence is not an object",
    }
    assert all(r["batch_id"] == "b" for r in rejects)


def test_item_with_no_surviving_evidence_is_dropped():
    items = [{"process": "Ghost", "evidence": [{"message_id": "m1", "quote": "nope"}]}]
    kept, rejects, passed, failed = validate.validate_items(items, BODIES)
    assert kept == []
    assert passed == 0 and failed == 1
    assert rejects[-1]["reason"] == "no surviving evidence, item dropped"
    assert rejects[-1]["process"] == "Ghost"


def test_item_without_evidence_key_is_dropped():
    kept, rejects, passed, failed = validate.validate_items([{"process": "None"}], BODIES)
    assert kept == [] and passed == 0 and failed == 0
    assert len(rejects) == 1


def test_original_items_are_not_mutated():
    items = [{"process": "P", "evidence": [{"message_id": "m1", "quote": "confirm"}, {"message_id": "m1", "quote": "zzz"}]}]
    validate.validate_items(items, BODIES)
    assert len(items[0]["evidence"]) == 2


# ---------------------------------------------------------------------------
# Against a real parsed fixture db.
# ---------------------------------------------------------------------------


def _extraction(rows, batch_id="batch_001", corpus_hash="h"):
    good = rows["alpha-a/inbox/4."]
    quoted = rows["beta-b/inbox/6."]
    return {
        "batch_id": batch_id,
        "corpus_hash": corpus_hash,
        "observations": [
            {
                "process": "Meter recaps",
                "evidence": [
                    {"message_id": good["id"], "quote": "Volumes  tie to the\nscheduled quantity"},
                    {"message_id": good["id"], "quote": "recap for the meter in the usual format"},
                    {"message_id": good["id"], "quote": "volumes tie to the scheduled quantity"},
                ],
            },
            {
                "process": "Capacity posting",
                "evidence": [{"message_id": quoted["id"], "quote": "Two shippers called before it was live."}],
            },
            {
                "process": "Invented",
                "evidence": [{"message_id": "000000000000", "quote": "anything"}],
            },
        ],
    }


def test_load_bodies_prefers_canonical_row(parsed, rows, data_dir):
    bodies = validate.load_bodies(data_dir / "messages.db")
    assert set(bodies) == {r["id"] for r in rows.values()}
    clean, raw = bodies[rows["alpha-a/inbox/4."]["id"]]
    assert "Original Message" not in clean
    assert "Original Message" in raw


def test_run_extractions_writes_validated_summary_and_rejects(parsed, rows, data_dir):
    ext = data_dir / "extractions"
    ext.mkdir()
    cache.write_json_atomic(ext / "batch_001.json", _extraction(rows))
    summary = validate.run_extractions(data_dir)
    assert summary["files"] == 1
    assert summary["pass"] == 3
    assert summary["fail"] == 2
    assert summary["observations_in"] == 3
    assert summary["observations_out"] == 2

    validated = json.loads((data_dir / "validated" / "batch_001.json").read_text())
    assert validated["batch_id"] == "batch_001"
    assert validated["corpus_hash"] == "h"
    assert [o["process"] for o in validated["observations"]] == ["Meter recaps", "Capacity posting"]
    assert len(validated["observations"][0]["evidence"]) == 2

    rejects = json.loads((data_dir / "validated" / "rejects.json").read_text())
    reasons = sorted(r["reason"] for r in rejects)
    assert reasons == [
        "no surviving evidence, item dropped",
        "quote is not a substring of the message",
        "unknown message_id",
    ]
    summary_file = json.loads((data_dir / "validated" / "summary.json").read_text())
    assert summary_file["batches"][0]["pass"] == 3


def test_run_extractions_is_cached(parsed, rows, data_dir):
    ext = data_dir / "extractions"
    ext.mkdir()
    cache.write_json_atomic(ext / "batch_001.json", _extraction(rows))
    validate.run_extractions(data_dir)
    out = data_dir / "validated" / "batch_001.json"
    before = os.stat(out).st_mtime_ns
    validate.run_extractions(data_dir)
    assert os.stat(out).st_mtime_ns == before
    cache.write_json_atomic(ext / "batch_002.json", _extraction(rows, batch_id="batch_002"))
    summary = validate.run_extractions(data_dir)
    assert summary["files"] == 2


def test_unreadable_extraction_file_is_reported_not_fatal(parsed, data_dir):
    ext = data_dir / "extractions"
    ext.mkdir()
    (ext / "batch_001.json").write_text("{not json")
    summary = validate.run_extractions(data_dir)
    assert summary["pass"] == 0
    assert summary["observations_out"] == 0
    assert (data_dir / "validated" / "batch_001.json").exists()


def test_single_file_mode_prints_counts(parsed, rows, data_dir, capsys):
    ext = data_dir / "extractions"
    ext.mkdir()
    path = ext / "batch_009.json"
    cache.write_json_atomic(path, _extraction(rows, batch_id="batch_009"))
    assert validate.main(["--data", str(data_dir), "--file", str(path)]) == 0
    assert capsys.readouterr().out.strip() == "pass=3 fail=2"
    assert (data_dir / "validated" / "batch_009.json").exists()


def test_synthesis_mode_drops_processes_and_orphaned_opportunities(parsed, rows, data_dir, capsys):
    good = rows["alpha-a/inbox/4."]["id"]
    synthesis = {
        "processes": [
            {"process_id": "p01", "name": "Meter recaps", "match_rule": {}, "evidence": [
                {"message_id": good, "quote": "Numbers look right to me."},
                {"message_id": good, "quote": "made up"},
            ]},
            {"process_id": "p02", "name": "Ghost", "match_rule": {}, "evidence": [
                {"message_id": good, "quote": "made up"},
            ]},
        ],
        "opportunities": [
            {"opportunity_id": "o01", "process_id": "p01", "evidence": [{"message_id": good, "quote": "Carol"}]},
            {"opportunity_id": "o02", "process_id": "p02", "evidence": [{"message_id": good, "quote": "Carol"}]},
            {"opportunity_id": "o03", "process_id": "p01", "evidence": [{"message_id": good, "quote": "nope"}]},
        ],
    }
    cache.write_json_atomic(data_dir / "synthesis.json", synthesis)
    assert validate.main(["--data", str(data_dir), "--synthesis"]) == 0
    assert capsys.readouterr().out.strip() == "pass=3 fail=3"

    out = json.loads((data_dir / "synthesis.json").read_text())
    assert [p["process_id"] for p in out["processes"]] == ["p01"]
    assert out["processes"][0]["evidence"] == [{"message_id": good, "quote": "Numbers look right to me."}]
    assert [o["opportunity_id"] for o in out["opportunities"]] == ["o01"]

    backup = json.loads((data_dir / "synthesis.unvalidated.json").read_text())
    assert backup == synthesis
    rejects = json.loads((data_dir / "validated" / "synthesis_rejects.json").read_text())
    assert any(r.get("opportunity_id") == "o02" and "process was dropped" in r["reason"] for r in rejects)
    assert any(r.get("opportunity_id") == "o03" and r["reason"] == "no surviving evidence, item dropped" for r in rejects)


def test_synthesis_mode_leaves_a_clean_file_untouched(parsed, rows, data_dir):
    good = rows["alpha-a/inbox/4."]["id"]
    synthesis = {
        "processes": [{"process_id": "p01", "evidence": [{"message_id": good, "quote": "Carol"}]}],
        "opportunities": [{"opportunity_id": "o01", "process_id": "p01", "evidence": [{"message_id": good, "quote": "Carol"}]}],
    }
    path = data_dir / "synthesis.json"
    cache.write_json_atomic(path, synthesis)
    before = os.stat(path).st_mtime_ns
    counts = validate.run_synthesis(data_dir)
    assert counts == {"pass": 2, "fail": 0, "processes_in": 1, "processes_out": 1, "opportunities_in": 1, "opportunities_out": 1}
    assert os.stat(path).st_mtime_ns == before
    assert not (data_dir / "synthesis.unvalidated.json").exists()


def test_synthesis_mode_requires_the_file(parsed, data_dir):
    with pytest.raises(SystemExit):
        validate.run_synthesis(data_dir)
