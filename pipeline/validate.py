"""Stage 4. Citation validation. No model, no judgement, only substring checks.

Three modes:

- default: every ``data/extractions/*.json`` -> ``data/validated/<batch_id>.json`` in
  the same shape, plus ``rejects.json`` and ``summary.json``.
- ``--file <path>``: validate one extraction file, write its validated copy, and print
  ``pass=N fail=M`` on one line. Used by the PostToolUse hook.
- ``--synthesis``: validate ``data/synthesis.json`` in place. Failing evidence is
  dropped, processes and opportunities with no surviving evidence are dropped, rejects
  go to ``data/validated/synthesis_rejects.json``.

A quote passes when, whitespace-collapsed and case preserved, it is a substring of the
cited message's whitespace-collapsed body_clean or body_raw.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

from pipeline import cache
from pipeline.parse import collapse_ws, open_db

log = logging.getLogger("validate")

WS_RE = re.compile(r"\s+")


# ---------------------------------------------------------------------------
# Core check.
# ---------------------------------------------------------------------------


def load_bodies(db_path: Path) -> dict[str, tuple[str, str]]:
    """id -> (collapsed body_clean, collapsed body_raw). Canonical rows win on id clash."""
    con = open_db(db_path)
    try:
        rows = con.execute(
            "SELECT id, body_clean, body_raw FROM messages ORDER BY (dup_of IS NOT NULL), path"
        ).fetchall()
    finally:
        con.close()
    bodies: dict[str, tuple[str, str]] = {}
    for r in rows:
        if r["id"] not in bodies:
            bodies[r["id"]] = (collapse_ws(r["body_clean"]), collapse_ws(r["body_raw"]))
    return bodies


def check_quote(quote, message_id, bodies: dict[str, tuple[str, str]]) -> str | None:
    """None when the quote is good, otherwise the reason it fails."""
    if not isinstance(message_id, str) or not message_id:
        return "missing message_id"
    if not isinstance(quote, str):
        return "quote is not a string"
    q = collapse_ws(quote)
    if not q:
        return "empty quote"
    body = bodies.get(message_id)
    if body is None:
        return "unknown message_id"
    clean, raw = body
    if q in clean or q in raw:
        return None
    return "quote is not a substring of the message"


def validate_items(
    items: list[dict], bodies: dict[str, tuple[str, str]], context: dict | None = None
) -> tuple[list[dict], list[dict], int, int]:
    """Filter evidence on every item. Returns (kept items, rejects, passed, failed).

    An item with no surviving evidence is dropped. The reject entries carry the item's
    identifying fields so a person can find what was cut.
    """
    kept: list[dict] = []
    rejects: list[dict] = []
    passed = failed = 0
    for item in items:
        if not isinstance(item, dict):
            rejects.append({**(context or {}), "reason": "item is not an object", "item": item})
            failed += 1
            continue
        evidence = item.get("evidence")
        if not isinstance(evidence, list):
            evidence = []
        good = []
        label = _label(item)
        for ev in evidence:
            if not isinstance(ev, dict):
                failed += 1
                rejects.append({**(context or {}), **label, "reason": "evidence is not an object", "evidence": ev})
                continue
            reason = check_quote(ev.get("quote"), ev.get("message_id"), bodies)
            if reason is None:
                passed += 1
                good.append(ev)
            else:
                failed += 1
                rejects.append(
                    {
                        **(context or {}),
                        **label,
                        "message_id": ev.get("message_id"),
                        "quote": ev.get("quote"),
                        "reason": reason,
                    }
                )
        if good:
            kept.append(dict(item, evidence=good))
        else:
            rejects.append({**(context or {}), **label, "reason": "no surviving evidence, item dropped"})
    return kept, rejects, passed, failed


def _label(item: dict) -> dict:
    out = {}
    for key in ("process_id", "opportunity_id", "process", "title", "name"):
        if key in item:
            out[key] = item[key]
    return out


# ---------------------------------------------------------------------------
# Extraction files.
# ---------------------------------------------------------------------------


def validate_extraction(path: Path, bodies: dict[str, tuple[str, str]]) -> tuple[dict, list[dict], dict]:
    """One extraction file -> (validated document, rejects, counts)."""
    doc = cache.read_json(path)
    batch_id = path.stem
    if not isinstance(doc, dict):
        counts = {"batch_id": batch_id, "pass": 0, "fail": 0, "observations_in": 0, "observations_out": 0, "error": "not a JSON object"}
        return (
            {"batch_id": batch_id, "corpus_hash": None, "observations": []},
            [{"batch_id": batch_id, "reason": "file is not a JSON object"}],
            counts,
        )
    batch_id = doc.get("batch_id") or batch_id
    observations = doc.get("observations")
    if not isinstance(observations, list):
        observations = []
    kept, rejects, passed, failed = validate_items(observations, bodies, {"batch_id": batch_id})
    validated = {"batch_id": batch_id, "corpus_hash": doc.get("corpus_hash"), "observations": kept}
    counts = {
        "batch_id": batch_id,
        "pass": passed,
        "fail": failed,
        "observations_in": len(observations),
        "observations_out": len(kept),
    }
    return validated, rejects, counts


def run_extractions(data_dir: Path, force: bool = False) -> dict:
    data_dir = Path(data_dir)
    db_path = data_dir / "messages.db"
    extractions_dir = data_dir / "extractions"
    validated_dir = data_dir / "validated"
    files = sorted(extractions_dir.glob("*.json")) if extractions_dir.exists() else []
    summary_path = validated_dir / "summary.json"
    rejects_path = validated_dir / "rejects.json"

    input_hash = cache.hash_paths(files + [db_path], relative_to=data_dir)
    outputs = [summary_path, rejects_path] + [validated_dir / f.name for f in files]
    if not force and cache.is_done(data_dir, "validate", input_hash, outputs):
        log.info("validate: up to date, skipping")
        return cache.read_json(summary_path, {})

    bodies = load_bodies(db_path)
    validated_dir.mkdir(parents=True, exist_ok=True)
    for stale in validated_dir.glob("batch_*.json"):
        stale.unlink()
    all_rejects: list[dict] = []
    per_batch: list[dict] = []
    for path in files:
        validated, rejects, counts = validate_extraction(path, bodies)
        cache.write_json_atomic(validated_dir / path.name, validated)
        all_rejects.extend(rejects)
        per_batch.append(counts)
        log.info("validate: %s pass=%d fail=%d", counts["batch_id"], counts["pass"], counts["fail"])

    summary = {
        "files": len(files),
        "pass": sum(c["pass"] for c in per_batch),
        "fail": sum(c["fail"] for c in per_batch),
        "observations_in": sum(c["observations_in"] for c in per_batch),
        "observations_out": sum(c["observations_out"] for c in per_batch),
        "batches": per_batch,
    }
    cache.write_json_atomic(rejects_path, all_rejects)
    cache.write_json_atomic(summary_path, summary)
    cache.mark_done(data_dir, "validate", input_hash, outputs)
    return summary


def run_single_file(data_dir: Path, path: Path) -> dict:
    """Validate one extraction file and write its validated copy. Never cached."""
    data_dir = Path(data_dir)
    bodies = load_bodies(data_dir / "messages.db")
    validated, rejects, counts = validate_extraction(Path(path), bodies)
    validated_dir = data_dir / "validated"
    validated_dir.mkdir(parents=True, exist_ok=True)
    cache.write_json_atomic(validated_dir / Path(path).name, validated)
    counts["rejects"] = rejects
    return counts


# ---------------------------------------------------------------------------
# Synthesis.
# ---------------------------------------------------------------------------


def validate_synthesis(doc: dict, bodies: dict[str, tuple[str, str]]) -> tuple[dict, list[dict], dict]:
    """Filter evidence on processes and opportunities. Orphaned opportunities go too."""
    processes = doc.get("processes") if isinstance(doc.get("processes"), list) else []
    opportunities = doc.get("opportunities") if isinstance(doc.get("opportunities"), list) else []

    kept_p, rej_p, pass_p, fail_p = validate_items(processes, bodies, {"section": "processes"})
    kept_o, rej_o, pass_o, fail_o = validate_items(opportunities, bodies, {"section": "opportunities"})

    live_ids = {p.get("process_id") for p in kept_p}
    orphans = [o for o in kept_o if o.get("process_id") not in live_ids]
    kept_o = [o for o in kept_o if o.get("process_id") in live_ids]
    for o in orphans:
        rej_o.append(
            {
                "section": "opportunities",
                **_label(o),
                "reason": "process was dropped, opportunity dropped with it",
            }
        )

    out = dict(doc, processes=kept_p, opportunities=kept_o)
    counts = {
        "pass": pass_p + pass_o,
        "fail": fail_p + fail_o,
        "processes_in": len(processes),
        "processes_out": len(kept_p),
        "opportunities_in": len(opportunities),
        "opportunities_out": len(kept_o),
    }
    return out, rej_p + rej_o, counts


def run_synthesis(data_dir: Path) -> dict:
    data_dir = Path(data_dir)
    synth_path = data_dir / "synthesis.json"
    if not synth_path.exists():
        raise SystemExit("validate: data/synthesis.json missing")
    doc = cache.read_json(synth_path)
    if not isinstance(doc, dict):
        raise SystemExit("validate: data/synthesis.json is not a JSON object")

    bodies = load_bodies(data_dir / "messages.db")
    out, rejects, counts = validate_synthesis(doc, bodies)

    validated_dir = data_dir / "validated"
    validated_dir.mkdir(parents=True, exist_ok=True)
    if out != doc:
        # Keep the unvalidated version once so the cut can be audited.
        raw_backup = data_dir / "synthesis.unvalidated.json"
        if not raw_backup.exists():
            cache.write_json_atomic(raw_backup, doc)
        cache.write_json_atomic(synth_path, out)
    cache.write_json_atomic(validated_dir / "synthesis_rejects.json", rejects)
    cache.write_json_atomic(validated_dir / "synthesis_summary.json", counts)
    log.info(
        "validate --synthesis: pass=%d fail=%d processes %d->%d opportunities %d->%d",
        counts["pass"],
        counts["fail"],
        counts["processes_in"],
        counts["processes_out"],
        counts["opportunities_in"],
        counts["opportunities_out"],
    )
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate evidence quotes against messages.db")
    ap.add_argument("--data", type=Path, default=cache.DATA_DIR)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--synthesis", action="store_true", help="validate data/synthesis.json in place")
    ap.add_argument("--file", type=Path, help="validate one extraction file and print pass/fail")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)

    if args.file:
        counts = run_single_file(args.data, args.file)
        print(f"pass={counts['pass']} fail={counts['fail']}")
        return 0
    if args.synthesis:
        counts = run_synthesis(args.data)
        print(f"pass={counts['pass']} fail={counts['fail']}")
        return 0
    summary = run_extractions(args.data, force=args.force)
    print(f"pass={summary.get('pass', 0)} fail={summary.get('fail', 0)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
