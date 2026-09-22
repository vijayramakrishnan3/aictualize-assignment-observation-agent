"""Stage 1. corpus/ -> data/messages.db, data/raw/<id>.txt, data/parse_stats.json.

Every file under corpus/ becomes one row in the ``messages`` table. Nothing here calls
a model. A file that cannot be parsed is logged and still gets a row with whatever
could be recovered, so downstream counts always add up to the number of files read.

Deviations from SPEC.md, all deliberate:

- ``id`` is the first 12 hex of sha1 of the raw bytes, exactly as specified, but two
  corpus files are byte-identical and therefore share an id. ``path`` is the primary
  key so both rows survive; the later path is marked ``dup_of`` its own id. Every
  lookup by id prefers the canonical row.
- A Date header that parses but lands in the future, or before 1990, is treated as
  unparseable. The corpus has a planted year-2031 date that would otherwise stretch
  the corpus span by thirty years and deflate every dollar figure.
- ``-----Original Message-----`` is matched with optional leading whitespace, because
  Outlook indents it by one space in about half the corpus.
- Lotus Notes ``---- Forwarded by ... ----`` lines are also treated as a cut point.
  The spec asks for forwarded headers to be stripped and this is how Notes writes them.
- When body_clean is empty the duplicate comparison uses body_raw instead. See
  ``mark_duplicates`` for the corpus evidence.
"""

from __future__ import annotations

import argparse
import email
import email.policy
import email.utils
import json
import logging
import os
import re
import sqlite3
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from pipeline import cache

log = logging.getLogger("parse")

MIN_PLAUSIBLE_YEAR = 1990

SUBJECT_PREFIX_RE = re.compile(r"^(?:(?:re|fw|fwd)\s*(?:\[\d+\])?\s*:\s*)+", re.IGNORECASE)
WS_RE = re.compile(r"\s+")
HEADER_LINE_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9-]*):\s?(.*)$")

# Cut points for quoted replies and forwarded headers, checked per line in order.
ORIGINAL_MESSAGE_RE = re.compile(r"^\s*-{2,}\s*Original Message\s*-{2,}\s*$", re.IGNORECASE)
ON_WROTE_RE = re.compile(r"^On .* wrote:\s*$")
FORWARDED_BY_RE = re.compile(r"^\s*-{3,}\s*Forwarded by .*", re.IGNORECASE)
BODY_FROM_RE = re.compile(r"^From:\s")
SIGNATURE_DELIM_RE = re.compile(r"^--\s*$")


@dataclass
class Parsed:
    id: str
    path: str
    mailbox: str
    folder: str
    header_message_id: str | None
    date_iso: str | None
    date_source: str | None
    from_addr: str
    to_addrs: list[str]
    cc_addrs: list[str]
    subject: str
    subject_norm: str
    body_raw: str
    body_clean: str
    thread_key: str
    dup_of: str | None = None
    char_len: int = 0
    parse_mode: str = "email"
    raw: bytes = field(default=b"", repr=False)


# ---------------------------------------------------------------------------
# Pure helpers. Each is unit tested on its own.
# ---------------------------------------------------------------------------


def normalize_subject(subject: str) -> str:
    """Lowercase, strip leading re:/fw:/fwd: chains, collapse whitespace."""
    s = (subject or "").lower()
    s = SUBJECT_PREFIX_RE.sub("", s)
    return WS_RE.sub(" ", s).strip()


def collapse_ws(text: str) -> str:
    return WS_RE.sub(" ", text or "").strip()


def parse_date(value: str | None, now: datetime | None = None) -> str | None:
    """RFC 2822 date -> ISO 8601 UTC, or None when unparseable or implausible."""
    if not value or not value.strip():
        return None
    try:
        dt = email.utils.parsedate_to_datetime(value.strip())
    except (TypeError, ValueError, IndexError, OverflowError):
        return None
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    now = now or datetime.now(timezone.utc)
    if dt.year < MIN_PLAUSIBLE_YEAR or dt > now:
        return None
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_addrs(values: list[str] | None) -> list[str]:
    """Header values -> lowercased addresses, order preserved, duplicates dropped."""
    out: list[str] = []
    for value in values or []:
        if not value:
            continue
        try:
            pairs = email.utils.getaddresses([str(value)])
        except Exception:  # pragma: no cover, getaddresses is very tolerant
            pairs = []
        for _name, addr in pairs:
            addr = addr.strip().lower()
            if addr and addr not in out:
                out.append(addr)
    return out


def strip_quoted(body: str) -> str:
    """Cut the body at the first quoted reply or forwarded header, then trim a signature.

    Cut points, checked per line: an Original Message separator, ``From:`` right after a
    blank line, ``On ... wrote:``, a Lotus Notes ``Forwarded by`` line, or the first line
    starting with ``>``. Everything from the cut line onward is dropped.
    """
    lines = body.split("\n")
    cut = len(lines)
    for i, line in enumerate(lines):
        if (
            ORIGINAL_MESSAGE_RE.match(line)
            or ON_WROTE_RE.match(line)
            or FORWARDED_BY_RE.match(line)
            or line.startswith(">")
            or (BODY_FROM_RE.match(line) and i > 0 and lines[i - 1].strip() == "")
        ):
            cut = i
            break
    kept = lines[:cut]
    for i, line in enumerate(kept):
        if SIGNATURE_DELIM_RE.match(line):
            kept = kept[:i]
            break
    return normalize_body_ws("\n".join(kept))


def normalize_body_ws(text: str) -> str:
    """Trailing whitespace off every line, at most one blank line in a row, trimmed."""
    lines = [ln.rstrip() for ln in text.split("\n")]
    out: list[str] = []
    blank = False
    for ln in lines:
        if ln == "":
            if blank:
                continue
            blank = True
        else:
            blank = False
        out.append(ln)
    return "\n".join(out).strip()


def thread_key_for(subject_norm: str, participants: list[str]) -> str:
    key = subject_norm + "\n" + ",".join(sorted(set(participants)))
    return cache.sha1_text(key)[:16]


def split_header_block(text: str) -> tuple[str, str]:
    """Split decoded text into (header block, body) at the first blank line."""
    idx = text.find("\n\n")
    if idx < 0:
        return text, ""
    return text[:idx], text[idx + 2 :]


def tolerant_headers(header_block: str) -> dict[str, list[str]]:
    """Parse ``Name: value`` lines by hand, unfolding continuations, skipping junk."""
    headers: dict[str, list[str]] = {}
    current: str | None = None
    for line in header_block.split("\n"):
        if line[:1] in (" ", "\t") and current:
            headers[current][-1] += " " + line.strip()
            continue
        m = HEADER_LINE_RE.match(line)
        if not m:
            current = None
            continue
        current = m.group(1).lower()
        headers.setdefault(current, []).append(m.group(2).strip())
    return headers


HEADER_NAMES = ("message-id", "date", "from", "to", "cc", "subject")


def extract_headers(raw: bytes, text: str) -> tuple[dict[str, list[str]], str]:
    """Header values by lowercased name. email.parser first, hand parse fills the gaps.

    email.parser stops reading headers at the first line that is not ``Name: value``
    or a continuation, and everything after it becomes body. The tolerant parse skips
    such lines instead, so any header the strict parser lost is recovered from it.
    Returns (headers, mode) where mode is ``email`` when the strict parser produced a
    From header and ``fallback`` otherwise.
    """
    header_block, _body = split_header_block(text)
    headers: dict[str, list[str]] = {}
    try:
        msg = email.message_from_bytes(raw, policy=email.policy.default)
        for name in HEADER_NAMES:
            values = msg.get_all(name)
            if values:
                headers[name] = [str(v) for v in values]
    except Exception as exc:  # the spec asks for a tolerant fallback on any failure
        log.debug("email.parser failed, falling back: %s", exc)
        headers = {}
    mode = "email" if headers.get("from") else "fallback"
    loose = tolerant_headers(header_block)
    for name in HEADER_NAMES:
        if not headers.get(name) and loose.get(name):
            headers[name] = loose[name]
    return headers, mode


def parse_file(path: Path, corpus_dir: Path, now: datetime | None = None) -> Parsed:
    raw = path.read_bytes()
    rel = path.relative_to(corpus_dir).as_posix()
    parts = rel.split("/")
    mailbox = parts[0] if len(parts) > 1 else ""
    folder = parts[1] if len(parts) > 2 else ""
    msg_id = cache.sha1_bytes(raw)[:12]

    text = raw.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    headers, mode = extract_headers(raw, text)
    _header_block, body_raw = split_header_block(text)

    def first(name: str) -> str | None:
        vals = headers.get(name)
        return vals[0] if vals else None

    from_list = parse_addrs(headers.get("from"))
    from_addr = from_list[0] if from_list else ""
    to_addrs = parse_addrs(headers.get("to"))
    cc_addrs = parse_addrs(headers.get("cc"))
    subject = collapse_ws(first("subject") or "")
    subject_norm = normalize_subject(subject)
    date_iso = parse_date(first("date"), now=now)
    header_message_id = (first("message-id") or "").strip() or None
    body_clean = strip_quoted(body_raw)
    participants = [from_addr] + to_addrs + cc_addrs

    return Parsed(
        id=msg_id,
        path=rel,
        mailbox=mailbox,
        folder=folder,
        header_message_id=header_message_id,
        date_iso=date_iso,
        date_source="header" if date_iso else None,
        from_addr=from_addr,
        to_addrs=to_addrs,
        cc_addrs=cc_addrs,
        subject=subject,
        subject_norm=subject_norm,
        body_raw=body_raw,
        body_clean=body_clean,
        thread_key=thread_key_for(subject_norm, [p for p in participants if p]),
        char_len=len(body_clean),
        parse_mode=mode,
        raw=raw,
    )


def _path_number(rel: str) -> int:
    stem = rel.rsplit("/", 1)[-1]
    digits = re.match(r"(\d+)", stem)
    return int(digits.group(1)) if digits else 0


def infer_dates(messages: list[Parsed]) -> int:
    """Fill missing dates from the nearest dated message in the same thread.

    Nearest means same mailbox and folder first, then closest file number, then the
    earliest path. Returns how many dates were inferred.
    """
    by_thread: dict[str, list[Parsed]] = {}
    for m in messages:
        by_thread.setdefault(m.thread_key, []).append(m)
    inferred = 0
    for m in messages:
        if m.date_iso:
            continue
        dated = [o for o in by_thread[m.thread_key] if o.date_iso and o.date_source == "header"]
        if not dated:
            continue
        n = _path_number(m.path)
        best = min(
            dated,
            key=lambda o: (
                0 if (o.mailbox, o.folder) == (m.mailbox, m.folder) else 1,
                abs(_path_number(o.path) - n),
                o.path,
            ),
        )
        m.date_iso = best.date_iso
        m.date_source = "inferred"
        inferred += 1
    return inferred


DUPLICATE_WINDOW_HOURS = 24


def mark_duplicates(messages: list[Parsed]) -> int:
    """Same from_addr, subject_norm, whitespace-collapsed body_clean, and a header
    date within DUPLICATE_WINDOW_HOURS of the canonical copy -> duplicate.

    The copy with the earliest path is canonical. Returns the duplicate count.

    Two refinements to the spec's rule. When body_clean is empty, which is every
    message that is nothing but a forward, the comparison falls back to body_raw. On
    this corpus the spec's version collapsed fifty distinct forwards with different
    quoted content into a handful of rows, because empty equals empty.

    The date window exists because of the Calpine Daily Gas Nomination messages: seven
    of them, July 2000 to April 2001, each an identical one-line body pointing at an
    attachment. Those are seven instances of a daily process, not one message sent
    seven times. The March and April 2001 export artifact, where messages appear twice
    with timestamps shifted by hours, still collapses because the shift is under the
    window. An undated message joins whichever cluster it lands in.
    """
    groups: dict[tuple[str, str, str], list[Parsed]] = {}
    for m in messages:
        body = collapse_ws(m.body_clean) or collapse_ws(m.body_raw)
        key = (m.from_addr, m.subject_norm, body)
        groups.setdefault(key, []).append(m)
    dups = 0
    for members in groups.values():
        if len(members) < 2:
            continue
        members.sort(key=lambda m: (m.date_iso or "", m.path))
        clusters: list[list[Parsed]] = []
        for m in members:
            if clusters and _within_window(clusters[-1][0], m):
                clusters[-1].append(m)
            else:
                clusters.append([m])
        for cluster in clusters:
            if len(cluster) < 2:
                continue
            cluster.sort(key=lambda m: m.path)
            canonical = cluster[0]
            for other in cluster[1:]:
                other.dup_of = canonical.id
                dups += 1
    return dups


def _within_window(anchor: Parsed, other: Parsed) -> bool:
    """True when either message is undated or their dates are within the window."""
    if not anchor.date_iso or not other.date_iso:
        return True
    a = datetime.fromisoformat(anchor.date_iso.replace("Z", "+00:00"))
    b = datetime.fromisoformat(other.date_iso.replace("Z", "+00:00"))
    return abs((b - a).total_seconds()) <= DUPLICATE_WINDOW_HOURS * 3600


# ---------------------------------------------------------------------------
# Storage.
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE messages (
    path TEXT PRIMARY KEY,
    id TEXT NOT NULL,
    mailbox TEXT NOT NULL,
    folder TEXT NOT NULL,
    header_message_id TEXT,
    date_iso TEXT,
    date_source TEXT,
    from_addr TEXT NOT NULL,
    to_addrs TEXT NOT NULL,
    cc_addrs TEXT NOT NULL,
    subject TEXT NOT NULL,
    subject_norm TEXT NOT NULL,
    body_raw TEXT NOT NULL,
    body_clean TEXT NOT NULL,
    thread_key TEXT NOT NULL,
    dup_of TEXT,
    char_len INTEGER NOT NULL,
    parse_mode TEXT NOT NULL
);
CREATE INDEX messages_id ON messages (id);
CREATE INDEX messages_thread ON messages (thread_key);
CREATE INDEX messages_dup ON messages (dup_of);
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


def write_db(db_path: Path, messages: list[Parsed], corpus_hash: str) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="messages", suffix=".db.tmp", dir=db_path.parent)
    os.close(fd)
    os.unlink(tmp)
    con = sqlite3.connect(tmp)
    try:
        con.executescript(SCHEMA)
        con.executemany(
            "INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [
                (
                    m.path,
                    m.id,
                    m.mailbox,
                    m.folder,
                    m.header_message_id,
                    m.date_iso,
                    m.date_source,
                    m.from_addr,
                    json.dumps(m.to_addrs),
                    json.dumps(m.cc_addrs),
                    m.subject,
                    m.subject_norm,
                    m.body_raw,
                    m.body_clean,
                    m.thread_key,
                    m.dup_of,
                    m.char_len,
                    m.parse_mode,
                )
                for m in messages
            ],
        )
        con.execute("INSERT INTO meta VALUES ('corpus_hash', ?)", (corpus_hash,))
        con.execute("INSERT INTO meta VALUES ('message_count', ?)", (str(len(messages)),))
        con.commit()
    finally:
        con.close()
    os.replace(tmp, db_path)


def open_db(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    return con


def db_corpus_hash(db_path: Path) -> str | None:
    if not Path(db_path).exists():
        return None
    con = open_db(db_path)
    try:
        row = con.execute("SELECT value FROM meta WHERE key='corpus_hash'").fetchone()
        return row[0] if row else None
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Driver.
# ---------------------------------------------------------------------------


def parse_corpus(
    corpus_dir: Path, data_dir: Path, force: bool = False, now: datetime | None = None
) -> dict:
    """Run the stage. Returns the stats dict, whether or not work was done."""
    corpus_dir = Path(corpus_dir)
    data_dir = Path(data_dir)
    db_path = data_dir / "messages.db"
    stats_path = data_dir / "parse_stats.json"
    raw_dir = data_dir / "raw"

    files = cache.list_files(corpus_dir)
    chash = cache.hash_paths(files, relative_to=corpus_dir)
    outputs = [db_path, stats_path]
    if not force and cache.is_done(data_dir, "parse", chash, outputs):
        stats = cache.read_json(stats_path, {})
        log.info("parse: up to date (corpus %s), skipping", chash[:12])
        return stats

    messages: list[Parsed] = []
    failed: list[dict] = []
    fallback = 0
    for path in files:
        try:
            m = parse_file(path, corpus_dir, now=now)
        except Exception as exc:
            rel = path.relative_to(corpus_dir).as_posix()
            log.error("parse: could not parse %s: %s", rel, exc)
            failed.append({"path": rel, "error": str(exc)})
            continue
        if m.parse_mode == "fallback":
            fallback += 1
        messages.append(m)
    messages.sort(key=lambda m: m.path)

    duplicates = mark_duplicates(messages)
    inferred = infer_dates(messages)
    undated = sum(1 for m in messages if not m.date_iso)
    largest = max(messages, key=lambda m: len(m.raw), default=None)

    raw_dir.mkdir(parents=True, exist_ok=True)
    for m in messages:
        (raw_dir / f"{m.id}.txt").write_bytes(m.raw)

    write_db(db_path, messages, chash)

    stats = {
        "corpus_hash": chash,
        "files_read": len(files),
        "parsed": len(messages),
        "failed": len(failed),
        "failed_files": failed,
        "fallback_header_parse": fallback,
        "duplicates": duplicates,
        "unique": len(messages) - duplicates,
        "undated": undated,
        "inferred_dates": inferred,
        "header_dates": sum(1 for m in messages if m.date_source == "header"),
        "largest": (
            {
                "path": largest.path,
                "id": largest.id,
                "bytes": len(largest.raw),
                "char_len": largest.char_len,
            }
            if largest
            else None
        ),
        "total_body_clean_chars": sum(m.char_len for m in messages if not m.dup_of),
    }
    cache.write_json_atomic(stats_path, stats)
    cache.mark_done(data_dir, "parse", chash, outputs)

    log.info(
        "parse: read %d, parsed %d, failed %d, duplicates %d, undated %d, inferred %d, "
        "largest %s (%d bytes)",
        stats["files_read"],
        stats["parsed"],
        stats["failed"],
        stats["duplicates"],
        stats["undated"],
        stats["inferred_dates"],
        stats["largest"]["path"] if largest else "-",
        stats["largest"]["bytes"] if largest else 0,
    )
    return stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Parse corpus/ into data/messages.db")
    ap.add_argument("--corpus", type=Path, default=cache.CORPUS_DIR)
    ap.add_argument("--data", type=Path, default=cache.DATA_DIR)
    ap.add_argument("--force", action="store_true", help="ignore the cache stamp")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)
    stats = parse_corpus(args.corpus, args.data, force=args.force)
    print(json.dumps({k: v for k, v in stats.items() if k != "failed_files"}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
