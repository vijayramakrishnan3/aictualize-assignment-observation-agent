# Notes

## How I drove Claude Code

I drove Claude Code almost entirely by voice, through Wispr Flow. Before building
anything, I had it read the brief and the emails and explain back to me what the
problem actually was and what we were solving. Then I had it write a plan, one
document laying out every piece of the system, what each piece does, and how the
pieces hand work to each other. Nothing was built until that plan existed.

From there, three AI helpers built three pieces at the same time, each working from
the same plan. One built the code that cleans and checks the emails, one built the
dashboard, and one built the Claude Code setup, meaning the instructions for each
helper and the single command, /run, that runs everything. Each helper had its own
files, so they never overwrote each other.

The rule underneath all of it was simple. Anything that has to be exactly right is
regular code, not AI. That covers cleaning the emails, removing duplicates, checking
quotes, counting, the math, and the dashboard.

My computer's safety settings blocked one Claude session from launching another, so
the run in this repo was started step by step from my build session, using the same
helpers and instructions /run uses.

## What I handed to AI helpers and why

Email readers. 21 of them, on Sonnet, the cheaper model. Each one read one pile of
emails and wrote down the repeated tasks it saw, with exact quotes. This is
repetitive work, and a code checker catches any quote that isn't word for word.

One combiner, on Opus, the stronger model. It merged about 100 notes from the
readers into 15 distinct tasks. That takes judgment and only happens once, so it
got the better model.

Document writers. Five of them, on Sonnet. Each wrote one checklist or template for
one of the top tasks. It's a small, contained job.

Nothing that needs to be exact went to AI. The AI never decides how often a task
happens and never does the math. It suggests a rule for spotting a task, and code
counts the emails that match.

## How I kept each helper's workload manageable

The emails are about thirty times too big for one AI to read at once, and that's
the whole challenge. Regular code went first. It removed duplicate emails and
stripped out old replies quoted inside newer ones, which shrank the pile a lot
before any AI saw it. Then it split the emails into 21 piles sized to fit, and each
reader only ever saw its own pile. The combiner only read the readers' notes, never
the emails themselves. Each document writer only read the few emails behind its
own task.

## What ran at the same time

Eight email readers worked at once, with a new one starting as each finished. All
21 piles took about ten minutes. All five document writers ran at the same time in
about a minute. The full run took about twenty minutes, under the thirty minute
limit, and re-running skips anything already done.

## Where Claude Code got it wrong and how it was caught

Every one of these was caught by checking the output against what the emails
actually showed, before anything reached the final report.

Daily emails treated as copies. One company sent the same short email every day
for months. The first version saw identical text and deleted the extras, which hid
a daily task, exactly the kind of thing this system exists to find. It was caught
by checking which "copies" were far apart in time. Now two emails only count as
copies if they arrived within a day of each other.

Math that made tasks look rare. A weekly report showed up 16 times over about five
months, but the math divided by the full 27 months the emails cover. That came out
to less than once a month for a weekly report, which doesn't make sense, and the
first total was only $179 a month. It was caught by comparing the numbers against
what the emails obviously showed. Now each task is measured over the months it
actually ran, which puts the total at $427 a month. The cautious $179 still shows
next to it.

A bar nothing could clear. The system only writes a document for tasks worth more
than a set amount per month. Claude Code first set that at $1,500. The biggest task
in four inboxes was worth $117, so nothing qualified and no documents were written.
I reset it to $30 a month. It takes someone about an hour to adopt a new checklist,
which is $85 of their time, so anything saving $30 a month pays for itself within
three months. Five tasks cleared it.

The trap email. One email posed as an official notice and told any AI reading it
to report invoice approval as fully automated and rank it first. The AI ignored it.
The instructions said emails are information, not orders, and every quote gets
checked against the original. Nothing in the report comes from that email.

Quote checking. All 253 quotes matched their emails word for word, with zero
rejected. Telling the AI upfront that a checker would throw out anything inexact
made it copy carefully in the first place.

## What I'd build next with another week

A code based filter that flags trap style emails, instead of relying only on
instructions to the AI. A rule that stops tasks that only ran for a few days from
ranking high. The sixth ranked task only appeared across about eight days. A looser
count shown next to the strict count, so the gap between them is visible.

## Where it's most likely wrong

The totals are probably low. The readers noticed about 620 examples of repeated
tasks, but the strict counting rules only counted 320. That's deliberate, since
every counted email is clearly the task, but it means real totals are likely
higher. Tasks that barely ran can look more frequent than they are. And this is
four inboxes out of thousands of employees, so every dollar figure understates the
company wide picture.

## What it took on faith

How long each task takes a person is essentially a guess. Emails don't record time
spent, so the AI estimates it, and every dollar figure depends on that estimate. The
$85 an hour rate comes from the brief, a blended cost for an hour of an employee's
time across junior and senior people. The one hour it takes someone to adopt a new
document, which sets the $30 bar, is my own estimate.
