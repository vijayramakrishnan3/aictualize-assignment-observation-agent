# Observation agent, build spec

The assignment brief is `ASSIGNMENT.md`. Read it first. This file is the contract every
part of the system builds against. If you need to change a contract, change it here and
say so in your final report.

## Principle

Deterministic Python does everything that has to be exactly right. A model does only the
reading and judging. The two meet through JSON files on disk with fixed schemas below.

- Python 3.12 via `uv`. Run everything as `uv run python -m pipeline.<stage>`. Standard
  library only unless a dependency is unavoidable. Never use the system `python3`.
- Every stage is idempotent and cached. Outputs are keyed by a content hash of their
  inputs. Re-running on an unchanged corpus does no work.
- Tests live in `tests/`, run with `uv run pytest`, and never call a model.
- No em dashes anywhere. Not in code comments, docs, or generated text.

## Layout

```
corpus/                 the 3,240 raw messages, read only
pipeline/               deterministic code
  parse.py              corpus -> data/messages.db
  batch.py              messages.db -> data/batches/batch_NNN.json
  validate.py           data/extractions/*.json -> data/validated/*.json (+ rejects)
  compute.py            data/synthesis.json + messages.db -> data/report.json
  build.py              report.json -> run/dashboard/ (static site) + run/report.md
  serve.py              serves run/dashboard on localhost
  cache.py              hashing and skip-if-done helpers
tests/
dashboard/              static template files build.py copies and fills
run/                    output of one real run, committed: report.md, dashboard/, logs/, artifacts/
data/                   intermediate, gitignored
.claude/                CLAUDE.md, agents/, commands/, hooks/, settings.json
notes/BUILD-LOG.md      running log of decisions and takeaways during the build
NOTES.md                the two-page write-up, written last
```

## Stage 1, parse (`pipeline/parse.py`)

Reads every file under `corpus/`. Writes `data/messages.db` (SQLite) with table
`messages`:

| column | meaning |
|---|---|
| id | first 12 hex of sha1 of the raw file bytes. Stable across runs. |
| path | relative path under corpus/ |
| mailbox | top folder, e.g. `farmer-d` |
| folder | second folder, e.g. `logistics` |
| header_message_id | the Message-ID header, may be null |
| date_iso | ISO 8601 UTC, null if unparseable |
| date_source | `header`, `inferred`, or null |
| from_addr | lowercased |
| to_addrs | JSON list, lowercased |
| cc_addrs | JSON list, lowercased |
| subject | as written |
| subject_norm | lowercased, leading `re:`/`fw:`/`fwd:` chains stripped, whitespace collapsed |
| body_raw | everything after the header block |
| body_clean | body_raw with quoted replies, forwarded headers, and signatures stripped, whitespace normalized |
| thread_key | subject_norm plus the sorted set of participant addresses, hashed |
| dup_of | id of the canonical copy if this is a duplicate, else null |
| char_len | len(body_clean) |

Rules:

- Use `email.parser` with `policy=email.policy.default`, and fall back to a tolerant
  header split on `\n\n` when it throws.
- Duplicate = same `from_addr`, same `subject_norm`, and identical `body_clean` after
  normalization. Keep the copy with the earliest path as canonical.
- Date inference: if the Date header is missing or unparseable, use the date of the
  nearest message in the same thread. Otherwise leave null and mark it.
- Quoted reply stripping: cut at the first line matching `^-----Original Message-----`,
  `^From:\s` after a blank line, `^On .* wrote:$`, or a run of lines starting with `>`.
  Keep the cut text in body_raw so quotes can still be validated against it.
- The parser must log counts: files read, parsed, duplicates, undated, inferred dates,
  largest message. Print them and write `data/parse_stats.json`.
- Also write `data/raw/<id>.txt`, the raw file, for the dashboard drill-through.

## Stage 2, batch (`pipeline/batch.py`)

Writes `data/batches/batch_NNN.json`, non-duplicate messages only, ordered by mailbox
then date. Each batch is at most 110,000 characters of `body_clean` plus headers. A
single message larger than the cap gets its body truncated to the cap with a
`truncated: true` flag. Batch file:

```json
{"batch_id": "batch_007", "corpus_hash": "…", "messages": [
  {"id": "3f2a…", "date": "2001-10-26", "from": "…", "to": ["…"], "subject": "…",
   "mailbox": "farmer-d", "body": "…", "truncated": false}
]}
```

Also writes `data/batches/index.json`: list of batch ids with message counts and a
`done` flag that is true when `data/extractions/<batch_id>.json` exists and its
`corpus_hash` matches.

## Stage 3, extraction (model, subagent `extractor`)

One subagent per batch. Input is the batch file. Output is
`data/extractions/<batch_id>.json`:

```json
{"batch_id": "batch_007", "corpus_hash": "…", "observations": [
  {"process": "Daily gas pipeline nominations",
   "description": "Schedulers submit and confirm daily volumes with pipelines and counterparties.",
   "actors": ["j..farmer@enron.com"],
   "stall": "Confirmations arrive late and volumes get re-keyed from spreadsheets.",
   "evidence": [{"message_id": "3f2a…", "quote": "verbatim text of at most 300 characters"}],
   "instances_in_batch": 14,
   "minutes_per_instance": 20,
   "automation_idea": "Auto-parse nomination emails into the scheduling sheet and flag mismatches."}
]}
```

Quotes must be copied verbatim from `body`. The validator will drop anything that is
not an exact substring. The extractor is told this.

## Stage 4, validate (`pipeline/validate.py`)

For every extraction file: for every evidence item, the quote (whitespace-collapsed,
case preserved) must be a substring of that message's `body_clean` or `body_raw`
(whitespace-collapsed). Passing evidence is kept. Failing evidence goes to
`data/validated/rejects.json` with a reason. Observations with no surviving evidence are
dropped. Writes `data/validated/<batch_id>.json` in the same shape, plus
`data/validated/summary.json` with pass and fail counts per batch.

## Stage 5, synthesis (model, subagent `synthesizer`)

Reads all `data/validated/*.json` (observations only, no bodies) and writes
`data/synthesis.json`:

```json
{"processes": [
  {"process_id": "p01", "name": "…", "description": "…", "actors": ["…"],
   "stall": "…",
   "match_rule": {"subject_regex": "nomination|nom\\b", "body_any": ["nominat"], "from_any": []},
   "minutes_per_instance": 20,
   "expected_matches": ["3f2a…", "9b1c…", "77de…"],
   "evidence": [{"message_id": "…", "quote": "…"}]}],
 "opportunities": [
  {"opportunity_id": "o01", "process_id": "p01", "title": "…",
   "automation": "what to build, one paragraph",
   "minutes_saved_per_instance": 15, "rationale": "…",
   "evidence": [{"message_id": "…", "quote": "…"}],
   "artifact_type": "sop | email_template | checklist | template | none"}]}
```

`expected_matches` is 3 to 5 message ids the synthesizer expects the rule to hit. compute.py
reports any that miss, which is a cheap check that the rule means what the model thinks
it means. `minutes_saved_per_instance` on an opportunity is capped at the process's
`minutes_per_instance`.

The `match_rule` is the key design choice. The model proposes a deterministic rule that
identifies instances of the process in the corpus. Code counts the matches. Frequency is
therefore auditable: the dashboard can show exactly which messages matched.

Evidence in synthesis must be drawn from validated extractions. validate.py is run again
on synthesis.json before compute.

## Stage 6, compute (`pipeline/compute.py`)

For each process, count non-duplicate messages matching `match_rule`. The non-empty
parts are ANDed: the regex must match subject_norm, any keyword must appear in
body_clean lowercased, and from_addr must be in the list, for whichever parts are
filled in. An empty part is skipped. A rule with all three empty matches nothing. Corpus span in months = (max date minus min date over dated
non-duplicate messages) / 30.44, floored at 1.

```
active_months       = (last match minus first match) / 30.44, floored at 1
instances_per_month = matches / active_months
hours_per_month     = instances_per_month * minutes_saved_per_instance / 60
dollars_per_month   = hours_per_month * 85
```

Writes `data/report.json`:

```json
{"generated_at": "…", "corpus_hash": "…", "rate_per_hour": 85, "span_months": 14.2,
 "totals": {"messages": 3240, "unique": …, "duplicates": …, "undated": …,
            "hours_per_month": …, "dollars_per_month": …},
 "processes": [ … each with match_count, matched_message_ids (first 200), instances_per_month … ],
 "opportunities": [ … ranked by dollars_per_month desc, each with hours_per_month, dollars_per_month,
                     instances_per_month, evidence (with from, date, subject resolved), artifact_path or null … ]}
```

The threshold for producing an artifact is `dollars_per_month >= 30`, a payback rule: an
artifact costs about an hour to adopt and must pay that back within a quarter on the hours
visible in four mailboxes. It is a constant in compute.py and is printed in the report.

## Stage 7, act (model, subagent `drafter`)

For each opportunity at or above threshold, write `run/artifacts/<opportunity_id>-<slug>.md`:
an SOP, an email template, a checklist, or a template, per `artifact_type`. Every
artifact opens with a one-line purpose, cites at least two evidence message ids, and is
something a person could use the next morning without editing.

## Stage 8, build and serve (`pipeline/build.py`, `pipeline/serve.py`)

`build.py` writes `run/dashboard/` as a static site: `index.html`, `data.json`
(report.json with artifact text inlined), and copies `data/raw/<id>.txt` for every
message referenced anywhere into `run/dashboard/messages/`. Also writes `run/report.md`,
a readable version of the same report.

`serve.py` serves `run/dashboard/` on `http://localhost:8765` with the standard library
only. `/` is the dashboard. `/messages/<id>.txt` is the raw message.

Dashboard requirements, from the brief: ranked opportunities, a running dollar total,
and drill-through on every claim. Clicking a dollar figure opens the opportunity. The
opportunity view shows the math (matches, span, minutes, hours, dollars), the match rule,
the evidence quotes, and the artifact. Clicking a quote opens the raw message with the
quote highlighted. It has to look like something you would put in front of a client
president: calm, dense, no clutter, readable on a laptop.

## Stage 9, orchestration (`.claude/commands/run.md`)

`/run` drives the whole thing inside Claude Code, unattended:

1. `uv run python -m pipeline.parse` then `batch`.
2. Read `data/batches/index.json`. For every batch not done, spawn an `extractor`
   subagent. Spawn them in parallel, up to 8 at a time.
3. `uv run python -m pipeline.validate`.
4. Spawn one `synthesizer` subagent.
5. `uv run python -m pipeline.validate --synthesis` then `compute`.
6. Spawn one `drafter` subagent per opportunity above threshold, in parallel.
7. `uv run python -m pipeline.build` then start `serve` in the background and print the URL.
8. Append a run summary to `run/logs/run-<timestamp>.md`.

Hooks: a `PostToolUse` hook on `Write` that runs validate on any file written under
`data/extractions/` and prints the pass/fail count, so a bad extraction is caught at the
moment it is written and not at the end.

## Model routing

| agent | model | why |
|---|---|---|
| extractor | sonnet | many parallel calls, structured output, validator catches errors |
| synthesizer | opus | one call, needs judgment across the whole corpus |
| drafter | sonnet | bounded writing task |
| notes-scribe | sonnet | turns the build log into NOTES.md |
