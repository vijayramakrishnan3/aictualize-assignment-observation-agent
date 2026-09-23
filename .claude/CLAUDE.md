# Observation agent

Reads a 3,240-message email archive, finds the recurring work, ranks the automation
opportunities in hours and dollars per month, cites every claim to a verbatim quote,
drafts artifacts for the biggest ones, and serves a dashboard on localhost. The brief is
`ASSIGNMENT.md`. The contract every stage builds against is `SPEC.md`. Read both before
touching anything.

## The line

Deterministic Python does everything that must be exactly right. A model does only the
reading and judging. They meet through JSON files on disk with fixed schemas in SPEC.md.

Code owns parsing, dedupe, dates, batching, quote validation, match counting, the hours
and dollars arithmetic, the build, and the server. Models own extraction, synthesis,
drafting, and the notes draft. Never move a job across that line.

## Stages

| stage | what | command or agent |
|---|---|---|
| 1 parse | corpus to `data/messages.db`, `data/raw/`, `data/parse_stats.json` | `uv run python -m pipeline.parse` |
| 2 batch | messages to `data/batches/batch_NNN.json` and `index.json` | `uv run python -m pipeline.batch` |
| 3 extract | one batch to `data/extractions/<batch_id>.json` | `extractor` subagent, sonnet, 8 in parallel |
| 4 validate | quotes checked, `data/validated/` plus `rejects.json` and `summary.json` | `uv run python -m pipeline.validate` |
| 5 synthesize | validated observations to `data/synthesis.json` | `synthesizer` subagent, opus, one call |
| 5b validate | synthesis quotes checked | `uv run python -m pipeline.validate --synthesis` |
| 6 compute | match rules counted, money computed, `data/report.json` | `uv run python -m pipeline.compute` |
| 7 act | one artifact per opportunity above threshold, `run/artifacts/` | `drafter` subagent, sonnet, all in parallel |
| 8 build | `run/dashboard/` and `run/report.md` | `uv run python -m pipeline.build` |
| 8b serve | dashboard on http://localhost:8765 | `uv run python -m pipeline.serve` |
| 9 run | all of the above, unattended, logged to `run/logs/` | `/run` |

`data/` is intermediate and gitignored. `run/` is the output of one real run and is
committed. Tests are `uv run pytest` and never call a model.

## Rules that do not bend

- **No model output enters the report without passing `pipeline/validate.py`.**
  Extractions are validated before synthesis. Synthesis is validated before compute.
  A quote that is not an exact substring of the raw message is dropped, not repaired.
- **Quotes are never edited.** Not trimmed, not tidied, not fixed for typos, not
  paraphrased. Copied character for character from the message body, and copied again
  exactly when they move from extraction to synthesis to artifact.
- **The model never states a frequency.** It proposes a `match_rule`. Code counts.
- **Every stage is idempotent.** Outputs are keyed by content hash. The two model
  stages after validation are checked with `uv run python -m pipeline.status` before
  any agent is spawned. Re-running on an unchanged corpus dispatches no agents.
- **Standard library only** in `pipeline/`. Python 3.12 through `uv`. Never the system
  `python3`.
- **No em dashes anywhere.** Code, comments, docs, generated text.

## Subagents and hooks

Agents are in `.claude/agents/`. Each reads only what its prompt names. The
`PostToolUse` hook in `.claude/settings.json` runs the validator on any file written
under `data/extractions/` and reports the pass and fail counts at write time.
