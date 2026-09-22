"""Stage 8, build. report.json -> run/dashboard/ (static site) + run/report.md.

Reads:
    data/report.json          the Stage 6 output
    data/messages.db          for from, date, subject, mailbox on every referenced message
    data/raw/<id>.txt         raw message files, copied for drill-through
    run/artifacts/*.md        drafted artifacts, inlined into data.json
    dashboard/                the static template (index.html, app.js, styles.css)

Writes:
    run/dashboard/index.html, app.js, styles.css
    run/dashboard/data.json   report.json plus artifact text and a message index
    run/dashboard/messages/<id>.txt
    run/report.md

Usage:
    uv run python -m pipeline.build
    uv run python -m pipeline.build --data data --run run --template dashboard
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

RATE_FALLBACK = 85
THRESHOLD_FALLBACK = 1500
COMPANY = "Enron, four mailboxes"
TEMPLATE_FILES = ("index.html", "app.js", "styles.css")


# ---------------------------------------------------------------- loading


def load_report(data_dir: Path) -> dict:
    path = data_dir / "report.json"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} does not exist. Run `uv run python -m pipeline.compute` first."
        )
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def referenced_message_ids(report: dict) -> list[str]:
    """Every message id named anywhere in evidence or matched_message_ids, in
    first-seen order, deduplicated."""
    seen: dict[str, None] = {}

    def add(mid) -> None:
        if isinstance(mid, str) and mid and mid not in seen:
            seen[mid] = None

    for section in ("processes", "opportunities"):
        for item in report.get(section) or []:
            for ev in item.get("evidence") or []:
                add(ev.get("message_id"))
            for mid in item.get("matched_message_ids") or []:
                add(mid)
    return list(seen)


def load_message_index(data_dir: Path, ids: list[str]) -> dict[str, dict]:
    """Resolve from, date, subject, mailbox, folder for each id from messages.db.
    Ids not present in the db get an entry with null fields so the dashboard
    still links to the raw file if it exists."""
    index: dict[str, dict] = {
        mid: {"from": None, "date": None, "subject": None, "mailbox": None, "folder": None}
        for mid in ids
    }
    db_path = data_dir / "messages.db"
    if not db_path.exists() or not ids:
        return index
    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        chunk = 500
        for start in range(0, len(ids), chunk):
            part = ids[start : start + chunk]
            marks = ",".join("?" for _ in part)
            rows = conn.execute(
                f"SELECT id, from_addr, date_iso, subject, mailbox, folder "
                f"FROM messages WHERE id IN ({marks})",
                part,
            ).fetchall()
            for row in rows:
                index[row["id"]] = {
                    "from": row["from_addr"],
                    "date": row["date_iso"],
                    "subject": row["subject"],
                    "mailbox": row["mailbox"],
                    "folder": row["folder"],
                }
    finally:
        conn.close()
    return index


def load_artifacts(run_dir: Path, report: dict) -> dict[str, str]:
    """Map opportunity_id -> artifact markdown. Looks at artifact_path first,
    then falls back to run/artifacts/<opportunity_id>-*.md."""
    out: dict[str, str] = {}
    art_dir = run_dir / "artifacts"
    for opp in report.get("opportunities") or []:
        oid = opp.get("opportunity_id")
        text = None
        rel = opp.get("artifact_path")
        candidates: list[Path] = []
        if rel:
            p = Path(rel)
            candidates.append(p if p.is_absolute() else run_dir.parent / p)
            candidates.append(art_dir / p.name)
        if art_dir.is_dir() and oid:
            candidates.extend(sorted(art_dir.glob(f"{oid}-*.md")))
        for cand in candidates:
            if cand.is_file():
                text = cand.read_text(encoding="utf-8")
                break
        if text is not None and oid:
            out[oid] = text
    return out


# ---------------------------------------------------------------- helpers


def _num(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _rate(report: dict) -> float:
    return _num(report.get("rate_per_hour"), RATE_FALLBACK)


def _threshold(report: dict) -> float:
    for key in ("artifact_threshold", "threshold_dollars_per_month", "threshold"):
        if key in report:
            return _num(report[key], THRESHOLD_FALLBACK)
    return float(THRESHOLD_FALLBACK)


def _ranked_opportunities(report: dict) -> list[dict]:
    opps = list(report.get("opportunities") or [])
    opps.sort(key=lambda o: _num(o.get("dollars_per_month")), reverse=True)
    return opps


def _process_by_id(report: dict) -> dict[str, dict]:
    return {p.get("process_id"): p for p in report.get("processes") or [] if p.get("process_id")}


def _fmt_money(value) -> str:
    return f"${_num(value):,.0f}"


def _fmt_num(value, places=1) -> str:
    return f"{_num(value):,.{places}f}"


def _cell(text) -> str:
    return str(text if text is not None else "").replace("|", "\\|").replace("\n", " ")


def _rule_text(rule: dict | None) -> str:
    if not rule:
        return "no rule"
    parts = []
    if rule.get("subject_regex"):
        parts.append(f"subject matches /{rule['subject_regex']}/")
    if rule.get("body_any"):
        parts.append("body contains any of " + ", ".join(f'"{k}"' for k in rule["body_any"]))
    if rule.get("from_any"):
        parts.append("from any of " + ", ".join(rule["from_any"]))
    return "; ".join(parts) if parts else "empty rule, matches nothing"


# ---------------------------------------------------------------- report.md


def render_report_md(report: dict, artifacts: dict[str, str], msg_index: dict[str, dict]) -> str:
    rate = _rate(report)
    threshold = _threshold(report)
    totals = report.get("totals") or {}
    span = _num(report.get("span_months"), 1)
    opps = _ranked_opportunities(report)
    procs = _process_by_id(report)
    lines: list[str] = []
    w = lines.append

    w(f"# Observation report, {COMPANY}")
    w("")
    w(f"Generated {report.get('generated_at', 'unknown')}. Corpus hash "
      f"`{report.get('corpus_hash', 'unknown')}`.")
    w("")
    w("## Totals")
    w("")
    w("| Measure | Value |")
    w("|---|---|")
    w(f"| Messages in corpus | {int(_num(totals.get('messages'))):,} |")
    w(f"| Unique messages | {int(_num(totals.get('unique'))):,} |")
    w(f"| Duplicates removed | {int(_num(totals.get('duplicates'))):,} |")
    w(f"| Undated messages | {int(_num(totals.get('undated'))):,} |")
    w(f"| Corpus span | {_fmt_num(span)} months |")
    w(f"| Blended rate | {_fmt_money(rate)} per hour |")
    w(f"| Hours per month, all opportunities | {_fmt_num(totals.get('hours_per_month'))} |")
    w(f"| Dollars per month, all opportunities | {_fmt_money(totals.get('dollars_per_month'))} |")
    w(f"| Artifact threshold | {_fmt_money(threshold)} per month |")
    w("")

    w("## Ranked opportunities")
    w("")
    w("| Rank | Opportunity | Process | Instances / month | Hours / month | Dollars / month | Running total | Artifact |")
    w("|---|---|---|---|---|---|---|---|")
    running = 0.0
    for rank, opp in enumerate(opps, start=1):
        dollars = _num(opp.get("dollars_per_month"))
        running += dollars
        proc = procs.get(opp.get("process_id")) or {}
        has_artifact = "yes" if opp.get("opportunity_id") in artifacts else "no"
        w(
            f"| {rank} | {_cell(opp.get('title'))} ({opp.get('opportunity_id')}) "
            f"| {_cell(proc.get('name') or opp.get('process_id'))} "
            f"| {_fmt_num(opp.get('instances_per_month'))} "
            f"| {_fmt_num(opp.get('hours_per_month'))} "
            f"| {_fmt_money(dollars)} | {_fmt_money(running)} | {has_artifact} |"
        )
    w("")

    for rank, opp in enumerate(opps, start=1):
        oid = opp.get("opportunity_id")
        proc = procs.get(opp.get("process_id")) or {}
        matches = _num(proc.get("match_count"))
        minutes = _num(opp.get("minutes_saved_per_instance"))
        w(f"## {rank}. {opp.get('title')} ({oid})")
        w("")
        w(f"Process: {proc.get('name') or opp.get('process_id')} ({opp.get('process_id')})")
        w("")
        if opp.get("automation"):
            w(str(opp["automation"]))
            w("")
        if opp.get("rationale"):
            w(f"Rationale. {opp['rationale']}")
            w("")
        w("The math.")
        w("")
        w(f"- {int(matches):,} matched messages / {_fmt_num(span)} months = "
          f"{_fmt_num(opp.get('instances_per_month'))} instances per month")
        w(f"- {_fmt_num(opp.get('instances_per_month'))} instances x {_fmt_num(minutes, 0)} minutes / 60 = "
          f"{_fmt_num(opp.get('hours_per_month'))} hours per month")
        w(f"- {_fmt_num(opp.get('hours_per_month'))} hours x {_fmt_money(rate)} = "
          f"{_fmt_money(opp.get('dollars_per_month'))} per month")
        w(f"- Match rule: {_rule_text(proc.get('match_rule'))}")
        w("")
        evidence = opp.get("evidence") or []
        if evidence:
            w("Evidence.")
            w("")
            for ev in evidence:
                mid = ev.get("message_id")
                meta = msg_index.get(mid) or {}
                who = ev.get("from") or meta.get("from") or "unknown sender"
                when = ev.get("date") or meta.get("date") or "undated"
                subj = ev.get("subject") or meta.get("subject") or "no subject"
                w(f"> {ev.get('quote', '')}")
                w(f">")
                w(f"> {who}, {when}, {_cell(subj)}. Message `{mid}`.")
                w("")
        if oid in artifacts:
            w(f"Artifact: `run/artifacts/{Path(opp.get('artifact_path') or '').name or oid}` "
              f"(rendered on the dashboard).")
        else:
            w(f"No artifact. Below the {_fmt_money(threshold)} per month threshold "
              "or none was drafted.")
        w("")

    w("## Processes")
    w("")
    for proc in report.get("processes") or []:
        w(f"### {proc.get('name')} ({proc.get('process_id')})")
        w("")
        if proc.get("description"):
            w(str(proc["description"]))
            w("")
        if proc.get("actors"):
            w("Actors: " + ", ".join(proc["actors"]))
            w("")
        if proc.get("stall"):
            w(f"Where it stalls. {proc['stall']}")
            w("")
        w(f"Matched {int(_num(proc.get('match_count'))):,} messages, "
          f"{_fmt_num(proc.get('instances_per_month'))} per month. "
          f"Rule: {_rule_text(proc.get('match_rule'))}")
        w("")
        for ev in proc.get("evidence") or []:
            mid = ev.get("message_id")
            meta = msg_index.get(mid) or {}
            who = ev.get("from") or meta.get("from") or "unknown sender"
            when = ev.get("date") or meta.get("date") or "undated"
            w(f"> {ev.get('quote', '')}")
            w(">")
            w(f"> {who}, {when}. Message `{mid}`.")
            w("")

    w("## Threshold")
    w("")
    w(f"An artifact (SOP, email template, checklist, or template) is drafted for every "
      f"opportunity at or above {_fmt_money(threshold)} per month. Below that, the "
      "attention cost of adopting a new document exceeds what it saves in the first quarter.")
    w("")
    w("## Methodology")
    w("")
    w(
        "Every message in the corpus was parsed, deduplicated, and dated by deterministic "
        "code. A model read the corpus in batches and proposed recurring processes, each "
        "with verbatim quotes as evidence. Every quote was checked as an exact substring "
        "of the message it cites, and quotes that failed were dropped rather than repaired. "
        "For each process the model proposed a deterministic match rule (a subject regex, "
        "body keywords, sender list) and code counted the non-duplicate messages that match "
        f"it over the {_fmt_num(span)} month corpus span. Instances per month is that count "
        "divided by the span. Hours per month is instances times the model's minutes saved "
        f"per instance, divided by 60. Dollars per month is hours times the {_fmt_money(rate)} "
        "blended rate. The minutes per instance figure is a judgment with no ground truth in "
        "an email archive, so everything downstream of it is arithmetic on an estimate. "
        "The matched message list for every process is on the dashboard so over-matching "
        "can be seen directly."
    )
    w("")
    return "\n".join(lines)


# ---------------------------------------------------------------- build


def build(data_dir: Path, run_dir: Path, template_dir: Path) -> dict:
    report = load_report(data_dir)
    ids = referenced_message_ids(report)
    msg_index = load_message_index(data_dir, ids)
    artifacts = load_artifacts(run_dir, report)

    dash = run_dir / "dashboard"
    msg_out = dash / "messages"
    dash.mkdir(parents=True, exist_ok=True)
    msg_out.mkdir(parents=True, exist_ok=True)

    missing_template = [f for f in TEMPLATE_FILES if not (template_dir / f).is_file()]
    if missing_template:
        raise FileNotFoundError(
            f"Template files missing from {template_dir}: {', '.join(missing_template)}"
        )
    for name in TEMPLATE_FILES:
        shutil.copyfile(template_dir / name, dash / name)

    raw_dir = data_dir / "raw"
    copied = 0
    missing_raw: list[str] = []
    for mid in ids:
        src = raw_dir / f"{mid}.txt"
        if src.is_file():
            shutil.copyfile(src, msg_out / f"{mid}.txt")
            copied += 1
        else:
            missing_raw.append(mid)

    data = dict(report)
    data["company"] = COMPANY
    data["rate_per_hour"] = _rate(report)
    data["artifact_threshold"] = _threshold(report)
    data["built_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    data["opportunities"] = [
        {**opp, "artifact_markdown": artifacts.get(opp.get("opportunity_id"))}
        for opp in _ranked_opportunities(report)
    ]
    data["messages"] = {
        mid: {**meta, "raw_available": mid not in missing_raw} for mid, meta in msg_index.items()
    }
    (dash / "data.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    (run_dir / "report.md").write_text(
        render_report_md(report, artifacts, msg_index), encoding="utf-8"
    )

    return {
        "opportunities": len(data["opportunities"]),
        "processes": len(report.get("processes") or []),
        "messages_referenced": len(ids),
        "messages_copied": copied,
        "messages_missing_raw": missing_raw,
        "artifacts_inlined": len(artifacts),
        "dashboard": str(dash),
        "report_md": str(run_dir / "report.md"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build run/dashboard and run/report.md")
    parser.add_argument("--data", default="data", help="data directory (default: data)")
    parser.add_argument("--run", default="run", help="run directory (default: run)")
    parser.add_argument("--template", default="dashboard", help="template directory")
    args = parser.parse_args(argv)
    try:
        stats = build(Path(args.data), Path(args.run), Path(args.template))
    except FileNotFoundError as exc:
        print(f"build: {exc}", file=sys.stderr)
        return 1
    print(
        f"build: {stats['opportunities']} opportunities, {stats['processes']} processes, "
        f"{stats['messages_copied']}/{stats['messages_referenced']} referenced messages copied, "
        f"{stats['artifacts_inlined']} artifacts inlined"
    )
    if stats["messages_missing_raw"]:
        print(
            f"build: warning, {len(stats['messages_missing_raw'])} referenced ids have no "
            f"raw file: {', '.join(stats['messages_missing_raw'][:10])}",
            file=sys.stderr,
        )
    print(f"build: wrote {stats['dashboard']} and {stats['report_md']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
