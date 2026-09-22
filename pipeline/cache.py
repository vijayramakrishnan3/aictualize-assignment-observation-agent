"""Hashing and skip-if-done helpers shared by every stage.

A stage records a stamp under ``data/.cache/<stage>.json`` holding the hash of its
inputs and the list of outputs it wrote. On the next run the stage compares the current
input hash with the stamp and, if every listed output still exists, does nothing.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT / "corpus"
DATA_DIR = ROOT / "data"
RUN_DIR = ROOT / "run"


def sha1_bytes(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def sha1_file(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def list_files(root: Path) -> list[Path]:
    """Every regular file under root, sorted by relative path for stable hashing."""
    if not root.exists():
        return []
    files = [p for p in root.rglob("*") if p.is_file() and not p.name.startswith(".")]
    return sorted(files, key=lambda p: p.relative_to(root).as_posix())


def hash_paths(paths: Iterable[Path], relative_to: Path | None = None) -> str:
    """Hash of (relative path, content hash) pairs. Order independent."""
    entries = []
    for p in paths:
        p = Path(p)
        rel = p.relative_to(relative_to).as_posix() if relative_to else p.as_posix()
        entries.append(f"{rel}\t{sha1_file(p)}")
    entries.sort()
    return sha1_text("\n".join(entries))


def corpus_hash(corpus_dir: Path = CORPUS_DIR) -> str:
    return hash_paths(list_files(corpus_dir), relative_to=corpus_dir)


def stamp_path(data_dir: Path, stage: str) -> Path:
    return data_dir / ".cache" / f"{stage}.json"


def read_json(path: Path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def write_json_atomic(path: Path, obj) -> None:
    """Write JSON to a temp file in the same directory, then rename over the target."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, ensure_ascii=False, sort_keys=False)
            fh.write("\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def is_done(data_dir: Path, stage: str, input_hash: str, outputs: Iterable[Path]) -> bool:
    """True when the stamp matches input_hash and every listed output exists."""
    stamp = read_json(stamp_path(data_dir, stage))
    if not stamp or stamp.get("input_hash") != input_hash:
        return False
    for out in outputs:
        if not Path(out).exists():
            return False
    return True


def mark_done(data_dir: Path, stage: str, input_hash: str, outputs: Iterable[Path]) -> None:
    write_json_atomic(
        stamp_path(data_dir, stage),
        {"stage": stage, "input_hash": input_hash, "outputs": [str(o) for o in outputs]},
    )
