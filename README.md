# Observation agent

Reads a company's email archive, finds the recurring work, ranks the automation
opportunities in hours and dollars per month, cites every claim to a verbatim quote,
drafts an artifact for each opportunity worth acting on, and serves the result as a
dashboard. Runs inside Claude Code on a subscription, with no API keys.

The brief is `ASSIGNMENT.md`. The contract is `SPEC.md`. The write-up is `NOTES.md`.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) with Python 3.12. `uv sync` sets up the environment.
- [Claude Code](https://code.claude.com/) with a subscription.

## Run it

Open Claude Code in this directory and type

```
/run
```

It parses and batches the corpus, spawns extractor subagents eight at a time, validates
every quote, spawns one synthesizer, validates again, computes the numbers, spawns one
drafter per opportunity above threshold, builds the dashboard, starts the server, and
writes a log to `run/logs/`. It finishes unattended in under 30 minutes and prints
http://localhost:8765 when it is done. A second run on the same corpus repeats nothing.

To serve an existing run without Claude Code

```
uv run python -m pipeline.serve
```

To run the tests, which never call a model

```
uv run pytest
```

## Layout

```
corpus/          the 3,240 raw messages, read only
pipeline/        deterministic Python, one module per stage
  parse.py       corpus to data/messages.db and data/raw/
  batch.py       messages to data/batches/
  validate.py    every quote checked as an exact substring, rejects logged
  compute.py     match rules counted, hours and dollars computed
  build.py       static dashboard and run/report.md
  serve.py       localhost:8765, standard library only
  cache.py       content hashing, skip if done
tests/           uv run pytest
dashboard/       static templates build.py fills
data/            intermediate files, gitignored
run/             one real run: report.md, dashboard/, logs/, artifacts/
.claude/         CLAUDE.md, agents/, commands/run.md, hooks/, settings.json
notes/           the build log the notes were written from
NOTES.md         the two-page write-up
```

## Design

Deterministic code does everything that has to be exactly right and a model does only
the reading and judging. Parsing, deduplication, dates, batching, quote validation,
frequency counting, the money arithmetic, and the server are Python with no model call.
A Sonnet subagent reads each batch and proposes observations with verbatim quotes. An
Opus subagent merges those into distinct processes and, instead of guessing how often
each one happens, writes a deterministic match rule that code applies to the whole
corpus, so every frequency is a count the dashboard can list message by message. A
validator checks every quote as an exact substring of the raw message before it can
reach synthesis, and again before it can reach the report, and a hook runs that check
the moment an extraction is written. Anything that fails is dropped, not repaired, and
the reject rate is reported because it is itself evidence of how far the model can be
trusted with this.
