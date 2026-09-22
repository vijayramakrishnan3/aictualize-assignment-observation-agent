"""Stage 6. data/synthesis.json + data/messages.db -> data/report.json.

Code counts, the model never does. For each process the synthesizer's ``match_rule``
is applied to every non-duplicate message and the matches are counted. The rule's
three parts are ANDed: every non-empty part must hold, an empty part is no constraint,
and a rule with all three empty matches nothing. That last clause is why AND is the
reading: under OR an all-empty rule would match nothing anyway and the spec would not
need to say so.

    instances_per_month = matches / span_months
    hours_per_month     = instances_per_month * minutes_saved_per_instance / 60
    dollars_per_month   = hours_per_month * RATE

Extra process fields the synthesizer may send, ``minutes_per_instance`` and
``expected_matches``, are copied through. ``expected_matches_missed`` lists the
expected ids the rule did not hit, which is the cheapest test of an over-narrow rule.
An opportunity's ``minutes_saved_per_instance`` is capped at its process's
``minutes_per_instance`` when that is present.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from pipeline import cache
from pipeline.parse import open_db

log = logging.getLogger("compute")

ARTIFACT_THRESHOLD = 1500
RATE = 85
DAYS_PER_MONTH = 30.44
MAX_MATCHED_IDS = 200


# ---------------------------------------------------------------------------
# Matching.
# ---------------------------------------------------------------------------


def compile_rule(rule: dict | None) -> dict:
    """Normalize a match_rule into something cheap to apply. Never raises."""
    rule = rule if isinstance(rule, dict) else {}
    subject_regex = rule.get("subject_regex") or ""
    body_any = [str(k).lower() for k in (rule.get("body_any") or []) if str(k).strip()]
    from_any = [str(a).lower().strip() for a in (rule.get("from_any") or []) if str(a).strip()]
    compiled = None
    error = None
    if isinstance(subject_regex, str) and subject_regex.strip():
        try:
            compiled = re.compile(subject_regex, re.IGNORECASE)
        except re.error as exc:
            error = f"invalid subject_regex: {exc}"
    elif subject_regex and not isinstance(subject_regex, str):
        error = "subject_regex is not a string"
    return {
        "subject_regex": subject_regex if isinstance(subject_regex, str) else "",
        "compiled": compiled,
        "body_any": body_any,
        "from_any": from_any,
        "error": error,
        "empty": compiled is None and not body_any and not from_any,
    }


def message_matches(rule: dict, subject_norm: str, body_lower: str, from_addr: str) -> bool:
    if rule["empty"] or rule["error"]:
        return False
    if rule["compiled"] is not None and not rule["compiled"].search(subject_norm or ""):
        return False
    if rule["body_any"] and not any(k in body_lower for k in rule["body_any"]):
        return False
    if rule["from_any"] and (from_addr or "") not in rule["from_any"]:
        return False
    return True


def count_matches(rule: dict, messages: list[dict]) -> list[str]:
    """Ids of matching messages, in the order given (date, then path)."""
    return [
        m["id"]
        for m in messages
        if message_matches(rule, m["subject_norm"], m["body_lower"], m["from_addr"])
    ]


# ---------------------------------------------------------------------------
# Arithmetic.
# ---------------------------------------------------------------------------


def span_months(dates: list[str]) -> float:
    """(max date minus min date) / 30.44, floored at 1. Dates are ISO strings."""
    dated = [d for d in dates if d]
    if not dated:
        return 1.0
    lo = datetime.fromisoformat(min(dated).replace("Z", "+00:00"))
    hi = datetime.fromisoformat(max(dated).replace("Z", "+00:00"))
    days = (hi - lo).total_seconds() / 86400.0
    return max(1.0, days / DAYS_PER_MONTH)


def as_number(value, default=0.0) -> float:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return default
    if n != n or n < 0:
        return default
    return n


def money(matches: int, span: float, minutes: float, rate: float = RATE) -> dict:
    ipm = matches / span if span else 0.0
    hours = ipm * minutes / 60.0
    return {
        "instances_per_month": round(ipm, 2),
        "hours_per_month": round(hours, 2),
        "dollars_per_month": round(hours * rate, 2),
    }


def slugify(text: str, limit: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:limit].rstrip("-") or "opportunity"


# ---------------------------------------------------------------------------
# Report.
# ---------------------------------------------------------------------------


def load_messages(db_path: Path) -> tuple[list[dict], dict, dict[str, dict]]:
    """Non-duplicate messages for matching, totals, and an id -> header lookup."""
    con = open_db(db_path)
    try:
        rows = con.execute(
            "SELECT id, path, subject, subject_norm, body_clean, from_addr, date_iso, dup_of "
            "FROM messages ORDER BY (date_iso IS NULL), date_iso, path"
        ).fetchall()
        chash_row = con.execute("SELECT value FROM meta WHERE key='corpus_hash'").fetchone()
    finally:
        con.close()
    messages = []
    lookup: dict[str, dict] = {}
    total = dups = undated = 0
    for r in rows:
        total += 1
        header = {
            "id": r["id"],
            "path": r["path"],
            "from": r["from_addr"],
            "date": r["date_iso"][:10] if r["date_iso"] else None,
            "subject": r["subject"],
        }
        if r["id"] not in lookup or r["dup_of"] is None:
            lookup[r["id"]] = header
        if r["dup_of"]:
            dups += 1
            continue
        if not r["date_iso"]:
            undated += 1
        messages.append(
            {
                "id": r["id"],
                "subject_norm": r["subject_norm"],
                "body_lower": r["body_clean"].lower(),
                "from_addr": r["from_addr"],
                "date_iso": r["date_iso"],
            }
        )
    totals = {
        "messages": total,
        "unique": total - dups,
        "duplicates": dups,
        "undated": undated,
        "corpus_hash": chash_row[0] if chash_row else None,
    }
    return messages, totals, lookup


def resolve_evidence(evidence: list, lookup: dict[str, dict]) -> list[dict]:
    out = []
    for ev in evidence or []:
        if not isinstance(ev, dict):
            continue
        header = lookup.get(ev.get("message_id"), {})
        out.append(
            {
                "message_id": ev.get("message_id"),
                "quote": ev.get("quote"),
                "from": header.get("from"),
                "date": header.get("date"),
                "subject": header.get("subject"),
                "path": header.get("path"),
            }
        )
    return out


def build_report(
    synthesis: dict,
    messages: list[dict],
    totals: dict,
    lookup: dict[str, dict],
    now: datetime | None = None,
    artifacts_dir: Path | None = None,
) -> dict:
    span = span_months([m["date_iso"] for m in messages])
    span_rounded = round(span, 2)
    processes_in = synthesis.get("processes") if isinstance(synthesis.get("processes"), list) else []
    opportunities_in = (
        synthesis.get("opportunities") if isinstance(synthesis.get("opportunities"), list) else []
    )

    processes: list[dict] = []
    by_id: dict[str, dict] = {}
    for p in processes_in:
        if not isinstance(p, dict):
            continue
        rule = compile_rule(p.get("match_rule"))
        matched = count_matches(rule, messages)
        expected = [e for e in (p.get("expected_matches") or []) if isinstance(e, str)]
        matched_set = set(matched)
        minutes = p.get("minutes_per_instance")
        entry = {
            **p,
            "match_rule": {
                "subject_regex": rule["subject_regex"],
                "body_any": rule["body_any"],
                "from_any": rule["from_any"],
            },
            "match_rule_error": rule["error"],
            "match_count": len(matched),
            "matched_message_ids": matched[:MAX_MATCHED_IDS],
            "instances_per_month": round(len(matched) / span, 2),
            "minutes_per_instance": as_number(minutes) if minutes is not None else None,
            "expected_matches": expected,
            "expected_matches_missed": [e for e in expected if e not in matched_set],
            "evidence": resolve_evidence(p.get("evidence"), lookup),
        }
        processes.append(entry)
        if isinstance(p.get("process_id"), str):
            by_id[p["process_id"]] = entry

    opportunities: list[dict] = []
    for o in opportunities_in:
        if not isinstance(o, dict):
            continue
        proc = by_id.get(o.get("process_id"))
        matches = proc["match_count"] if proc else 0
        minutes = as_number(o.get("minutes_saved_per_instance"))
        cap = proc.get("minutes_per_instance") if proc else None
        capped = False
        if cap is not None and minutes > cap:
            minutes, capped = cap, True
        figures = money(matches, span, minutes)
        artifact_type = o.get("artifact_type") or "none"
        above = figures["dollars_per_month"] >= ARTIFACT_THRESHOLD and artifact_type != "none"
        oid = o.get("opportunity_id") or slugify(o.get("title", ""))
        artifact_rel = f"run/artifacts/{oid}-{slugify(o.get('title', ''))}.md" if above else None
        artifact_exists = bool(
            artifact_rel and artifacts_dir and (artifacts_dir / Path(artifact_rel).name).exists()
        )
        opportunities.append(
            {
                **o,
                "opportunity_id": oid,
                "artifact_type": artifact_type,
                "threshold": ARTIFACT_THRESHOLD,
                "minutes_saved_per_instance": minutes,
                "minutes_capped_to_process": capped,
                "match_count": matches,
                "span_months": span_rounded,
                "rate_per_hour": RATE,
                **figures,
                "above_threshold": above,
                "artifact_path": artifact_rel,
                "artifact_exists": artifact_exists,
                "evidence": resolve_evidence(o.get("evidence"), lookup),
            }
        )
    opportunities.sort(key=lambda o: (-o["dollars_per_month"], o["opportunity_id"]))
    for rank, o in enumerate(opportunities, start=1):
        o["rank"] = rank

    now = now or datetime.now(timezone.utc)
    return {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "corpus_hash": totals.get("corpus_hash"),
        "rate_per_hour": RATE,
        "artifact_threshold": ARTIFACT_THRESHOLD,
        "span_months": span_rounded,
        "totals": {
            "messages": totals["messages"],
            "unique": totals["unique"],
            "duplicates": totals["duplicates"],
            "undated": totals["undated"],
            "processes": len(processes),
            "opportunities": len(opportunities),
            "above_threshold": sum(1 for o in opportunities if o["above_threshold"]),
            "hours_per_month": round(sum(o["hours_per_month"] for o in opportunities), 2),
            "dollars_per_month": round(sum(o["dollars_per_month"] for o in opportunities), 2),
        },
        "processes": processes,
        "opportunities": opportunities,
    }


def run(data_dir: Path, force: bool = False, run_dir: Path | None = None) -> dict:
    data_dir = Path(data_dir)
    db_path = data_dir / "messages.db"
    synth_path = data_dir / "synthesis.json"
    report_path = data_dir / "report.json"
    if not db_path.exists():
        raise SystemExit("compute: data/messages.db missing, run pipeline.parse first")
    if not synth_path.exists():
        raise SystemExit("compute: data/synthesis.json missing, run the synthesizer first")

    input_hash = cache.sha1_text(
        cache.hash_paths([db_path, synth_path], relative_to=data_dir)
        + f"\n{ARTIFACT_THRESHOLD}\n{RATE}"
    )
    if not force and cache.is_done(data_dir, "compute", input_hash, [report_path]):
        log.info("compute: up to date, skipping")
        return cache.read_json(report_path, {})

    synthesis = cache.read_json(synth_path)
    if not isinstance(synthesis, dict):
        raise SystemExit("compute: data/synthesis.json is not a JSON object")
    messages, totals, lookup = load_messages(db_path)
    artifacts_dir = (run_dir or cache.RUN_DIR) / "artifacts"
    report = build_report(synthesis, messages, totals, lookup, artifacts_dir=artifacts_dir)
    cache.write_json_atomic(report_path, report)
    cache.mark_done(data_dir, "compute", input_hash, [report_path])
    log.info(
        "compute: %d processes, %d opportunities, %d above $%d, $%.2f/month total, span %.2f months",
        len(report["processes"]),
        len(report["opportunities"]),
        report["totals"]["above_threshold"],
        ARTIFACT_THRESHOLD,
        report["totals"]["dollars_per_month"],
        report["span_months"],
    )
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Count match rules and compute the money")
    ap.add_argument("--data", type=Path, default=cache.DATA_DIR)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)
    report = run(args.data, force=args.force)
    print(
        json.dumps(
            {
                "artifact_threshold": ARTIFACT_THRESHOLD,
                "rate_per_hour": RATE,
                "span_months": report.get("span_months"),
                "totals": report.get("totals"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
