"""Compute tests: match rules, span, arithmetic, ranking, thresholds, caching."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pipeline import cache, compute

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def msg(id_, subject_norm="", body="", from_addr="a@x", date="2001-01-01T00:00:00Z"):
    return {
        "id": id_,
        "subject_norm": subject_norm,
        "body_lower": body.lower(),
        "from_addr": from_addr,
        "date_iso": date,
    }


MESSAGES = [
    msg("m1", "daily nomination", "please confirm the nomination", "alice@x", "2001-01-01T00:00:00Z"),
    msg("m2", "re nomination sheet", "volumes attached", "bob@x", "2001-01-15T00:00:00Z"),
    msg("m3", "meter recap", "numbers tie to the nomination", "alice@x", "2001-02-01T00:00:00Z"),
    msg("m4", "lunch", "tacos", "carol@x", "2001-03-02T00:00:00Z"),
    msg("m5", "undated thing", "nomination", "alice@x", None),
]


# ---------------------------------------------------------------------------
# Constants the brief fixes.
# ---------------------------------------------------------------------------


def test_constants():
    assert compute.ARTIFACT_THRESHOLD == 1500
    assert compute.RATE == 85


# ---------------------------------------------------------------------------
# Match rules.
# ---------------------------------------------------------------------------


def test_subject_regex_only():
    rule = compute.compile_rule({"subject_regex": "nomination", "body_any": [], "from_any": []})
    assert compute.count_matches(rule, MESSAGES) == ["m1", "m2"]


def test_subject_regex_is_case_insensitive():
    rule = compute.compile_rule({"subject_regex": "NOMINATION"})
    assert compute.count_matches(rule, MESSAGES) == ["m1", "m2"]


def test_body_any_only():
    rule = compute.compile_rule({"body_any": ["Nomination", "tacos"]})
    assert compute.count_matches(rule, MESSAGES) == ["m1", "m3", "m4", "m5"]


def test_from_any_only():
    rule = compute.compile_rule({"from_any": ["ALICE@x"]})
    assert compute.count_matches(rule, MESSAGES) == ["m1", "m3", "m5"]


def test_parts_are_anded():
    rule = compute.compile_rule({"subject_regex": "nomination", "body_any": ["nomination"], "from_any": ["alice@x"]})
    assert compute.count_matches(rule, MESSAGES) == ["m1"]
    rule = compute.compile_rule({"body_any": ["nomination"], "from_any": ["bob@x"]})
    assert compute.count_matches(rule, MESSAGES) == []


def test_all_empty_rule_matches_nothing():
    for rule in ({}, None, {"subject_regex": "", "body_any": [], "from_any": []}, {"body_any": ["  "]}):
        compiled = compute.compile_rule(rule)
        assert compiled["empty"] is True
        assert compute.count_matches(compiled, MESSAGES) == []


def test_invalid_regex_matches_nothing_and_reports():
    rule = compute.compile_rule({"subject_regex": "(unclosed", "body_any": ["nomination"]})
    assert rule["error"].startswith("invalid subject_regex")
    assert compute.count_matches(rule, MESSAGES) == []


# ---------------------------------------------------------------------------
# Arithmetic.
# ---------------------------------------------------------------------------


def test_span_months():
    assert compute.span_months([]) == 1.0
    assert compute.span_months(["2001-01-01T00:00:00Z"]) == 1.0
    assert compute.span_months(["2001-01-01T00:00:00Z", "2001-01-10T00:00:00Z", None]) == 1.0
    span = compute.span_months(["2001-01-01T00:00:00Z", "2001-03-02T00:00:00Z"])
    assert span == pytest.approx(60 / 30.44)


def test_money():
    got = compute.money(matches=28, span=2.0, minutes=15)
    assert got == {"instances_per_month": 14.0, "hours_per_month": 3.5, "dollars_per_month": 297.5}
    assert compute.money(0, 3.0, 20)["dollars_per_month"] == 0.0


def test_as_number():
    assert compute.as_number("12") == 12.0
    assert compute.as_number(None) == 0.0
    assert compute.as_number("x") == 0.0
    assert compute.as_number(-5) == 0.0


def test_slugify():
    assert compute.slugify("Auto-parse nomination emails!") == "auto-parse-nomination-emails"
    assert compute.slugify("") == "opportunity"


# ---------------------------------------------------------------------------
# build_report on in-memory data.
# ---------------------------------------------------------------------------

LOOKUP = {m["id"]: {"id": m["id"], "path": f"p/{m['id']}", "from": m["from_addr"], "date": (m["date_iso"] or "")[:10] or None, "subject": m["subject_norm"]} for m in MESSAGES}
TOTALS = {"messages": 6, "unique": 5, "duplicates": 1, "undated": 1, "corpus_hash": "abc"}


def synthesis():
    return {
        "processes": [
            {
                "process_id": "p01",
                "name": "Nominations",
                "match_rule": {"subject_regex": "nomination", "body_any": [], "from_any": []},
                "minutes_per_instance": 20,
                "expected_matches": ["m1", "m2", "m3"],
                "evidence": [{"message_id": "m1", "quote": "please confirm"}],
            },
            {
                "process_id": "p02",
                "name": "Nothing",
                "match_rule": {},
                "evidence": [{"message_id": "m4", "quote": "tacos"}],
            },
        ],
        "opportunities": [
            {"opportunity_id": "o01", "process_id": "p01", "title": "Parse nominations", "minutes_saved_per_instance": 30, "artifact_type": "sop", "evidence": [{"message_id": "m1", "quote": "please confirm"}]},
            {"opportunity_id": "o02", "process_id": "p01", "title": "Tiny win", "minutes_saved_per_instance": 1, "artifact_type": "checklist", "evidence": [{"message_id": "m2", "quote": "volumes"}]},
            {"opportunity_id": "o03", "process_id": "p02", "title": "Empty rule", "minutes_saved_per_instance": 60, "artifact_type": "sop", "evidence": [{"message_id": "m4", "quote": "tacos"}]},
            {"opportunity_id": "o04", "process_id": "missing", "title": "Orphan", "minutes_saved_per_instance": 60, "artifact_type": "none", "evidence": []},
        ],
    }


def test_build_report_counts_and_money():
    report = compute.build_report(synthesis(), MESSAGES, TOTALS, LOOKUP, now=NOW)
    # span: 2001-01-01 to 2001-03-02 = 60 days = 1.97 months
    assert report["span_months"] == 1.97
    assert report["rate_per_hour"] == 85
    assert report["artifact_threshold"] == 1500
    assert report["generated_at"] == "2026-01-01T00:00:00Z"
    assert report["corpus_hash"] == "abc"

    p01 = report["processes"][0]
    assert p01["match_count"] == 2
    assert p01["matched_message_ids"] == ["m1", "m2"]
    assert p01["expected_matches"] == ["m1", "m2", "m3"]
    assert p01["expected_matches_missed"] == ["m3"]
    assert p01["minutes_per_instance"] == 20
    assert p01["instances_per_month"] == round(2 / (60 / 30.44), 2)
    assert p01["evidence"][0]["from"] == "alice@x"
    assert p01["evidence"][0]["date"] == "2001-01-01"

    p02 = report["processes"][1]
    assert p02["match_count"] == 0
    assert p02["matched_message_ids"] == []
    assert p02["minutes_per_instance"] is None
    assert p02["expected_matches_missed"] == []


def test_opportunities_are_ranked_capped_and_thresholded():
    report = compute.build_report(synthesis(), MESSAGES, TOTALS, LOOKUP, now=NOW)
    opps = {o["opportunity_id"]: o for o in report["opportunities"]}
    assert [o["opportunity_id"] for o in report["opportunities"]] == ["o01", "o02", "o03", "o04"]
    assert [o["rank"] for o in report["opportunities"]] == [1, 2, 3, 4]

    o01 = opps["o01"]
    span = 60 / 30.44
    assert o01["minutes_saved_per_instance"] == 20  # capped from 30 to the process's 20
    assert o01["minutes_capped_to_process"] is True
    assert o01["match_count"] == 2
    assert o01["instances_per_month"] == round(2 / span, 2)
    assert o01["hours_per_month"] == round(2 / span * 20 / 60, 2)
    assert o01["dollars_per_month"] == round(2 / span * 20 / 60 * 85, 2)
    assert o01["threshold"] == 1500
    assert o01["artifact_type"] == "sop"
    assert o01["above_threshold"] is False
    assert o01["artifact_path"] is None
    assert o01["evidence"][0]["subject"] == "daily nomination"

    assert opps["o02"]["minutes_capped_to_process"] is False
    assert opps["o03"]["dollars_per_month"] == 0.0
    assert opps["o04"]["match_count"] == 0
    assert opps["o04"]["artifact_type"] == "none"

    totals = report["totals"]
    assert totals["opportunities"] == 4
    assert totals["above_threshold"] == 0
    assert totals["dollars_per_month"] == round(sum(o["dollars_per_month"] for o in report["opportunities"]), 2)
    assert totals["messages"] == 6 and totals["unique"] == 5 and totals["duplicates"] == 1


def test_above_threshold_gets_an_artifact_path(tmp_path):
    many = [msg(f"x{i}", "nomination", "", "a@x", "2001-01-01T00:00:00Z") for i in range(200)]
    synth = {
        "processes": [{"process_id": "p01", "match_rule": {"subject_regex": "nomination"}, "evidence": []}],
        "opportunities": [
            {"opportunity_id": "o01", "process_id": "p01", "title": "Big Win: Parse it", "minutes_saved_per_instance": 30, "artifact_type": "sop", "evidence": []},
            {"opportunity_id": "o02", "process_id": "p01", "title": "No artifact wanted", "minutes_saved_per_instance": 30, "artifact_type": "none", "evidence": []},
        ],
    }
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    (artifacts / "o01-big-win-parse-it.md").write_text("# done\n")
    report = compute.build_report(synth, many, TOTALS, {}, now=NOW, artifacts_dir=artifacts)
    o01, o02 = report["opportunities"]
    # 200 matches / 1 month * 30 min / 60 * 85 = 8500
    assert o01["dollars_per_month"] == 8500.0
    assert o01["above_threshold"] is True
    assert o01["artifact_path"] == "run/artifacts/o01-big-win-parse-it.md"
    assert o01["artifact_exists"] is True
    assert o02["above_threshold"] is False
    assert o02["artifact_path"] is None
    assert report["totals"]["above_threshold"] == 1
    assert len(report["processes"][0]["matched_message_ids"]) == 200


def test_matched_ids_are_capped_at_200():
    many = [msg(f"x{i}", "nomination") for i in range(250)]
    synth = {"processes": [{"process_id": "p01", "match_rule": {"subject_regex": "nomination"}}], "opportunities": []}
    report = compute.build_report(synth, many, TOTALS, {}, now=NOW)
    assert report["processes"][0]["match_count"] == 250
    assert len(report["processes"][0]["matched_message_ids"]) == 200


def test_malformed_synthesis_entries_are_skipped():
    synth = {"processes": ["junk", None, {"process_id": "p01", "match_rule": {"subject_regex": "x"}}], "opportunities": [42, {"process_id": "p01", "title": "t"}]}
    report = compute.build_report(synth, MESSAGES, TOTALS, LOOKUP, now=NOW)
    assert len(report["processes"]) == 1
    assert len(report["opportunities"]) == 1
    assert report["opportunities"][0]["opportunity_id"] == "t"
    assert report["opportunities"][0]["minutes_saved_per_instance"] == 0.0


# ---------------------------------------------------------------------------
# End to end on the parsed fixture db.
# ---------------------------------------------------------------------------


def test_run_end_to_end_and_cached(parsed, rows, data_dir):
    good = rows["alpha-a/inbox/1."]["id"]
    synth = {
        "processes": [{"process_id": "p01", "name": "Nominations", "match_rule": {"subject_regex": "nomination"}, "evidence": [{"message_id": good, "quote": "Please confirm"}]}],
        "opportunities": [{"opportunity_id": "o01", "process_id": "p01", "title": "Auto confirm", "minutes_saved_per_instance": 10, "artifact_type": "email_template", "evidence": [{"message_id": good, "quote": "Please confirm"}]}],
    }
    cache.write_json_atomic(data_dir / "synthesis.json", synth)
    report = compute.run(data_dir, run_dir=data_dir)
    assert (data_dir / "report.json").exists()
    # Two messages with "nomination" in subject_norm are non-duplicates: 1. and 3.
    assert report["processes"][0]["match_count"] == 2
    assert set(report["processes"][0]["matched_message_ids"]) == {rows["alpha-a/inbox/1."]["id"], rows["alpha-a/sent/3."]["id"]}
    assert report["totals"] == {
        "messages": 6, "unique": 5, "duplicates": 1, "undated": 1,
        "processes": 1, "opportunities": 1, "above_threshold": 0,
        "hours_per_month": report["opportunities"][0]["hours_per_month"],
        "dollars_per_month": report["opportunities"][0]["dollars_per_month"],
    }
    # Fixture dates span 8 Jan to 10 Jan 2001, so the span floors at 1 month.
    assert report["span_months"] == 1.0
    assert report["opportunities"][0]["instances_per_month"] == 2.0
    assert report["opportunities"][0]["hours_per_month"] == round(2 * 10 / 60, 2)
    assert report["opportunities"][0]["evidence"][0]["from"] == "alice@example.com"
    assert report["opportunities"][0]["evidence"][0]["date"] == "2001-01-08"
    assert report["opportunities"][0]["evidence"][0]["subject"] == "Daily nomination"

    path = data_dir / "report.json"
    before = os.stat(path).st_mtime_ns
    compute.run(data_dir, run_dir=data_dir)
    assert os.stat(path).st_mtime_ns == before

    synth["opportunities"][0]["minutes_saved_per_instance"] = 20
    cache.write_json_atomic(data_dir / "synthesis.json", synth)
    again = compute.run(data_dir, run_dir=data_dir)
    assert again["opportunities"][0]["hours_per_month"] == round(2 * 20 / 60, 2)


def test_run_requires_synthesis(parsed, data_dir):
    with pytest.raises(SystemExit):
        compute.run(data_dir)


def test_main_prints_summary(parsed, rows, data_dir, capsys):
    cache.write_json_atomic(data_dir / "synthesis.json", {"processes": [], "opportunities": []})
    assert compute.main(["--data", str(data_dir)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["artifact_threshold"] == 1500
    assert out["rate_per_hour"] == 85
    assert out["totals"]["opportunities"] == 0
