---
description: Run the whole observation pipeline unattended, parse through dashboard, and print the localhost URL.
allowed-tools: Bash(uv run:*), Read, Write, Glob, Grep, Agent
---

Run the full pipeline from SPEC.md Stage 9, start to finish, without asking questions.
Every step below is mandatory and in order. Do not skip a step because its output
already exists, the stages are cached and will return quickly on their own. Do not stop
to ask for confirmation. The only reason to stop early is the reject-rate gate in step 4.

Record the wall-clock time at the start of every step so the log in step 9 is accurate.
Get timestamps with `uv run python -c "import datetime;print(datetime.datetime.now().isoformat(timespec='seconds'))"`.

## Step 0, start the log

Get a timestamp in the form `YYYYMMDD-HHMMSS` with
`uv run python -c "import datetime;print(datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))"`.
The log path for this run is `run/logs/run-<timestamp>.md`. You will write it in step 9.
Keep the timestamp, the start time, and every count you collect below in your working
notes as you go.

## Step 1, parse and batch

Run `uv run python -m pipeline.parse`. Record the counts it prints, files read, parsed,
duplicates, undated, inferred dates, largest message. If it exits non-zero, stop and
report the error. Nothing downstream can run without messages.db.

Run `uv run python -m pipeline.batch`. Record how many batches it wrote.

## Step 2, extract in parallel

Read `data/batches/index.json`. It lists every batch with a message count and a `done`
flag. Collect the `batch_id` of every entry where `done` is false. If the list is empty,
record "0 batches dispatched, all cached" and go to step 3.

Dispatch the pending batches to `extractor` subagents in waves of up to 8. For each
wave, issue all the Agent calls in one message so they run concurrently, using
`subagent_type: extractor` and this prompt, with the real path filled in:

```
Extract observations from data/batches/<batch_id>.json and write
data/extractions/<batch_id>.json. Follow your instructions exactly.
```

Wait for every agent in the wave to return before starting the next wave. Each extractor
replies with one line: batch id, observation count, evidence count. Record those lines.
If an extractor fails or returns without writing its file, dispatch it once more in the
next wave. If it fails a second time, record the batch id as failed and continue, do not
block the run on one batch.

Record the number of waves, the number of batches dispatched, and the elapsed time for
the whole step.

## Step 3, validate the extractions

Run `uv run python -m pipeline.validate`. It checks every quote against the raw message
text and writes `data/validated/batch_*.json`, `data/validated/rejects.json`, and
`data/validated/summary.json`.

Read `data/validated/summary.json`. For each batch compute the reject rate,
fail divided by pass plus fail. Record the per-batch pass and fail counts and the totals.

## Step 4, the reject-rate gate

If any batch has a reject rate above 40 percent, stop here. Write the run log (step 9)
with everything collected so far, state which batches exceeded the gate with their
numbers, and end your reply with a plain statement that the run halted at validation
and why. Do not run synthesis on extractions that are mostly wrong. A reject rate that
high means the extractor is paraphrasing, and the fix is in the extractor prompt, not in
running more of the pipeline.

If every batch is at or under 40 percent, continue.

## Step 5, synthesize

Spawn one `synthesizer` subagent with `subagent_type: synthesizer` and this prompt:

```
Read every file matching data/validated/batch_*.json, merge the observations into
distinct processes, and write data/synthesis.json. Follow your instructions exactly.
```

Wait for it. Record its one-line reply and the elapsed time. If `data/synthesis.json`
does not exist afterwards, spawn it once more. If it still does not exist, stop, write
the log, and report.

## Step 6, validate the synthesis and compute

Run `uv run python -m pipeline.validate --synthesis`. Record pass and fail counts. If
every quote fails, stop, write the log, and report, because the synthesizer has rewritten
its evidence instead of copying it.

Run `uv run python -m pipeline.compute`. It writes `data/report.json`. Read
`data/report.json` and record `span_months`, the totals block, the number of processes,
the number of opportunities, and the threshold it prints. Also record, for each
process, `match_count` and whether every id in `expected_matches` is in
`matched_message_ids`. A process whose expected ids do not match is a match-rule bug and
goes in the log.

## Step 7, draft artifacts in parallel

From `data/report.json`, collect every opportunity whose `dollars_per_month` is at or
above the threshold and whose `artifact_type` is not `none`. Spawn one `drafter`
subagent per opportunity, all in one message so they run concurrently, using
`subagent_type: drafter` and this prompt with the real id:

```
Write the artifact for opportunity <opportunity_id>. Follow your instructions exactly.
```

Wait for all of them. Each replies with the path it wrote. Record the paths. If a
drafter returns without a path, dispatch it once more. Record the count of artifacts
written and the elapsed time.

## Step 8, build and serve

Run `uv run python -m pipeline.build`. It writes `run/dashboard/` and `run/report.md`
and links artifacts into the report. Record that it succeeded.

Start the server in the background with `uv run python -m pipeline.serve`, using the
Bash tool's background mode so the command returns immediately. Do not wait on it.

## Step 9, write the run log

Write `run/logs/run-<timestamp>.md` with these sections, using the numbers you
collected. Every number comes from a command output or a file you read, never from
memory of a previous run.

```
# Run <timestamp>

Started <start>, finished <end>, <total minutes> minutes wall clock.

## Parse
files read, parsed, duplicates, undated, inferred dates, largest message

## Batch
batches total, batches already done, batches dispatched, waves, extract step minutes

## Extract
one line per extractor reply, then any batch that failed twice

## Validate
per batch: pass, fail, reject rate. Then totals and the highest reject rate.
Gate result: passed, or halted with the batches over 40 percent.

## Synthesize
synthesizer reply line, synthesis validate pass and fail, step minutes

## Compute
span months, unique messages, hours per month, dollars per month, threshold,
processes, opportunities above threshold, any process whose expected_matches missed

## Draft
artifacts written, one path per line, step minutes

## Serve
http://localhost:8765
```

## Step 10, finish

End your reply with the final totals in three lines, hours per month, dollars per
month, artifacts written, then the log path, then on its own line:

http://localhost:8765
