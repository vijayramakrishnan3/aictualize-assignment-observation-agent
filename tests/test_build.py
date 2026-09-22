"""Tests for pipeline/build.py and pipeline/serve.py. Fixture-based, no model calls.

The fixture generator below writes a realistic data/report.json (3 processes,
5 opportunities), a throwaway messages.db, raw message files, and three
artifacts, so build.py can be exercised end to end in a temp directory.

To look at the dashboard by hand:

    uv run python tests/test_build.py --write /tmp/obs-fixture
    uv run python -m pipeline.build --data /tmp/obs-fixture/data --run /tmp/obs-fixture/run
    uv run python -m pipeline.serve --dir /tmp/obs-fixture/run/dashboard
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
import sqlite3
import sys
import threading
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline import build, serve  # noqa: E402

TEMPLATE_DIR = ROOT / "dashboard"
RATE = 85
THRESHOLD = 1500
SPAN_MONTHS = 14.2


# ---------------------------------------------------------------- fixture data


def _raw(message_id_hdr, date, from_addr, to, subject, body, mailbox="farmer-d", folder="logistics", cc=""):
    return (
        f"Message-ID: <{message_id_hdr}.JavaMail.evans@thyme>\n"
        f"Date: {date}\n"
        f"From: {from_addr}\n"
        f"To: {to}\n"
        f"Subject: {subject}\n"
        f"Cc: {cc}\n"
        "Mime-Version: 1.0\n"
        "Content-Type: text/plain; charset=us-ascii\n"
        "Content-Transfer-Encoding: 7bit\n"
        f"X-Folder: \\ExMerge - {mailbox}\\{folder}\n"
        f"X-Origin: {mailbox.upper()}\n"
        "\n"
        f"{body}\n"
    )


# (header id, RFC date, iso date, from, to, subject, body, mailbox, folder)
RAW_MESSAGES = [
    (
        "32394345.1075840432744", "Fri, 26 Oct 2001 13:53:09 -0700 (PDT)", "2001-10-26T20:53:09+00:00",
        "richard.pinion@enron.com", "j..farmer@enron.com, lisa.kinsey@enron.com",
        "Pipeline Nominations away from the office",
        "These troubled times mandate that Enron take a fresh look at our contingency plans for "
        "conducting business away from the office.  Bob Superty has asked me to put together a "
        "survey on processes and equipment that could be used if schedulers could not get into "
        "the office.\n\nPlease forward this memo and ask your respective schedulers to respond by "
        "Friday.\n\nRichard",
        "farmer-d", "logistics",
    ),
    (
        "18820340.1075840433001", "Mon, 05 Nov 2001 07:12:44 -0800 (PST)", "2001-11-05T15:12:44+00:00",
        "j..farmer@enron.com", "victor.lamadrid@enron.com",
        "RE: Nov noms - Texas Eastern",
        "Victor,\n\nThe nomination for TETCO did not confirm until 9:40 this morning. I had to re-key "
        "the volumes from the spreadsheet into Unify again because the confirmation came back with a "
        "different meter total.\n\nCan you call the pipeline and see why the confirmations are coming "
        "back late every day this week?\n\nDaren",
        "farmer-d", "logistics",
    ),
    (
        "27410981.1075840433210", "Tue, 13 Nov 2001 16:02:10 -0800 (PST)", "2001-11-14T00:02:10+00:00",
        "victor.lamadrid@enron.com", "j..farmer@enron.com, patti.sullivan@enron.com",
        "FW: daily nomination confirmations",
        "Here is the status of today's noms.\n\nHPL confirmed at 100%. TETCO cut us 2,000 at Katy. "
        "Transco is still pending, they said the scheduler is out and the backup does not have the "
        "spreadsheet.\n\nI will send the final once Transco confirms.\n\nVictor",
        "farmer-d", "logistics",
    ),
    (
        "30112009.1075840433555", "Wed, 05 Dec 2001 10:31:00 -0800 (PST)", "2001-12-05T18:31:00+00:00",
        "j..farmer@enron.com", "lisa.kinsey@enron.com",
        "nominations for 12/6",
        "Lisa,\n\nPlease nominate 5,000 at Katy and 3,200 at Bammel for tomorrow. Same counterparties "
        "as today. Let me know when the pipeline confirms so I can update the sheet.\n\nThanks,\nDaren",
        "farmer-d", "logistics",
    ),
    (
        "41209877.1075840501122", "Thu, 04 Oct 2001 09:15:33 -0700 (PDT)", "2001-10-04T16:15:33+00:00",
        "darron.giron@enron.com", "j..farmer@enron.com",
        "Meter 9843 volume variance",
        "Daren,\n\nMeter 9843 shows a 1,150 MMBtu variance between the nominated and the actual for "
        "September. The actuals came in on the pipeline statement but never made it into the "
        "spreadsheet. I have to go back through every day and rekey the actuals by hand before we "
        "can close the month.\n\nCan you check whether the settlement group has the same number?\n\n"
        "Darron",
        "giron-d", "volume_management",
    ),
    (
        "41209878.1075840501200", "Mon, 08 Oct 2001 14:48:02 -0700 (PDT)", "2001-10-08T21:48:02+00:00",
        "j..farmer@enron.com", "darron.giron@enron.com",
        "RE: Meter 9843 volume variance",
        "Darron,\n\nSettlements has 1,100 not 1,150. The difference is the 10/1 imbalance that was "
        "posted late. We still have to reconcile every meter one at a time each month and I do not "
        "think anyone has a list of which ones are done.\n\nDaren",
        "giron-d", "volume_management",
    ),
    (
        "41210433.1075840501877", "Fri, 02 Nov 2001 08:20:19 -0800 (PST)", "2001-11-02T16:20:19+00:00",
        "darron.giron@enron.com", "j..farmer@enron.com, mary.smith@enron.com",
        "October actuals - please review",
        "All,\n\nAttached are the October actuals. Meters 9843, 9851 and 6012 still do not tie to the "
        "pipeline statements. Please send me your corrections by Wednesday so we can get the "
        "invoices out. Last month this took until the 15th.\n\nDarron",
        "giron-d", "volume_management",
    ),
    (
        "55120988.1075840601123", "Tue, 16 Oct 2001 11:04:50 -0700 (PDT)", "2001-10-16T18:04:50+00:00",
        "bill.williams@enron.com", "cara.semperger@enron.com",
        "Deal 812334 correction",
        "Cara,\n\nDeal 812334 was entered with the wrong counterparty. It should be Powerex not PGE. "
        "Can you correct the ticket in EnPower and send me the confirmation once it is fixed? This "
        "is the third one this week so I want to make sure it is right before the invoice goes out.\n\n"
        "Bill",
        "williams-w3", "schedule",
    ),
    (
        "55121002.1075840601456", "Wed, 17 Oct 2001 08:41:12 -0700 (PDT)", "2001-10-17T15:41:12+00:00",
        "cara.semperger@enron.com", "bill.williams@enron.com",
        "RE: Deal 812334 correction",
        "Bill,\n\nFixed. The ticket now shows Powerex and the confirm has been resent. For what it is "
        "worth, the correction requests come in with different information every time, so I usually "
        "have to call to get the deal number or the delivery point.\n\nCara",
        "williams-w3", "schedule",
    ),
    (
        "55130077.1075840601901", "Thu, 29 Nov 2001 15:27:38 -0800 (PST)", "2001-11-29T23:27:38+00:00",
        "michelle.lokay@enron.com", "lorraine.lindberg@enron.com",
        "Deal ticket errors on Transwestern",
        "Lorraine,\n\nThree deal tickets from yesterday had the wrong volume. I am sending corrections "
        "one at a time but it would help if the traders used the same format when they ask for a "
        "change. Right now it is a phone call, a sticky note, or an email with no deal number.\n\n"
        "Michelle",
        "lokay-m", "tw_commercial_group",
    ),
    (
        "18820399.1075840433099", "Mon, 10 Dec 2001 06:55:21 -0800 (PST)", "2001-12-10T14:55:21+00:00",
        "lisa.kinsey@enron.com", "j..farmer@enron.com",
        "coverage while I am out",
        "Daren,\n\nI am out Thursday and Friday. Patti will cover the noms but she does not have the "
        "pipeline contact list or the login for the Transco site. Can you send those to her?\n\nLisa",
        "farmer-d", "logistics",
    ),
    (
        "41210500.1075840501999", "Mon, 03 Dec 2001 09:12:47 -0800 (PST)", "2001-12-03T17:12:47+00:00",
        "mary.smith@enron.com", "darron.giron@enron.com, j..farmer@enron.com",
        "November actualization",
        "Reminder that November actuals are due to settlements by the 7th. Please get your meters "
        "reconciled and send me the list of any that still do not tie.\n\nMary",
        "giron-d", "volume_management",
    ),
]

ARTIFACTS = {
    "o01": ("o01-nomination-confirmation-sop.md", "sop", """# SOP: Daily pipeline nomination confirmation log

Purpose: one place where every day's nominations and confirmations are recorded, so late or short confirmations are visible before 10:00 and nobody re-keys volumes twice.

Evidence: messages {m1}, {m2}.

## Every morning, by 9:00

1. Open the nomination sheet for the gas day.
2. Enter each nomination by pipeline and meter. **Do not** retype from yesterday.
3. When a confirmation arrives, mark it confirmed with the time and the confirmed volume.

## If a confirmation has not arrived by 9:30

- Call the pipeline scheduler. Use the contact list in the shared folder.
- Note the call and the reason in the sheet.
- If cut, record the cut volume next to the nomination.

## End of day

- Send the sheet to the group with the subject `Noms confirmed for <date>`.
- Anything still pending goes on the next morning's list first.
"""),
    "o02": ("o02-meter-variance-checklist.md", "checklist", """# Checklist: monthly meter reconciliation

Purpose: close the month without rekeying actuals by hand and without losing track of which meters are done.

Evidence: messages {m1}, {m2}.

## Before the 5th

- Pull the pipeline statements for every meter into one folder.
- Load actuals into the sheet from the statements, not from memory.
- Mark each meter `tied` or `variance` with the MMBtu difference.

## Variances

- Any variance over 500 MMBtu gets a line in the exception list with the meter, the month, and who owns it.
- Check settlements for the same meter before asking anyone else.
- Late imbalances get their posting date noted so the same question is not asked twice.

## Before the 7th

- Send the exception list to settlements.
- Send the tied list to the group so nobody rechecks a finished meter.
"""),
    "o03": ("o03-deal-correction-email.md", "email_template", """# Email template: deal ticket correction request

Purpose: every correction request arrives with the same five fields so the scheduler can fix it without a phone call.

Evidence: messages {m1}, {m2}.

## Subject

`Deal <deal number> correction: <field>`

## Body

Hi <name>,

Please correct deal <deal number>.

- Field: <counterparty | volume | price | delivery point | date>
- Currently shows: <current value>
- Should be: <correct value>
- Reason: <one line>
- Needed by: <date, before the invoice run>

Reply with the corrected confirm when it is done.

Thanks,
<your name>
"""),
}


def _message_id(raw: str) -> str:
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def _active_months(first_iso: str, last_iso: str) -> float:
    first = datetime.fromisoformat(first_iso)
    last = datetime.fromisoformat(last_iso)
    return round(max(1.0, (last - first).days / 30.44), 4)


def _norm_subject(subject: str) -> str:
    s = subject.strip().lower()
    while True:
        for prefix in ("re:", "fw:", "fwd:"):
            if s.startswith(prefix):
                s = s[len(prefix):].strip()
                break
        else:
            return " ".join(s.split())


def build_fixture(root: Path) -> dict:
    """Write data/ and run/artifacts/ under root. Returns the report dict."""
    data = root / "data"
    raw_dir = data / "raw"
    art_dir = root / "run" / "artifacts"
    raw_dir.mkdir(parents=True, exist_ok=True)
    art_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(data / "messages.db"))
    conn.execute(
        "CREATE TABLE messages (id TEXT PRIMARY KEY, path TEXT, mailbox TEXT, folder TEXT, "
        "header_message_id TEXT, date_iso TEXT, date_source TEXT, from_addr TEXT, to_addrs TEXT, "
        "cc_addrs TEXT, subject TEXT, subject_norm TEXT, body_raw TEXT, body_clean TEXT, "
        "thread_key TEXT, dup_of TEXT, char_len INTEGER)"
    )
    ids: list[str] = []
    bodies: dict[str, str] = {}
    metas: dict[str, dict] = {}
    for n, (hdr, rfc, iso, frm, to, subject, body, mailbox, folder) in enumerate(RAW_MESSAGES):
        raw = _raw(hdr, rfc, frm, to, subject, body, mailbox, folder)
        mid = _message_id(raw)
        ids.append(mid)
        bodies[mid] = body
        metas[mid] = {"from": frm, "date": iso, "subject": subject}
        (raw_dir / f"{mid}.txt").write_text(raw, encoding="utf-8")
        conn.execute(
            "INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                mid, f"{mailbox}/{folder}/{n + 1}.", mailbox, folder, f"<{hdr}.JavaMail.evans@thyme>",
                iso, "header", frm, json.dumps([a.strip() for a in to.split(",")]), "[]",
                subject, _norm_subject(subject), body, body,
                hashlib.sha1(_norm_subject(subject).encode()).hexdigest()[:12], None, len(body),
            ),
        )
    conn.commit()
    conn.close()

    def ev(index: int, quote: str) -> dict:
        mid = ids[index]
        assert quote in bodies[mid], f"fixture quote is not a substring: {quote!r}"
        return {"message_id": mid, "quote": quote, **metas[mid]}

    processes = [
        {
            "process_id": "p01",
            "name": "Daily gas pipeline nominations",
            "description": "Schedulers nominate daily volumes with each pipeline, wait for confirmations, and re-key confirmed volumes into the scheduling sheet.",
            "actors": ["j..farmer@enron.com", "victor.lamadrid@enron.com", "lisa.kinsey@enron.com"],
            "stall": "Confirmations arrive late and volumes are re-keyed from spreadsheets when the confirmed total differs.",
            "match_rule": {"subject_regex": "nomination|\\bnoms?\\b", "body_any": ["nominat", "confirm"], "from_any": []},
            "evidence": [
                ev(1, "The nomination for TETCO did not confirm until 9:40 this morning."),
                ev(2, "Transco is still pending, they said the scheduler is out and the backup does not have the spreadsheet."),
            ],
            "match_count": 612,
            "matched_message_ids": [ids[0], ids[1], ids[2], ids[3], ids[10]],
            "first_match": "2001-05-14T13:02:00+00:00",
            "last_match": "2002-04-30T21:40:12+00:00",
        },
        {
            "process_id": "p02",
            "name": "Monthly meter volume reconciliation",
            "description": "Volume managers compare nominated volumes to pipeline actuals meter by meter and correct the spreadsheet before settlements closes the month.",
            "actors": ["darron.giron@enron.com", "j..farmer@enron.com", "mary.smith@enron.com"],
            "stall": "Actuals are rekeyed by hand from pipeline statements and nobody holds a list of which meters are already reconciled.",
            "match_rule": {"subject_regex": "actual|variance|meter", "body_any": ["actuals", "variance", "reconcil"], "from_any": []},
            "evidence": [
                ev(4, "I have to go back through every day and rekey the actuals by hand before we can close the month."),
                ev(5, "We still have to reconcile every meter one at a time each month and I do not think anyone has a list of which ones are done."),
                ev(6, "Last month this took until the 15th."),
            ],
            "match_count": 388,
            "matched_message_ids": [ids[4], ids[5], ids[6], ids[11]],
            "first_match": "2001-08-01T15:11:09+00:00",
            "last_match": "2002-03-15T19:03:44+00:00",
        },
        {
            "process_id": "p03",
            "name": "Deal ticket corrections",
            "description": "Traders and schedulers request corrections to deal tickets with the wrong counterparty, volume, or delivery point before invoices go out.",
            "actors": ["bill.williams@enron.com", "cara.semperger@enron.com", "michelle.lokay@enron.com"],
            "stall": "Requests arrive in different formats and often without a deal number, so the scheduler has to call back for details.",
            "match_rule": {"subject_regex": "deal .*(correct|error|ticket)", "body_any": ["correct the ticket", "deal number", "wrong counterparty", "wrong volume"], "from_any": []},
            "evidence": [
                ev(8, "the correction requests come in with different information every time, so I usually have to call to get the deal number or the delivery point."),
                ev(9, "Right now it is a phone call, a sticky note, or an email with no deal number."),
            ],
            "match_count": 290,
            "matched_message_ids": [ids[7], ids[8], ids[9]],
            "first_match": "2001-09-10T14:20:31+00:00",
            "last_match": "2002-01-31T22:58:05+00:00",
        },
    ]

    for p in processes:
        p["active_months"] = _active_months(p["first_match"], p["last_match"])
        p["instances_per_month"] = round(p["match_count"] / p["active_months"], 4)
        p["instances_per_month_corpus_span"] = round(p["match_count"] / SPAN_MONTHS, 4)

    opp_specs = [
        ("o01", "p01", "Log nominations and confirmations in one sheet, flag late confirms", 30, "sop",
         "A shared nomination log per gas day where each pipeline's nomination, confirmation time, and confirmed volume are entered once. Anything unconfirmed by 9:30 is flagged and called. Ends the second re-keying when the confirmed total differs.",
         "Every nomination day produces the same three steps and the same failure. The log removes the re-key and makes late confirmations visible.",
         [ev(1, "I had to re-key the volumes from the spreadsheet into Unify again because the confirmation came back with a different meter total."),
          ev(2, "TETCO cut us 2,000 at Katy.")]),
        ("o02", "p02", "Monthly meter reconciliation checklist with an exception list", 45, "checklist",
         "A checklist that loads actuals from pipeline statements once, marks each meter tied or variance, and produces one exception list for settlements. Replaces rekeying and the question of which meters are done.",
         "The month closes late because reconciliation is untracked. A tied list and an exception list are cheap and remove both stalls.",
         [ev(4, "The actuals came in on the pipeline statement but never made it into the spreadsheet."),
          ev(6, "Meters 9843, 9851 and 6012 still do not tie to the pipeline statements.")]),
        ("o03", "p03", "Standard deal correction request email", 55, "email_template",
         "One email template for correction requests with the deal number, the field, the current value, the correct value, and the deadline. Schedulers stop calling back for details and corrections can be batched.",
         "Corrections are frequent and each one costs a call. A fixed format is the smallest change that removes the call.",
         [ev(7, "It should be Powerex not PGE."),
          ev(9, "it would help if the traders used the same format when they ask for a change.")]),
        ("o04", "p01", "Scheduler coverage pack for days out of the office", 5, "checklist",
         "A one-page coverage pack per scheduler with pipeline contacts, site logins held by the group, and the location of the nomination sheet, handed to the backup the day before.",
         "Coverage gaps are rare compared to daily nominations, so the saving is small, but the failure when it happens blocks a whole gas day.",
         [ev(10, "Patti will cover the noms but she does not have the pipeline contact list or the login for the Transco site."),
          ev(0, "Please forward this memo and ask your respective schedulers to respond by Friday.")]),
        ("o05", "p02", "Monthly actuals reminder with the tied and untied meter list", 8, "template",
         "A reminder sent on the 1st with the list of meters, who owns each, and which tied last month, so the request for corrections does not start from zero.",
         "The reminder already goes out; attaching the meter list costs nothing and shortens the chase.",
         [ev(11, "Please get your meters reconciled and send me the list of any that still do not tie.")]),
    ]

    opportunities = []
    for oid, pid, title, minutes, atype, automation, rationale, evidence in opp_specs:
        proc = next(p for p in processes if p["process_id"] == pid)
        inst = proc["match_count"] / proc["active_months"]
        hours = inst * minutes / 60
        dollars = hours * RATE
        inst_span = proc["match_count"] / SPAN_MONTHS
        hours_span = inst_span * minutes / 60
        dollars_span = hours_span * RATE
        artifact_path = None
        if oid in ARTIFACTS and dollars >= THRESHOLD:
            fname, _, text = ARTIFACTS[oid]
            e1, e2 = evidence[0]["message_id"], evidence[1]["message_id"]
            (art_dir / fname).write_text(text.format(m1=e1, m2=e2), encoding="utf-8")
            artifact_path = f"run/artifacts/{fname}"
        opportunities.append({
            "opportunity_id": oid, "process_id": pid, "title": title,
            "automation": automation, "minutes_saved_per_instance": minutes,
            "rationale": rationale, "evidence": evidence, "artifact_type": atype,
            "instances_per_month": round(inst, 4), "hours_per_month": round(hours, 4),
            "dollars_per_month": round(dollars, 2),
            "instances_per_month_corpus_span": round(inst_span, 4),
            "hours_per_month_corpus_span": round(hours_span, 4),
            "dollars_per_month_corpus_span": round(dollars_span, 2),
            "artifact_path": artifact_path,
        })
    opportunities.sort(key=lambda o: o["dollars_per_month"], reverse=True)

    report = {
        "generated_at": "2026-09-22T21:00:00+00:00",
        "corpus_hash": "fixture0000000000000000000000000000000000",
        "rate_per_hour": RATE,
        "artifact_threshold": THRESHOLD,
        "span_months": SPAN_MONTHS,
        "frequency_basis": "active_window",
        "frequency_note": "Headline rates use each process's active window, first match to last match. The conservative figure spreads the same matches over the full corpus span.",
        "totals": {
            "messages": 3240, "unique": 3011, "duplicates": 229, "undated": 14,
            "hours_per_month": round(sum(o["hours_per_month"] for o in opportunities), 4),
            "dollars_per_month": round(sum(o["dollars_per_month"] for o in opportunities), 2),
            "hours_per_month_corpus_span": round(sum(o["hours_per_month_corpus_span"] for o in opportunities), 4),
            "dollars_per_month_corpus_span": round(sum(o["dollars_per_month_corpus_span"] for o in opportunities), 2),
        },
        "processes": processes,
        "opportunities": opportunities,
    }
    (data / "report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    return report


# ---------------------------------------------------------------- fixtures


@pytest.fixture
def built(tmp_path: Path):
    report = build_fixture(tmp_path)
    stats = build.build(tmp_path / "data", tmp_path / "run", TEMPLATE_DIR)
    dash = tmp_path / "run" / "dashboard"
    data = json.loads((dash / "data.json").read_text(encoding="utf-8"))
    md = (tmp_path / "run" / "report.md").read_text(encoding="utf-8")
    return {"root": tmp_path, "report": report, "stats": stats, "dash": dash, "data": data, "md": md}


# ---------------------------------------------------------------- tests: build


def test_fixture_is_deterministic(tmp_path: Path):
    a = build_fixture(tmp_path / "a")
    b = build_fixture(tmp_path / "b")
    assert a == b
    assert len(a["processes"]) == 3
    assert len(a["opportunities"]) == 5
    above = [o for o in a["opportunities"] if o["dollars_per_month"] >= THRESHOLD]
    assert len(above) == 3 and all(o["artifact_path"] for o in above)


def test_build_writes_static_site(built):
    dash = built["dash"]
    for name in ("index.html", "app.js", "styles.css", "data.json"):
        assert (dash / name).is_file(), name
    assert (dash / "index.html").read_text(encoding="utf-8") == (TEMPLATE_DIR / "index.html").read_text(encoding="utf-8")
    assert (built["root"] / "run" / "report.md").is_file()


def test_every_referenced_message_is_copied(built):
    report = built["report"]
    ids = build.referenced_message_ids(report)
    expected = set()
    for section in ("processes", "opportunities"):
        for item in report[section]:
            expected.update(e["message_id"] for e in item["evidence"])
            expected.update(item.get("matched_message_ids") or [])
    assert set(ids) == expected
    for mid in ids:
        copied = built["dash"] / "messages" / f"{mid}.txt"
        assert copied.is_file(), mid
        assert copied.read_bytes() == (built["root"] / "data" / "raw" / f"{mid}.txt").read_bytes()
    assert built["stats"]["messages_copied"] == len(ids)
    assert built["stats"]["messages_missing_raw"] == []


def test_data_json_has_message_index_and_ranked_opportunities(built):
    data = built["data"]
    assert data["company"] == "Enron, four mailboxes"
    assert data["rate_per_hour"] == RATE
    assert data["artifact_threshold"] == THRESHOLD
    dollars = [o["dollars_per_month"] for o in data["opportunities"]]
    assert dollars == sorted(dollars, reverse=True)
    for mid in build.referenced_message_ids(built["report"]):
        entry = data["messages"][mid]
        assert entry["from"] and entry["date"] and entry["subject"] and entry["mailbox"]
        assert entry["raw_available"] is True


def test_artifacts_are_inlined(built):
    by_id = {o["opportunity_id"]: o for o in built["data"]["opportunities"]}
    for oid, (fname, _, _) in ARTIFACTS.items():
        text = by_id[oid]["artifact_markdown"]
        assert text is not None, oid
        assert text == (built["root"] / "run" / "artifacts" / fname).read_text(encoding="utf-8")
        ev_ids = [e["message_id"] for e in by_id[oid]["evidence"]]
        assert ev_ids[0] in text and ev_ids[1] in text
    assert by_id["o04"]["artifact_markdown"] is None
    assert by_id["o05"]["artifact_markdown"] is None


def test_artifact_fallback_by_opportunity_id(tmp_path: Path):
    report = build_fixture(tmp_path)
    # Drop artifact_path from o01; the file still exists as o01-*.md and must be found.
    for o in report["opportunities"]:
        if o["opportunity_id"] == "o01":
            o["artifact_path"] = None
    (tmp_path / "data" / "report.json").write_text(json.dumps(report), encoding="utf-8")
    build.build(tmp_path / "data", tmp_path / "run", TEMPLATE_DIR)
    data = json.loads((tmp_path / "run" / "dashboard" / "data.json").read_text(encoding="utf-8"))
    o01 = next(o for o in data["opportunities"] if o["opportunity_id"] == "o01")
    assert o01["artifact_markdown"] and o01["artifact_markdown"].startswith("# SOP")


def test_quotes_are_substrings_of_copied_raw_files(built):
    """The dashboard highlights by whitespace-tolerant substring match. Guarantee the
    fixture, and therefore the render path, actually exercises a found quote."""
    for section in ("processes", "opportunities"):
        for item in built["report"][section]:
            for e in item["evidence"]:
                raw = (built["dash"] / "messages" / f"{e['message_id']}.txt").read_text(encoding="utf-8")
                assert " ".join(e["quote"].split()) in " ".join(raw.split())


def test_report_md_contents(built):
    md = built["md"]
    report = built["report"]
    assert md.startswith("# Observation report, Enron, four mailboxes")
    assert "| Messages in corpus | 3,240 |" in md
    assert f"| Artifact threshold | ${THRESHOLD:,} per month |" in md
    assert "| Blended rate | $85 per hour |" in md
    # ranked table in dollar order with a running total column
    table_rows = [ln for ln in md.splitlines() if ln.startswith("| ") and "(o0" in ln]
    assert len(table_rows) == 5
    order = [ln.split("(o0")[1][0] for ln in table_rows]
    expected = [o["opportunity_id"][-1] for o in report["opportunities"]]
    assert order == expected
    running = 0.0
    for ln, o in zip(table_rows, report["opportunities"]):
        running += o["dollars_per_month"]
        assert f"${running:,.0f}" in ln
    # every evidence quote appears with its message id
    for section in ("processes", "opportunities"):
        for item in report[section]:
            for e in item["evidence"]:
                assert f"> {e['quote']}" in md
                assert f"`{e['message_id']}`" in md
    for p in report["processes"]:
        assert f"### {p['name']} ({p['process_id']})" in md
    assert "## Threshold" in md and "## Methodology" in md
    # both frequency bases, per opportunity and in totals
    assert "612 matched messages, 2001-05-14 to 2002-04-30 = 11.5 active months" in md
    assert "- 612 / 11.5 = 53.1 instances per month" in md
    for o in report["opportunities"]:
        assert f"{o['hours_per_month_corpus_span']:,.1f} hours, ${o['dollars_per_month_corpus_span']:,.0f} per month" in md
    t = report["totals"]
    assert f"| Dollars per month, all opportunities (active window) | ${t['dollars_per_month']:,.0f} |" in md
    assert f"| Dollars per month, over the full corpus span | ${t['dollars_per_month_corpus_span']:,.0f} |" in md
    assert report["frequency_note"] in md


def test_headline_exceeds_corpus_span_figures(built):
    """Active windows are shorter than the corpus span, so headline rates are higher."""
    for o in built["report"]["opportunities"]:
        assert o["dollars_per_month"] > o["dollars_per_month_corpus_span"]
    t = built["report"]["totals"]
    assert t["dollars_per_month"] > t["dollars_per_month_corpus_span"]
    assert built["data"]["frequency_basis"] == "active_window"
    assert built["data"]["frequency_note"]


def test_null_match_window_still_builds(tmp_path: Path):
    report = build_fixture(tmp_path)
    for p in report["processes"]:
        if p["process_id"] == "p03":
            p["first_match"] = None
            p["last_match"] = None
            p["active_months"] = 1.0
    (tmp_path / "data" / "report.json").write_text(json.dumps(report), encoding="utf-8")
    build.build(tmp_path / "data", tmp_path / "run", TEMPLATE_DIR)
    md = (tmp_path / "run" / "report.md").read_text(encoding="utf-8")
    assert "290 matched messages, no dated matches, window floored at 1 month = 1.0 active months" in md
    data = json.loads((tmp_path / "run" / "dashboard" / "data.json").read_text(encoding="utf-8"))
    p03 = next(p for p in data["processes"] if p["process_id"] == "p03")
    assert p03["first_match"] is None and p03["last_match"] is None


def test_missing_report_is_a_clear_error(tmp_path: Path, capsys):
    (tmp_path / "data").mkdir()
    rc = build.main(["--data", str(tmp_path / "data"), "--run", str(tmp_path / "run"), "--template", str(TEMPLATE_DIR)])
    assert rc == 1
    assert "report.json does not exist" in capsys.readouterr().err


def test_main_prints_summary(tmp_path: Path, capsys):
    build_fixture(tmp_path)
    rc = build.main(["--data", str(tmp_path / "data"), "--run", str(tmp_path / "run"), "--template", str(TEMPLATE_DIR)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "5 opportunities, 3 processes" in out
    assert "3 artifacts inlined" in out


def test_no_em_dashes_anywhere(built):
    files = [TEMPLATE_DIR / n for n in ("index.html", "app.js", "styles.css")]
    files += [ROOT / "pipeline" / "build.py", ROOT / "pipeline" / "serve.py", Path(__file__)]
    files += [built["dash"] / "data.json", built["root"] / "run" / "report.md"]
    em_dash = chr(0x2014)
    for f in files:
        assert em_dash not in f.read_text(encoding="utf-8"), f


# ---------------------------------------------------------------- tests: serve


def _get(url: str):
    with urllib.request.urlopen(url, timeout=5) as resp:
        return resp.status, resp.headers.get("Content-Type"), resp.read().decode("utf-8")


def test_serve_serves_index_data_and_messages(built):
    server = serve.make_server(built["dash"], 0)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{port}"
        status, ctype, body = _get(base + "/")
        assert status == 200 and ctype.startswith("text/html") and '<div id="app"' in body
        status, ctype, body = _get(base + "/data.json")
        assert status == 200 and ctype.startswith("application/json")
        assert json.loads(body)["company"] == "Enron, four mailboxes"
        status, ctype, _ = _get(base + "/app.js")
        assert status == 200 and ctype.startswith("text/javascript")
        status, ctype, _ = _get(base + "/styles.css")
        assert status == 200 and ctype.startswith("text/css")
        mid = build.referenced_message_ids(built["report"])[0]
        status, ctype, body = _get(base + f"/messages/{mid}.txt")
        assert status == 200 and ctype.startswith("text/plain")
        assert body.startswith("Message-ID:")
        with pytest.raises(urllib.error.HTTPError) as exc:
            _get(base + "/messages/doesnotexist.txt")
        assert exc.value.code == 404
    finally:
        server.shutdown()
        server.server_close()


def test_serve_missing_dashboard_is_a_clear_error(tmp_path: Path, capsys):
    rc = serve.main(["--dir", str(tmp_path / "nope"), "--port", "0"])
    assert rc == 1
    assert "pipeline.build" in capsys.readouterr().err


# ---------------------------------------------------------------- manual use


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--write":
        target = Path(sys.argv[2])
        build_fixture(target)
        print(f"fixture written under {target}/data and {target}/run/artifacts")
    else:
        print("usage: uv run python tests/test_build.py --write <dir>")
