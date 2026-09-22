# Nightly Flow-Without-Deal Exception Queue

This is Daren's morning queue for meters that flowed gas with no active Sitara deal covering them. Each row is prefilled by the nightly job so he only has to pick extend, new deal, or add counterparty.

## How it works now, and what changes

Today a scheduler spots the gap by reading a flow report or the UA4 report, looks up the meter's deal history in Sitara by hand, and emails Daren the meter, the flow, and the last deal number. Daren then has to look the meter up again before he can answer.

The nightly job removes the lookup on both ends. It joins metered flow by meter and day against active and evergreen Sitara deals, and for every meter with flow and no covering deal it writes one row below, prefilled from Sitara. Daren opens the queue, reads the suggested action, and picks extend, new deal, or add counterparty. No re-typing, no second Sitara lookup.

## Queue row (one per meter)

| Field | Where it comes from |
|---|---|
| Meter number | The meter on the flow report with no matching deal for the period |
| Period | The month(s) the uncovered flow falls in |
| Flow detail | The day(s) and volume(s) that flowed with no deal, or the average flow per day |
| Last deal number | The most recent Sitara deal ticket tied to this meter |
| Last deal counterparty | The counterparty on that last deal |
| Last deal end date | The date that deal expired or the last month it covered |
| Evergreen flag | Whether the expired deal had the evergreen flag set, yes or no |
| Suggested action | "Extend deal {last deal number} through {period end}" if a prior deal exists and the meter and counterparty look unchanged, otherwise "No prior deal in range, create new" |
| Daren's decision | Extend / New deal / Add counterparty, left blank for Daren |
| New or extended deal number | Left blank until Daren enters the result |
| Date actioned | Left blank until Daren closes the row |

## Example row, filled from the evidence

| Field | Value |
|---|---|
| Meter number | 6387 |
| Period | Dec 00 |
| Flow detail | Avg flow 273/day for Dec, plus a little flow on 1/1 and 1/2 |
| Last deal number | 519467 |
| Last deal counterparty | Duke Energy Trading & Mktg |
| Last deal end date | Nov 00 |
| Evergreen flag | No |
| Suggested action | Extend deal 519467 through Dec 00, or create new if counterparty changed |
| Daren's decision | (blank, pending) |
| New or extended deal number | (blank, pending) |
| Date actioned | (blank, pending) |

## What the queue catches that a person misses

The evergreen flag matters. Deal 156657 expired 3/2000 with no evergreen flag set and no new deal referenced, and the meter still flowed 556 MMBTU on April 1, so the gap sat until Jackie Young caught it by hand and emailed Daren to roll the deal. The nightly join flags this the first night it happens instead of whenever someone next reads the flow report.

Not every row needs Daren to decide alone. Michael Olsen's meter 986315 row shows flow without a deal for Dec and Jan, with deal 502952 good only through November, and he asks whether to extend it or add a new counterparty. The queue carries that same open question as the suggested action so Daren has the same context without a second email.

## Evidence

Source: c3fb116d26be, 2001-01-09, aimee.lannou@enron.com, "Meter 6387 - Dec 00"
Source: 833ea24c1a58, 2000-04-03, jackie.young@enron.com, "980432"
Source: a081ad55db4e, 2001-02-05, michael.olsen@enron.com, "meter 986315"
Source: bd77d5723ce5, 2001-01-02, aimee.lannou@enron.com, "Meter 1517"
Source: 2ccf3e9de5dd, 2000-02-17, jackie.young@enron.com, "98-6892 Overflow"
Source: 8f6a51a09b44, 2000-05-31, jackie.young@enron.com, "98-6892"
Source: 4b18dcf16fe4, 2000-08-29, aimee.lannou@enron.com, "Meter 5593"
Source: d84b70fd3ab2, 2000-01-11, aimee.lannou@enron.com, "UA4 - 1998"
