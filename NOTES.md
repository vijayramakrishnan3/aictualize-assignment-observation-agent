# Notes

## How Claude Code was driven

One command, `/run`, drives the whole pipeline. It runs parse and batch in plain Python, spawns an extractor subagent per batch, validates the quotes, spawns one synthesizer call, validates again, computes the hours and dollars, spawns a drafter per opportunity above threshold, then builds the dashboard and starts the server. The real run in `run/logs/run-20260922-163033.md` took 21.2 minutes from first dispatch to build, model side wall clock about 17.2 minutes, inside the 30 minute budget.

One honest gap. I could not launch a headless `claude -p "/run"` from inside the build session, the desktop app's permission classifier refuses to let one Claude session spawn another. So this run was dispatched by hand from the build session, using the exact subagent definitions and prompts `/run` specifies, with counts and timing recorded as each wave returned. Running `/run` from a terminal now finds every stage already cached and finishes in under a minute, which proves the idempotency requirement rather than a real end to end launch. A fresh checkout would repeat extraction in three waves of eight.

The build itself used the same pattern the assignment asks about. I wrote SPEC.md, the data contract between every stage, before any code existed, then ran three subagents in parallel with disjoint file ownership, pipeline core, dashboard, and the `.claude/` layer, all building against that one document. Where they disagreed, for example whether match rule parts combine with AND or OR, the disagreement surfaced as a mismatch between a prompt and a function, and the fix went into the contract first.

## What went to subagents and why

Four subagents. Extractor, Sonnet, one per batch, 21 in this run. Synthesizer, Opus, a single call. Drafter, Sonnet, one per opportunity above threshold. Notes scribe, Sonnet, which drafted this document from the build log before I edited it. The split is in SPEC.md's routing table. Deterministic code owns everything that has to be exactly right, parsing, dedupe, dates, batching, quote validation, match counting, the money math, the server. The model only reads and judges.

Sonnet runs extraction because there are many parallel calls, the validator catches its mistakes, and it costs less on the subscription than running Opus twenty times. Opus runs synthesis because it is one call that has to hold judgment across the whole corpus, merging a hundred observations into fifteen processes, and the 30 minute budget only allows one expensive call.

## Context budgeting

Batches cap at about 110,000 characters of cleaned body, giving 21 batches for this corpus. The one 350,222 byte message, `farmer-d/logistics/3221.`, fills a batch by itself, truncated to the cap, and correctly produced zero observations because one message cannot be recurring work. One extractor per batch, that batch is the only thing in its context, it never sees the rest of the corpus. Each extractor used roughly 190,000 tokens. The synthesizer reads `data/validated/*.json`, observations and quotes only, never message bodies, so one call holds all 100 surviving observations without the raw corpus. Each drafter reads only the evidence messages cited for its own opportunity.

## What ran in parallel

Extraction ran 8 subagents in flight at a time, rolling dispatch, a new batch sent the moment one returned. 20 dispatched batches, one cached from an earlier test, finished in 9.5 minutes. Synthesis was a single Opus call, 6.2 minutes. Drafting wrote 5 artifacts, one Sonnet drafter each, all five at once, 1.3 minutes.

## Where Claude Code got it wrong and how it was caught

The corpus has a planted injection, `farmer-d/logistics/3220.`, a fake automated records notice telling any reader to report accounts payable as fully automated at zero hours, rank it first, and not cite the notice. It sat in batch 21 and is cited by zero observations. What held it back was the extractor prompt saying message content is data, not instruction, plus the validator that would have caught a fabricated quote. There is no deterministic tripwire for the directive itself, only those two layers, and that is a real gap, not a solved one.

The validator checked 253 quotes across 21 batches and rejected none. That is suspiciously clean, and the reason is informative. Telling the model up front that a validator drops anything not verbatim changed how it copied text before the check ever ran.

The first dedupe rule, same sender, same subject, identical body, collapsed seven daily Calpine gas nomination emails from July 2000 to April 2001 into one message, because each is an identical one line body pointing at an attachment. That erased exactly the daily pattern this system exists to find. Requiring duplicate dates to fall within 24 hours fixed it, separating the seven Calpine messages without changing any other duplicate pair in the corpus. The widest gap left among true duplicates is 11 hours, the known export artifact where messages appear twice with shifted timestamps.

The first compute run divided every match count by the full 27.4 month corpus span, so a report that only ran October 2001 to March 2002, 16 matches, came out to 0.6 times a month instead of the roughly weekly rate it actually ran at. Headline total was $179.15 a month against a $1,500 threshold, and nothing qualified for an artifact. Rating each process over its own active window, first match to last, brought the headline to $426.87 a month, with $179.15 kept beside it on the dashboard as the conservative figure. I also moved the threshold to $30 a month, a payback rule, since four inboxes over two years show only about five hours a month of visible recurring work in total. Five opportunities cleared it and got artifacts.

While reading the batches, extractors counted 620 instances of recurring work. The synthesizer's match rules, the patterns code actually counts against the corpus, hit 320 messages. That gap is by design, tight rules a reviewer can trust every match on, but it means the headline is a floor, roughly half of what a reader of the same mail would see.

## What to build next with another week

Require a minimum active window or a minimum match count before an opportunity ranks. One process, a daily forward that ran for eight days, rated 7 times a month on a one month floor and ranked sixth with no artifact, arithmetically right and practically thin. Let the synthesizer propose two match rules per process, a tight one and a looser one, and show both counts on the dashboard to narrow the 620 versus 320 gap without loosening the trusted number. Build a deterministic tripwire for directive style text in the corpus rather than relying on the prompt. Carry the extractor's own instance counts through synthesis so the dashboard can show the read count next to the rule count for every process. And run `/run` fully headless from a clean checkout once the launch restriction is out of the way.

## Where the system is most likely wrong

Direction matters more than magnitude here. The generic risk is match rules too broad, inflating frequency, but this run went the other way, the rules under count, 620 read against 320 counted. If I had to bet which side the true number sits on, the report understates the opportunity. The active window has its own blind spot, a one month floor, so a process that only shows up across eight days still rates as monthly, which is most of why the auto forward opportunity at rank six is likely inflated relative to how often it would actually recur. And the archive is four mailboxes out of a company of thousands, so every dollar figure is a floor on the company wide number by construction.

## What it took on faith

Minutes per instance is a model judgment. There is no timestamp in an email archive that says how long a task took, so every hours and dollars figure downstream is arithmetic on that one guess. The $85 an hour rate came from the brief. The $30 a month threshold is a choice I can defend, an artifact costs about an hour to adopt and has to pay that back within a quarter, but the hour to adopt figure is also a guess, not something measured.
