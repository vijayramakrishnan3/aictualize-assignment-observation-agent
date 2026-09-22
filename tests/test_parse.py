"""Parser tests on the six fixture messages plus unit tests on the pure helpers."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from pipeline import parse
from tests.conftest import NOW


# ---------------------------------------------------------------------------
# Whole-corpus behaviour on the fixture directory.
# ---------------------------------------------------------------------------


def test_parses_every_fixture_file(parsed, rows):
    assert parsed["files_read"] == 6
    assert parsed["parsed"] == 6
    assert parsed["failed"] == 0
    assert set(rows) == {
        "alpha-a/inbox/1.",
        "alpha-a/inbox/2.",
        "alpha-a/inbox/4.",
        "alpha-a/inbox/5.",
        "alpha-a/sent/3.",
        "beta-b/inbox/6.",
    }


def test_id_is_sha1_prefix_of_raw_bytes(rows, corpus_dir):
    import hashlib

    raw = (corpus_dir / "alpha-a/inbox/1.").read_bytes()
    assert rows["alpha-a/inbox/1."]["id"] == hashlib.sha1(raw).hexdigest()[:12]


def test_mailbox_and_folder_come_from_the_path(rows):
    r = rows["alpha-a/sent/3."]
    assert r["mailbox"] == "alpha-a"
    assert r["folder"] == "sent"


def test_headers_are_lowercased_and_listed(rows):
    r = rows["alpha-a/inbox/4."]
    assert r["from_addr"] == "carol@example.com"
    assert json.loads(r["to_addrs"]) == ["alice@example.com"]
    assert json.loads(r["cc_addrs"]) == ["bob@example.com", "dave@example.com"]
    assert r["header_message_id"] == "<1004.fixture@thyme>"
    assert r["subject"] == "RE: Meter 984132 recap"


def test_crlf_file_is_normalized(rows):
    r = rows["alpha-a/inbox/1."]
    assert "\r" not in r["body_raw"]
    assert r["body_clean"] == "Please confirm the nomination for tomorrow.\n\nThanks,\nAlice"
    assert r["char_len"] == len(r["body_clean"])


def test_duplicate_is_marked_against_earliest_path(parsed, rows):
    canonical = rows["alpha-a/inbox/1."]
    dup = rows["alpha-a/inbox/2."]
    assert canonical["dup_of"] is None
    assert dup["dup_of"] == canonical["id"]
    assert parsed["duplicates"] == 1
    assert parsed["unique"] == 5
    # The reply in the thread is not a duplicate even though the subject matches.
    assert rows["alpha-a/sent/3."]["dup_of"] is None


def test_undated_message_gets_date_from_its_thread(parsed, rows):
    r = rows["alpha-a/sent/3."]
    assert r["date_source"] == "inferred"
    assert r["date_iso"] == rows["alpha-a/inbox/1."]["date_iso"]
    assert r["thread_key"] == rows["alpha-a/inbox/1."]["thread_key"]
    assert parsed["inferred_dates"] == 1


def test_malformed_header_does_not_crash_and_stays_undated(parsed, rows):
    r = rows["alpha-a/inbox/5."]
    assert r["date_iso"] is None
    assert r["date_source"] is None
    assert r["from_addr"] == "dave@example.com"
    assert r["subject"] == "Broken header"
    assert "body is fine" in r["body_clean"]
    assert parsed["undated"] == 1


def test_quoted_reply_is_stripped_from_clean_but_kept_in_raw(rows):
    r = rows["alpha-a/inbox/4."]
    assert r["body_clean"] == (
        "Numbers look right to me. Volumes tie to the scheduled quantity.\n\nCarol"
    )
    assert "Here is the recap for the meter" in r["body_raw"]
    assert "Original Message" in r["body_raw"]


def test_on_wrote_and_angle_quotes_are_stripped(rows):
    r = rows["beta-b/inbox/6."]
    assert r["body_clean"] == "Forwarding this so it does not get lost."
    assert "Two shippers called" in r["body_raw"]


def test_subject_norm_strips_prefix_chains(rows):
    assert rows["alpha-a/inbox/2."]["subject_norm"] == "daily nomination"
    assert rows["alpha-a/sent/3."]["subject_norm"] == "daily nomination"
    assert rows["beta-b/inbox/6."]["subject_norm"] == "capacity posting"


def test_raw_files_and_stats_are_written(parsed, rows, data_dir):
    for r in rows.values():
        assert (data_dir / "raw" / f"{r['id']}.txt").exists()
    stats = json.loads((data_dir / "parse_stats.json").read_text())
    assert stats["files_read"] == 6
    assert stats["largest"]["path"] == "alpha-a/inbox/4."
    assert stats["largest"]["bytes"] > 0


def test_second_run_is_skipped(parsed, corpus_dir, data_dir):
    db = data_dir / "messages.db"
    before = os.stat(db).st_mtime_ns
    again = parse.parse_corpus(corpus_dir, data_dir, now=NOW)
    assert os.stat(db).st_mtime_ns == before
    assert again["files_read"] == parsed["files_read"]


def test_changed_corpus_reparses(parsed, corpus_dir, data_dir):
    (corpus_dir / "beta-b/inbox/7.").write_bytes(
        b"Message-ID: <1007@thyme>\nDate: Thu, 11 Jan 2001 08:00:00 -0800\n"
        b"From: erin@example.com\nTo: frank@example.com\nSubject: New\n\nHello\n"
    )
    again = parse.parse_corpus(corpus_dir, data_dir, now=NOW)
    assert again["files_read"] == 7


def test_byte_identical_files_share_an_id_and_both_survive(corpus_dir, data_dir):
    src = corpus_dir / "alpha-a/inbox/1."
    (corpus_dir / "beta-b/inbox/9.").write_bytes(src.read_bytes())
    parse.parse_corpus(corpus_dir, data_dir, now=NOW)
    con = parse.open_db(data_dir / "messages.db")
    try:
        got = con.execute(
            "SELECT path, id, dup_of FROM messages WHERE path IN (?, ?) ORDER BY path",
            ("alpha-a/inbox/1.", "beta-b/inbox/9."),
        ).fetchall()
    finally:
        con.close()
    assert len(got) == 2
    assert got[0]["id"] == got[1]["id"]
    assert got[0]["dup_of"] is None
    assert got[1]["dup_of"] == got[0]["id"]


def test_garbage_file_is_logged_not_fatal(corpus_dir, data_dir):
    (corpus_dir / "beta-b/inbox/8.").write_bytes(b"\x00\xff\xfe not an email at all")
    stats = parse.parse_corpus(corpus_dir, data_dir, now=NOW)
    assert stats["files_read"] == 7
    assert stats["parsed"] + stats["failed"] == 7


# ---------------------------------------------------------------------------
# Pure helpers.
# ---------------------------------------------------------------------------


def test_normalize_subject():
    assert parse.normalize_subject("RE: FW: Fwd:  Daily   nomination ") == "daily nomination"
    assert parse.normalize_subject("Re[2]: thing") == "thing"
    assert parse.normalize_subject("Forecast (re: nothing)") == "forecast (re: nothing)"
    assert parse.normalize_subject("") == ""
    assert parse.normalize_subject(None) == ""


def test_parse_date_converts_to_utc():
    assert parse.parse_date("Fri, 14 Dec 2001 08:11:23 -0800 (PST)", now=NOW) == "2001-12-14T16:11:23Z"


def test_parse_date_rejects_garbage_future_and_ancient():
    assert parse.parse_date("Tues, 32 Febuary 2001 25:61:00", now=NOW) is None
    assert parse.parse_date("Wed, 12 Mar 2031 08:14:00 -0600 (CST)", now=NOW) is None
    assert parse.parse_date("Mon, 1 Jan 1979 00:00:00 +0000", now=NOW) is None
    assert parse.parse_date("", now=NOW) is None
    assert parse.parse_date(None, now=NOW) is None


def test_parse_date_treats_naive_as_utc():
    assert parse.parse_date("Mon, 8 Jan 2001 09:15:00", now=NOW) == "2001-01-08T09:15:00Z"


def test_strip_quoted_cut_points():
    assert parse.strip_quoted("keep\n-----Original Message-----\nFrom: x\ndrop") == "keep"
    assert parse.strip_quoted("keep\n -----Original Message-----\ndrop") == "keep"
    assert parse.strip_quoted("keep\nOn Tue, Bob wrote:\n> drop") == "keep"
    assert parse.strip_quoted("keep\n> drop\n> drop") == "keep"
    assert parse.strip_quoted("keep\n\nFrom: Someone\nSent: now\ndrop") == "keep"
    assert parse.strip_quoted("keep\n---------- Forwarded by Bob on 01/01 ----------\ndrop") == "keep"
    # From: without a preceding blank line is ordinary text and stays.
    assert parse.strip_quoted("keep\nFrom: here it is not a header") == "keep\nFrom: here it is not a header"


def test_strip_quoted_trims_signature_and_whitespace():
    body = "line one   \n\n\n\nline two\n-- \nBob Signature\n"
    assert parse.strip_quoted(body) == "line one\n\nline two"


def test_parse_addrs():
    assert parse.parse_addrs(["Alice <ALICE@Example.com>, bob@example.com"]) == [
        "alice@example.com",
        "bob@example.com",
    ]
    assert parse.parse_addrs([]) == []
    assert parse.parse_addrs(None) == []


def test_thread_key_ignores_participant_order():
    a = parse.thread_key_for("x", ["a@x", "b@x"])
    b = parse.thread_key_for("x", ["b@x", "a@x", "a@x"])
    assert a == b
    assert parse.thread_key_for("y", ["a@x", "b@x"]) != a


def test_tolerant_headers_unfold_and_skip_junk():
    block = "From: a@x\nTo: b@x,\n\tc@x\nnot a header\nSubject: hi"
    got = parse.tolerant_headers(block)
    assert got == {"from": ["a@x"], "to": ["b@x, c@x"], "subject": ["hi"]}
