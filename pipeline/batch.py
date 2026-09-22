"""Stage 2. data/messages.db -> data/batches/batch_NNN.json and data/batches/index.json.

Non-duplicate messages only, ordered by mailbox then date, greedily packed into batches
of at most BATCH_CAP characters. Size is measured as the characters of body_clean plus
the header fields that go into the batch entry. A single message over the cap has its
body truncated and is flagged ``truncated: true``.

The batch files are cached on the corpus hash. index.json is rewritten on every run
because its ``done`` flags depend on which extraction files exist right now.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from pipeline import cache
from pipeline.parse import open_db

log = logging.getLogger("batch")

BATCH_CAP = 110_000


def header_chars(entry: dict) -> int:
    return (
        len(entry["id"])
        + len(entry["date"] or "")
        + len(entry["from"])
        + sum(len(t) for t in entry["to"])
        + len(entry["subject"])
        + len(entry["mailbox"])
    )


def entry_chars(entry: dict) -> int:
    return header_chars(entry) + len(entry["body"])


def make_entry(row) -> dict:
    return {
        "id": row["id"],
        "date": row["date_iso"][:10] if row["date_iso"] else None,
        "from": row["from_addr"],
        "to": json.loads(row["to_addrs"]),
        "subject": row["subject"],
        "mailbox": row["mailbox"],
        "body": row["body_clean"],
        "truncated": False,
    }


def pack(entries: list[dict], cap: int = BATCH_CAP) -> list[list[dict]]:
    """Greedy first-fit in order. Oversized entries are truncated to fit alone."""
    batches: list[list[dict]] = []
    current: list[dict] = []
    current_chars = 0
    for entry in entries:
        size = entry_chars(entry)
        if size > cap:
            room = max(0, cap - header_chars(entry))
            entry = dict(entry, body=entry["body"][:room], truncated=True)
            size = entry_chars(entry)
        if current and current_chars + size > cap:
            batches.append(current)
            current, current_chars = [], 0
        current.append(entry)
        current_chars += size
    if current:
        batches.append(current)
    return batches


def load_entries(db_path: Path) -> tuple[list[dict], str]:
    con = open_db(db_path)
    try:
        chash = con.execute("SELECT value FROM meta WHERE key='corpus_hash'").fetchone()[0]
        rows = con.execute(
            "SELECT id, date_iso, from_addr, to_addrs, subject, mailbox, body_clean "
            "FROM messages WHERE dup_of IS NULL "
            "ORDER BY mailbox, (date_iso IS NULL), date_iso, path"
        ).fetchall()
    finally:
        con.close()
    return [make_entry(r) for r in rows], chash


def batch_id(n: int) -> str:
    return f"batch_{n:03d}"


def write_batches(batches: list[list[dict]], batches_dir: Path, chash: str) -> list[str]:
    batches_dir.mkdir(parents=True, exist_ok=True)
    for stale in batches_dir.glob("batch_*.json"):
        stale.unlink()
    ids = []
    for n, messages in enumerate(batches, start=1):
        bid = batch_id(n)
        cache.write_json_atomic(
            batches_dir / f"{bid}.json",
            {"batch_id": bid, "corpus_hash": chash, "messages": messages},
        )
        ids.append(bid)
    return ids


def build_index(batches_dir: Path, extractions_dir: Path, chash: str) -> dict:
    """index.json: every batch with its message count and a done flag."""
    entries = []
    for path in sorted(batches_dir.glob("batch_*.json")):
        batch = cache.read_json(path, {})
        bid = batch.get("batch_id", path.stem)
        extraction = cache.read_json(extractions_dir / f"{bid}.json")
        done = bool(extraction) and extraction.get("corpus_hash") == chash
        messages = batch.get("messages", [])
        entries.append(
            {
                "batch_id": bid,
                "messages": len(messages),
                "chars": sum(entry_chars(m) for m in messages),
                "truncated": sum(1 for m in messages if m.get("truncated")),
                "done": done,
            }
        )
    return {
        "corpus_hash": chash,
        "cap": BATCH_CAP,
        "batches": entries,
        "total": len(entries),
        "done": sum(1 for e in entries if e["done"]),
    }


def run(data_dir: Path, force: bool = False, cap: int = BATCH_CAP) -> dict:
    data_dir = Path(data_dir)
    db_path = data_dir / "messages.db"
    batches_dir = data_dir / "batches"
    extractions_dir = data_dir / "extractions"
    if not db_path.exists():
        raise SystemExit("batch: data/messages.db missing, run pipeline.parse first")

    entries, chash = load_entries(db_path)
    # Keyed on the database file, not the corpus hash, so a re-parse with changed
    # parser logic on the same corpus still repacks.
    input_hash = cache.sha1_text(f"{cache.sha1_file(db_path)}\n{cap}")
    existing = sorted(batches_dir.glob("batch_*.json")) if batches_dir.exists() else []
    if not force and existing and cache.is_done(data_dir, "batch", input_hash, existing):
        log.info("batch: up to date (%d batches), rewriting index only", len(existing))
    else:
        batches = pack(entries, cap=cap)
        ids = write_batches(batches, batches_dir, chash)
        cache.mark_done(
            data_dir, "batch", input_hash, [batches_dir / f"{b}.json" for b in ids]
        )
        log.info(
            "batch: wrote %d batches from %d messages (%d truncated)",
            len(ids),
            len(entries),
            sum(1 for b in batches for m in b if m["truncated"]),
        )

    index = build_index(batches_dir, extractions_dir, chash)
    cache.write_json_atomic(batches_dir / "index.json", index)
    return index


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Pack data/messages.db into batches")
    ap.add_argument("--data", type=Path, default=cache.DATA_DIR)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)
    index = run(args.data, force=args.force)
    print(
        json.dumps(
            {
                "batches": index["total"],
                "done": index["done"],
                "messages": sum(b["messages"] for b in index["batches"]),
                "truncated": sum(b["truncated"] for b in index["batches"]),
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
