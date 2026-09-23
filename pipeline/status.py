"""Skip-if-done checks for the two model stages that run after validation.

The parse, batch, validate, compute, and build stages cache themselves. The
synthesizer and drafters are model calls that /run dispatches, so /run asks this
module whether they are already done before spending tokens on them.

    uv run python -m pipeline.status synthesis        prints "synthesis: done" or "synthesis: pending"
    uv run python -m pipeline.status stamp-synthesis  records that synthesis.json matches the current inputs
    uv run python -m pipeline.status drafts           prints one pending opportunity id per line, or "drafts: done"

Synthesis is done when data/synthesis.json exists and data/synthesis.stamp holds the
hash of the validated extractions it was built from. A change to any validated batch
changes the hash, so synthesis runs again. A draft is done when its artifact file
exists under run/artifacts/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from pipeline.cache import hash_paths

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RUN_DIR = ROOT / "run"


def validated_inputs_hash(data_dir: Path = DATA_DIR) -> str:
    batches = sorted((data_dir / "validated").glob("batch_*.json"))
    return hash_paths(batches, relative_to=data_dir)


def synthesis_done(data_dir: Path = DATA_DIR) -> bool:
    synthesis = data_dir / "synthesis.json"
    stamp = data_dir / "synthesis.stamp"
    if not synthesis.exists() or not stamp.exists():
        return False
    return stamp.read_text().strip() == validated_inputs_hash(data_dir)


def stamp_synthesis(data_dir: Path = DATA_DIR) -> str:
    if not (data_dir / "synthesis.json").exists():
        raise FileNotFoundError("data/synthesis.json does not exist, nothing to stamp")
    digest = validated_inputs_hash(data_dir)
    (data_dir / "synthesis.stamp").write_text(digest + "\n")
    return digest


def pending_drafts(data_dir: Path = DATA_DIR, run_dir: Path = RUN_DIR) -> list[str]:
    report_path = data_dir / "report.json"
    if not report_path.exists():
        return []
    report = json.loads(report_path.read_text())
    pending = []
    for opp in report.get("opportunities", []):
        if not opp.get("above_threshold") or opp.get("artifact_type") in (None, "none"):
            continue
        rel = opp.get("artifact_path")
        if not rel or not (run_dir.parent / rel).exists():
            pending.append(opp["opportunity_id"])
    return pending


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    command = args[0] if args else ""
    if command == "synthesis":
        print("synthesis: done" if synthesis_done() else "synthesis: pending")
        return 0
    if command == "stamp-synthesis":
        print(f"synthesis: stamped {stamp_synthesis()[:12]}")
        return 0
    if command == "drafts":
        pending = pending_drafts()
        print("\n".join(pending) if pending else "drafts: done")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
