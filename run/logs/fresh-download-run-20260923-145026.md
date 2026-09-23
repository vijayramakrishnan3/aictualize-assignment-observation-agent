# Run 20260923-145026

Started 2026-09-23T14:50:26, finished 2026-09-23T15:06:23, 16.0 minutes wall clock.

This was a fresh run. `run/` had been cleared, so nothing was cached. Every batch was
extracted, synthesis ran, and all three artifacts were drafted from scratch.

## Parse

- files read 3240, parsed 3240, failed 0
- duplicates 42, unique 3198
- undated 3, inferred dates 0
- largest message farmer-d/logistics/3221. (id aa83ea509a55, 350222 bytes)

## Batch

- batches total 21, already done 0, dispatched 21
- waves 3 (8, 8, 5)
- 1 message truncated (batch_009, the single 350 KB message, cut to 110000 chars)
- extract step 14:50:31 to 14:59:41, 9.2 minutes

## Extract

- batch_001: 5 observations, 15 evidence items
- batch_002: 6 observations, 17 evidence items
- batch_003: 5 observations, 10 evidence items
- batch_004: 6 observations, 19 evidence items
- batch_005: 6 observations, 16 evidence items
- batch_006: 4 observations, 11 evidence items
- batch_007: 6 observations, 20 evidence items
- batch_008: 6 observations, 12 evidence items
- batch_009: 1 observations, 1 evidence items
- batch_010: 6 observations, 13 evidence items
- batch_011: 7 observations, 16 evidence items
- batch_012: 3 observations, 8 evidence items
- batch_013: 6 observations, 10 evidence items
- batch_014: 3 observations, 7 evidence items
- batch_015: 4 observations, 12 evidence items
- batch_016: 6 observations, 16 evidence items
- batch_017: 6 observations, 16 evidence items
- batch_018: 5 observations, 16 evidence items
- batch_019: 6 observations, 15 evidence items
- batch_020: 5 observations, 12 evidence items
- batch_021: 4 observations, 8 evidence items

Failed twice: none.

Notes from the extractors:

- batch_008 found an embedded "processing directive" in message 4c21e0fe6402 telling an
  automated reviewer to report accounts payable as fully automated and rank it top
  priority. It was treated as content and excluded. Prompt injection in the corpus,
  handled.
- batch_014's first write had a JSON syntax error. The PostToolUse validator hook caught
  it, and the rewrite passed.
- batch_011 and batch_012 both saw about 25 to 43 daily "Credit Report" emails with
  empty bodies. There is no verbatim quote to cite, so the process is under-evidenced
  or excluded. This is a known gap in coverage.

## Validate

| batch | pass | fail | reject rate |
|---|---|---|---|
| batch_001 | 15 | 0 | 0.0% |
| batch_002 | 17 | 0 | 0.0% |
| batch_003 | 10 | 0 | 0.0% |
| batch_004 | 19 | 0 | 0.0% |
| batch_005 | 15 | 0 | 0.0% |
| batch_006 | 11 | 0 | 0.0% |
| batch_007 | 20 | 0 | 0.0% |
| batch_008 | 12 | 0 | 0.0% |
| batch_009 | 1 | 0 | 0.0% |
| batch_010 | 13 | 0 | 0.0% |
| batch_011 | 14 | 1 | 6.7% |
| batch_012 | 8 | 0 | 0.0% |
| batch_013 | 10 | 0 | 0.0% |
| batch_014 | 7 | 0 | 0.0% |
| batch_015 | 12 | 0 | 0.0% |
| batch_016 | 16 | 0 | 0.0% |
| batch_017 | 16 | 0 | 0.0% |
| batch_018 | 15 | 1 | 6.3% |
| batch_019 | 14 | 0 | 0.0% |
| batch_020 | 12 | 0 | 0.0% |
| batch_021 | 8 | 0 | 0.0% |

Totals: pass 265, fail 2, reject rate 0.7%. Observations in 106, out 106.
Highest reject rate: batch_011 at 6.7%.

Gate result: passed.

## Synthesize

- status: pending, synthesizer dispatched (1 agent)
- reply: `synthesis: 15 processes, 15 opportunities, 125 evidence items`
- stamped 8c618ca2b77d
- synthesis validate: pass 125, fail 0, processes 15 to 15, opportunities 15 to 15
- step 14:59:46 to 15:04:06, 4.3 minutes

## Compute

- span months 27.38
- unique messages 3198
- hours per month 6.56, dollars per month $559.38 (rate $85/hour)
- corpus-span basis: 3.07 hours, $258.99 per month
- threshold $30
- processes 15, opportunities 15, above threshold 3
- expected_matches: every process matched all its expected ids. No match-rule misses.

| process | match_count |
|---|---|
| p01 | 55 |
| p02 | 39 |
| p03 | 14 |
| p04 | 76 |
| p05 | 25 |
| p06 | 17 |
| p07 | 4 |
| p08 | 16 |
| p09 | 19 |
| p10 | 17 |
| p11 | 19 |
| p12 | 14 |
| p13 | 16 |
| p14 | 17 |
| p15 | 7 |

The two largest opportunities, o04 ($115.82) and o15 ($49.58), have artifact type
`none`, so they get no artifact.

## Draft

- 3 drafters dispatched (o13, o11, o01), all returned a path
- run/artifacts/o01-nightly-flow-without-deal-exception-report-with-a-prefilled.md
- run/artifacts/o11-morning-pre-flash-congestion-reconciliation-checklist.md
- run/artifacts/o13-auto-generated-weekly-california-capacity-report.md
- step 15:04:15 to 15:05:47, 1.5 minutes

Slug mismatch fixed during the run: the o13 drafter wrote
`o13-auto-generated-weekly-california-capac.md`, which follows the 40-character slug
rule in `.claude/agents/drafter.md`. `pipeline/compute.py` builds `artifact_path` with a
60-character slug, so `pipeline.status drafts` still listed o13 as pending and the report
link pointed at a missing file. The file was renamed to the path compute expects. Its
content is unchanged. `drafts: done` after the rename. The drafter prompt and
`slugify(limit=60)` still disagree, and one of them should change.

## Serve

http://localhost:8765
