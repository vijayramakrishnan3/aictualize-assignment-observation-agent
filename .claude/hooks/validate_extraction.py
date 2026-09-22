"""PostToolUse hook on Write.

Claude Code pipes the tool call as JSON on stdin. If the written file sits under
data/extractions/, run the deterministic validator on it and print the pass and fail
counts, so a bad extraction is caught the moment it is written and not at the end.

Exit 0 prints the result to the transcript. Exit 2 also feeds the message back to the
agent that wrote the file, which is what we want when most of its quotes failed: the
extractor gets told once, in the same turn, and can rewrite with exact quotes.

Assumes pipeline/validate.py accepts `--file <path>` and prints pass and fail counts.
Standard library only.
"""

import json
import os
import re
import subprocess
import sys

GATE = 0.40


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or ""
    if not file_path:
        return 0

    project = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
    project = os.path.abspath(project)
    abs_path = os.path.abspath(
        file_path if os.path.isabs(file_path) else os.path.join(project, file_path)
    )
    extractions = os.path.join(project, "data", "extractions") + os.sep
    if not abs_path.startswith(extractions) or not abs_path.endswith(".json"):
        return 0

    rel = os.path.relpath(abs_path, project)
    proc = subprocess.run(
        ["uv", "run", "python", "-m", "pipeline.validate", "--file", rel],
        cwd=project,
        capture_output=True,
        text=True,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    print(f"[validate_extraction] {rel}")
    print(output.strip() or f"(validate exited {proc.returncode} with no output)")

    if proc.returncode != 0:
        print(f"[validate_extraction] validate exited {proc.returncode}", file=sys.stderr)
        return 2

    passed = _count(output, r"pass(?:ed)?")
    failed = _count(output, r"(?:fail(?:ed)?|reject(?:ed|s)?)")
    if passed is None or failed is None:
        return 0
    total = passed + failed
    if total == 0:
        print(
            f"[validate_extraction] {rel} has no evidence at all. Every observation "
            "needs at least one verbatim quote.",
            file=sys.stderr,
        )
        return 2
    rate = failed / total
    if rate > GATE:
        print(
            f"[validate_extraction] {rel}: {failed} of {total} quotes are not verbatim "
            f"({rate:.0%}). Re-read the batch and rewrite the file with quotes copied "
            "character for character from the message body.",
            file=sys.stderr,
        )
        return 2
    return 0


def _count(text: str, word: str):
    """Find a count next to a word: 'pass: 41', 'pass=41', 'passed 41', or '41 passed'."""
    for pattern in (
        rf"\b{word}\b\s*[:=]\s*(\d+)",
        rf"\b{word}\b\s+(\d+)",
        rf"(\d+)\s+{word}\b",
    ):
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


if __name__ == "__main__":
    sys.exit(main())
