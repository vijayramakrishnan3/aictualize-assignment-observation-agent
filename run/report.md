# Where Enron loses time

We read 3,240 emails from four Enron employees and found the work they repeat. Every figure below traces to the emails behind it.

**$427 a month** and **5.0 hours a month** across 15 repeated tasks. $179 if averaged over the full two year archive.

## The repeated tasks, biggest first

| Rank | Task | Times a month | Dollars a month | Running total | Document |
|---|---|---|---|---|---|
| 1 | Auto-generated weekly California Capacity Report (o14)<br><small>Weekly California Capacity Report</small> | 3.3 | $117 | $117 | ready |
| 2 | Morning pre-flash reconciliation checklist for congestion and deal entries (o13)<br><small>Reconciling real-time congestion revenue and Enpower deals against settlements</small> | 3.1 | $51 | $169 | ready |
| 3 | Nightly flow-without-deal exception report with a prefilled extension request (o01)<br><small>Extending or creating a Sitara deal ticket for meter flow with no covering deal</small> | 3.0 | $42 | $212 | ready |
| 4 | Prefilled monthly activity and hours survey (o07)<br><small>Monthly activity driver and hours survey for the cost model</small> | 1.6 | $33 | $246 | ready |
| 5 | Routed digital writeoff approval for small Strangers Gas volumes (o02)<br><small>Unaccounted for Gas writeoff approvals for stray meter volumes</small> | 1.8 | $31 | $277 | ready |
| 6 | Auto-forward the Energy Market Report to the West desk list (o15)<br><small>Daily Energy Market Report forward to the West power desk</small> | 7.0 | $29 | $307 |  |
| 7 | Parse nomination attachments straight into the scheduling system (o03)<br><small>Counterparty and plant nominations received as attachments and re-keyed</small> | 1.9 | $18 | $325 |  |
| 8 | Deal entry checklist for book assignment and cross-system links (o11)<br><small>Moving deals between books and linking deal numbers across Tagg, Sitara, SCI, and EOL</small> | 1.3 | $18 | $344 |  |
| 9 | Position notice email template generated from Enpower and CAPS (o12)<br><small>Real-time power desk short and long position notices</small> | 1.0 | $14 | $358 |  |
| 10 | Structured on-call log filled in during the shift (o08)<br><small>Weekend and holiday on-call notes written up after the shift</small> | 0.5 | $13 | $372 |  |
| 11 | Single book, curve, and access request form (o10)<br><small>Trading book, curve, and access setup requests in Tagg, TDS, and RiskTrac</small> | 0.8 | $13 | $386 |  |
| 12 | Standard price verification request with invoice to Sitara match (o06)<br><small>Correcting Sitara deal prices and charges to match invoices and statements</small> | 0.9 | $13 | $399 |  |
| 13 | Coverage notice email template backed by a standing roster (o09)<br><small>Out of office coverage handoff notices</small> | 1.3 | $12 | $412 |  |
| 14 | Open variance log with age, owner, and automatic resend (o05)<br><small>Reconciling volume imbalances and variances with counterparties and interconnects</small> | 0.4 | $7 | $419 |  |
| 15 | Standard procedure for revising nominations on flow drift, plant status, and pipeline cuts (o04)<br><small>Revising nominations when actual flow, plant output, or pipeline cuts change</small> | 1.1 | $7 | $427 |  |

## 1. Auto-generated weekly California Capacity Report (o14)

Michelle Lokay compiles Transwestern and El Paso delivery volumes by point, capacity percentages, and Gas Daily prices into the same report and sends it to the same distribution list every week.

**What it costs.** Happens about 3.3 times a month, takes about 25 minutes each time, so about 1.4 hours and $117 a month.

**What to do about it.** Pull Transwestern and El Paso delivery volumes by point and the Gas Daily prices from their sources each Friday, fill the fixed report template, and send it to the standing list for a quick review before release.

**The proof.**

> Transwestern's average deliveries to California were 945 MMBtu/d (87%), with San Juan lateral throughput at 865 MMBtu/d.  Total East deliveries averaged 525 MMBtu/d.
>
> michelle.lokay@enron.com, 2001-10-26, California Capacity Report for Week of 10/22-10/26. Email `86c805170e90`.

> Transwestern's average deliveries to California were 1122 MMBtu/d (103%), with San Juan lateral throughput at 844 MMBtu/d.  Total East deliveries averaged 270 MMBtu/d.
>
> michelle.lokay@enron.com, 2001-12-14, California Capacity Report for Week of 12/10-12/14. Email `a5fb48e9c2c6`.

**Ready-to-use document.** [o14-auto-generated-weekly-california-capacity-report.md](artifacts/o14-auto-generated-weekly-california-capacity-report.md)

## 2. Morning pre-flash reconciliation checklist for congestion and deal entries (o13)

Bill Williams hand-calculates CAISO congestion relief revenue and checks it against the inc sheet and the flash, and separately compares Enpower deal entries with the PMA sheet, the DPR, and the SAR to get double entries, wrong prices, and counterparty changes corrected by settlements.

**What it costs.** Happens about 3.1 times a month, takes about 12 minutes each time, so about 0.6 hours and $51 a month.

**What to do about it.** Before the morning flash, run a fixed checklist backed by an automated diff, CAISO congestion awards against the inc sheet and CAPS finals, Enpower new deals against the DPR and SAR for duplicates and price outliers, and PMA sheet lines against Enpower deal history, and send settlements one exception list with computed revenue.

**The proof.**

> Darren,
Could you meet with me regarding congestion revenue for 10/05?
We had two wheels that were not in the inc sheet but were awarded by the CAISO and are in finals in CAPS.
>
> bill.williams@enron.com, 2001-10-08, Congestion Revenue for 10/05. Email `4debc9c2f9cc`.

> We had some double deal-entry last night under the ST-WBOM book.  Consequently I zeroed the following deals out this morning after receiving the DPR and running a BOM SAR.
>
> bill.williams@enron.com, 2001-06-29, Adjustments for ST-WBOM for 06/27/01. Email `d2933ba141a4`.

**Ready-to-use document.** [o13-morning-pre-flash-reconciliation-checklist-for-congestion-an.md](artifacts/o13-morning-pre-flash-reconciliation-checklist-for-congestion-an.md)

## 3. Nightly flow-without-deal exception report with a prefilled extension request (o01)

Schedulers and volume management analysts find gas flowing at a meter that no active Sitara deal covers, because the ticket expired, the evergreen flag was never set, or no deal was ever entered, and email Daren Farmer to extend the prior deal or create a new one so the volume can be allocated and paid.

**What it costs.** Happens about 3.0 times a month, takes about 10 minutes each time, so about 0.5 hours and $42 a month.

**What to do about it.** Run a nightly job that joins metered flow by meter and day against active and evergreen Sitara deals, lists every meter with flow and no covering deal, and prefills a request with the meter, the flow dates and volumes, the last deal number, and the counterparty. Daren gets one morning queue and approves an extend or a new deal from it, instead of schedulers finding each gap by eye and writing a fresh email.

**The proof.**

> Daren - meter 6387 for Dec. 00 has flow with no nom.  Avg flow is 273/day.
Last deal associated with this meter was 519467 in Nov. 00 for Duke Energy
Trading & Mktg. There is also a little bit of flow on 1/1 and 1/2.  Please
let me know if you create a new deal or extend the current one.
>
> aimee.lannou@enron.com, 2001-01-09, Meter 6387 - Dec 00. Email `c3fb116d26be`.

> This deal expired 3/2000.  There was no new deal # referenced nor was the
evergreen flag applied.

This meter flowed 556 MMBTU's on April 1, 2000.
>
> jackie.young@enron.com, 2000-04-03, 980432. Email `833ea24c1a58`.

**Ready-to-use document.** [o01-nightly-flow-without-deal-exception-report-with-a-prefilled.md](artifacts/o01-nightly-flow-without-deal-exception-report-with-a-prefilled.md)

## 4. Prefilled monthly activity and hours survey (o07)

Financial Operations sends every RC manager a monthly activity driver survey and hours survey, plus an RC report review, with a hard return date, then sends reminders and follow-up questions to whoever is late or unclear.

**What it costs.** Happens about 1.6 times a month, takes about 15 minutes each time, so about 0.4 hours and $33 a month.

**What to do about it.** Prefill each RC's survey with last month's answers, headcount from the Org Database, and deal and ticket counts from Sitara and Unify, so managers only confirm or correct the exceptions. Track returns in the same sheet and send reminders automatically to RCs that have not responded by the deadline.

**The proof.**

> Please fill out the attached activity
driver survey with May numbers for your RC and return to Shari Mao by end of
day Friday, June 2.
>
> james.scribner@enron.com, 2000-05-30, May Activity Survey. Email `4edc3274cefb`.

> As a reminder, today is the deadline for completion of the OPM Survey.
>
> james.scribner@enron.com, 2000-10-06, OPM Survey. Email `c5bbb0fdf8e5`.

**Ready-to-use document.** [o07-prefilled-monthly-activity-and-hours-survey.md](artifacts/o07-prefilled-monthly-activity-and-hours-survey.md)

## 5. Routed digital writeoff approval for small Strangers Gas volumes (o02)

Clem Cernosek in Logistics finds small volumes booked to the HPL Strangers Gas Contract at meters with no deal for the month, and sends Daren Farmer a per-meter statement asking him to supply a deal or sign and return a printed approval to write the volume off to Unaccounted for Gas.

**What it costs.** Happens about 1.8 times a month, takes about 12 minutes each time, so about 0.4 hours and $31 a month.

**What to do about it.** When volume lands on the HPL Strangers Gas Contract at a meter with no deal, generate a writeoff approval with the meter's flow history and the months checked for deals already attached, and route it for a single approve or supply-a-deal decision. Volumes under an agreed threshold can be written off automatically and reported in a monthly list.

**The proof.**

> Currently, these volumes are being booked under the HPL Strangers Gas
Contract.  Logistics needs either a deal to record these volumes which have
flowed into HPL's Pipeline or  Logistics need approval to writeoff these
volumes to Unaccounted for Gas.
>
> clem.cernosek@enron.com, 2000-08-18, HPL Meter #985355 Brown Common Point. Email `85141cb3f0e2`.

> On 11/30/99, the above meter has recorded flow of 26 Mmbtus.   There were no
deals at this meter during November 1999 or December 1999.  Logistics needs
approval to writeoff these volumes to Unaccounted for Gas.
>
> clem.cernosek@enron.com, 2000-12-14, HPL Meter #980417 HPL/KMID - SEVEN OAKS. Email `b7ed38f73dea`.

**Ready-to-use document.** [o02-routed-digital-writeoff-approval-for-small-strangers-gas-vol.md](artifacts/o02-routed-digital-writeoff-approval-for-small-strangers-gas-vol.md)

## 6. Auto-forward the Energy Market Report to the West desk list (o15)

Jill Chatterton opens the Economic Insight Energy Market Report PDF each trading day and forwards it unchanged to the same West Desk distribution list.

**What it costs.** Happens about 7.0 times a month, takes about 3 minutes each time, so about 0.3 hours and $29 a month.

**What to do about it.** Add a mail rule that forwards the Economic Insight Energy Market Report to the West Desk distribution list the moment it arrives, so no one has to open and forward it each morning.

**The proof.**

> Subject: Energy Market Report - 01/29/02

Energy Market Report
Tuesday, January 29, 2002

*See attached pdf file.
>
> jill.chatterton@enron.com, 2002-01-30, FW: Energy Market Report - 01/29/02. Email `1c3b3d510170`.

> Subject: Energy Market Report - 02/04/02

Energy Market Report
Monday, February 4, 2002

*See attached pdf file.
>
> jill.chatterton@enron.com, 2002-02-05, FW: Energy Market Report - 02/04/02. Email `309449405256`.

## 7. Parse nomination attachments straight into the scheduling system (o03)

Calpine sends a daily and monthly gas nomination as a Word document, TXU sends a daily HPL nomination spreadsheet, and Enron Methanol sends a monthly plant nomination, and a scheduler has to open each one and key the volumes into the scheduling system by hand.

**What it costs.** Happens about 1.9 times a month, takes about 7 minutes each time, so about 0.2 hours and $18 a month.

**What to do about it.** Watch the scheduling inbox for the known nomination senders, parse the Calpine Word documents and TXU spreadsheets for date, point, and volume, and load them into the scheduling system as pending nominations with a variance flag against the prior day. The scheduler reviews and confirms instead of opening each file and re-keying it.

**The proof.**

> - CALPINE DAILY GAS NOMINATION 1.doc
>
> rickya@calpine.com, 1999-12-14, Calpine Daily Gas Nomination. Email `e9273e5803f6`.

> (See attached file: hpl1228.xls)
>
> timpowell@txu.com, 1999-12-27, HPL Nominations for December 28, 1999. Email `b582989db190`.

## 8. Deal entry checklist for book assignment and cross-system links (o11)

The desk flags deals that sit in the wrong book and must be flipped into FT-US/CAND-ERMS or, after the bankruptcy filing, moved into the bankruptcy books, and separately chases missing cross-references so each deal carries its Tagg, Sitara, SCI, and EOL numbers.

**What it costs.** Happens about 1.3 times a month, takes about 10 minutes each time, so about 0.2 hours and $18 a month.

**What to do about it.** Add a checklist to deal entry that confirms the correct book for the counterparty and entity and that the Tagg, Sitara, SCI, and EOL numbers are cross-entered, backed by a nightly report of deals in the wrong book or with an empty link field sent to the book admin.

**The proof.**

> Please remember to link up all deals.  By this, I mean Tagg numbers in
Sitara, Sitara numbers in Tagg, Tagg numbers in SCI, and especially EOL
numbers in Tagg.
>
> darron.giron@enron.com, 2000-10-17, Reminder. Email `3bff55c13fd2`.

> I've come across this deal that needs to be flipped right away.
This deal is in the MGMT-WEST book with Aquila Canada Corp. and
ENA.  It needs to be in the FT-US/CAND-ERMS book settling between
ECC and Aquila Canada Corp.
>
> darron.giron@enron.com, 2001-03-05, Re: Q50979.1. Email `c31f511e108f`.

## 9. Position notice email template generated from Enpower and CAPS (o12)

Bill Williams emails the real-time group whenever the desk is short or long for an upcoming day, with megawatts, prices, delivery points, and the book, and traders then buy or sell and key the deals into Enpower and CAPS.

**What it costs.** Happens about 1.0 times a month, takes about 10 minutes each time, so about 0.2 hours and $14 a month.

**What to do about it.** Pull the open short and long positions by book, point, hour ending, and price from Enpower and CAPS and generate the group notice in a fixed format, with the matching deal entries staged for the trader to confirm.

**The proof.**

> We are short 50 mws in SP-15 for HE 7-22 on Wednesday at $61.44.  Please purchase this 50 mws under ST-WBOM.
>
> bill.williams@enron.com, 2001-07-11, Short for 07/11/01 at SP-15. Email `3593d0497185`.

> We are long 25 mws on peak for 06/27/01 in SP-15.  This should be in CAPS under ST-WBOM, deals should be under ST-WBOM in Enpower as well.
>
> bill.williams@enron.com, 2001-06-27, Length for Wednesday. Email `affa2dd11baa`.

## 10. Structured on-call log filled in during the shift (o08)

The scheduler who covered the weekend or holiday on-call shift writes a call-by-call narrative of gas control pages, cuts, and well issues and emails it to the desk on Monday, and recipients then check each meter it mentions against the system.

**What it costs.** Happens about 0.5 times a month, takes about 20 minutes each time, so about 0.2 hours and $13 a month.

**What to do about it.** Give the on-call scheduler a shared log with one row per call, time, caller, meter, action taken, and system updated, filled in as calls come in. The Monday note is generated from the log and each meter row links to its system entry so recipients verify by exception instead of reading a narrative.

**The proof.**

> Friday 3/23 - Received a page from Silver in Gas Control at 8:00 pm regarding the Gulf Plains Plant.  They were cut into another pipeline (Tennessee), and wanted to overdeliver to us by 10M for the night.
>
> mary.poorman@enron.com, 2001-03-26, On Call Notes. Email `afb2990b7e07`.

> Attached are the notes from this weekend.
>
> robert.lloyd@enron.com, 2000-08-14, On Call Notes for Weekend Dated ; August 12th thru 13th. Email `0c4428ce9278`.

## 11. Single book, curve, and access request form (o10)

Desk controllers and traders email the Tagg, TDS, and RiskTrac administrators to create books and curves, map books to traders and EOL products, update the Book Admin list, and grant access, and during the Netco and UBS transition they rebuilt access matrices and curve mappings and re-pointed macros after each rename.

**What it costs.** Happens about 0.8 times a month, takes about 12 minutes each time, so about 0.2 hours and $13 a month.

**What to do about it.** Replace ad hoc emails with one request form that captures region, entity, book or curve name, trader, mapped books, and users, generates names by the naming convention, and routes to the admin who owns that system. Keep the trader to book to product mapping in one table that macros and hedgestrips read, so a rename updates everywhere at once.

**The proof.**

> I need to have FT-DENVER set up in TDS.  The trader is Jay Reitmeyer.  There
are two Tagg books that need to be mapped to this:  FT-DENVER and
INTRA-DENVER.
>
> darron.giron@enron.com, 2001-01-11, Denver in TDS. Email `460269329baa`.

> Please add Financial and Control group to these book requests if they are missing.  We would like for everyone to have access to these books that is on that matrix we sent you.  Thanks.
>
> m..love@enron.com, 2002-01-04, RE: new book req. Email `1881cb19a399`.

## 12. Standard price verification request with invoice to Sitara match (o06)

Settlements and counterparties find a price, rate, or demand charge in Sitara that does not match the counterparty invoice, confirmation, or actualized pipeline statement, and email the desk to verify the right figure and re-key it into Sitara, including a standing monthly EnerVest rate change.

**What it costs.** Happens about 0.9 times a month, takes about 10 minutes each time, so about 0.2 hours and $13 a month.

**What to do about it.** Match each incoming counterparty invoice or confirmation line against the Sitara deal price and flag mismatches over a small threshold, then send one standard verification email with the deal number, date, point, invoiced price, and Sitara price to the responsible trader. A recurring rate like the EnerVest monthly price is loaded through an upload instead of an email per month.

**The proof.**

> Daren, Conoco invoiced HPL at $5.87 for 03/23 at PGEV/Waha and deal ticket 685350 shows $4.87.  Can you confirm the price?  Thanks.
>
> cynthia.hakemack@enron.com, 2001-04-12, HPL/Conoco - Teco Waha 03/23/01 Purchase. Email `1e5f47d1b14d`.

> As usual, could you please change rate on S# 27239 for 12/00 production to
$5.811329?
>
> darron.giron@enron.com, 2001-01-23, Re: Enervest for 12/00. Email `6bef9c0df335`.

## 13. Coverage notice email template backed by a standing roster (o09)

Before a vacation or absence, each scheduler writes a note naming who covers their meters, pipelines, or accounts, with extensions and pager numbers, and sends it to the desk.

**What it costs.** Happens about 1.3 times a month, takes about 7 minutes each time, so about 0.1 hours and $12 a month.

**What to do about it.** Keep a standing roster of each scheduler's meters, pipelines, and default backups with extensions and pagers, and generate the out of office notice from it so the sender only enters dates and confirms the backup.

**The proof.**

> I will be on vacation from Thursday 5/10 thru Wednesday 5/16. Tom Acton will be my back up  713-571-3256, pager 713-707-3527 and Bob Cotten will do the NNGB (Black Marlin) and help Tom.
>
> carlos.rodriguez@enron.com, 2001-05-09, Out of the office. Email `dabe5d15b570`.

> I will be on vacation Friday, June 2 through  Monday, June 12.  In my absence
please direct any questions or issues to these people.
>
> aimee.lannou@enron.com, 2000-05-31, Vacation. Email `061a91d5ed81`.

## 14. Open variance log with age, owner, and automatic resend (o05)

HPL Logistics and Transwestern staff chase volume, allocation, and imbalance differences between MOPS and POPS, and with counterparties and interconnecting pipelines such as PG&E Texas, TXU Lone Star, Hesco, and El Paso at Mojave, by re-sending allocation data, spreadsheets, and faxes until each variance closes.

**What it costs.** Happens about 0.4 times a month, takes about 15 minutes each time, so about 0.1 hours and $7 a month.

**What to do about it.** Keep every open interconnect or counterparty variance in one log with the meter, contract, amount, owner, and date opened, and have it resend the allocation data to the counterparty contact and escalate internally once an item passes a set age. A daily MOPS to POPS diff feeds new variances into the log the day they appear.

**The proof.**

> this issue is still unresolved as well as a 6,000 variance on
contract 5098-695.
>
> sherlyn.schumack@enron.com, 2000-03-28, PG&E Texas contract 5095-037 for 2/00. Email `a6d7e21df5fe`.

> I have sent several emails, faxed the daily's and left
voice messages, but have not received any updates to this issue.
>
> sherlyn.schumack@enron.com, 2000-05-22, Re: PG&E Texas contract 5098-695 for 2/00. Email `9627c322fee7`.

## 15. Standard procedure for revising nominations on flow drift, plant status, and pipeline cuts (o04)

Schedulers revise nominated volumes by hand when a well or customer's metered flow drifts, when the Methanol or MTBE plant goes down or ramps up, or when a pipeline such as El Paso on Oasis cuts volumes, each announced in a prose email that someone reads and acts on.

**What it costs.** Happens about 1.1 times a month, takes about 5 minutes each time, so about 0.1 hours and $7 a month.

**What to do about it.** Write one procedure that says who revises the nomination for each trigger, a meter drifting past a set tolerance, a plant outage or restart notice, or a pipeline cut confirmation, what system entry is made, and what confirmation goes back. Pair it with a daily flag of meters whose flow deviates from the nomination beyond the tolerance so drift is caught before month end.

**The proof.**

> want to look at getting this nom revised for the rest of the month.
>
> lauri.allen@enron.com, 2000-02-16, Meter 9682. Email `6bbe1ee3b5aa`.

> The MTBE plant went down about 1 a.m. on Saturday morning, May 20, as a
result of power failure.
>
> maritta.mullet@enron.com, 2000-05-22, MTBE PLANT SHUT-DOWN. Email `6fcfcde2f76c`.

## How the numbers were calculated

Code parsed, deduplicated, and dated every email. A model read the archive in batches and proposed the repeated tasks, each with word for word quotes as evidence. Every quote was checked as an exact substring of the email it cites, and quotes that failed were dropped rather than repaired. For each task the model proposed a match rule (a subject pattern, body keywords, or a sender list) and code counted the non-duplicate emails that match it. Times a month is that count divided by the task's active window, the months between its first and last matching email, floored at one. Hours a month is times a month multiplied by the minutes saved each time, divided by 60. Dollars a month is hours multiplied by the $85 blended rate. The minutes per time is a judgment with no ground truth in an email archive, so everything downstream of it is arithmetic on an estimate.

Each process is rated over its own active window, first matching message to last. The conservative figure divides by the full archive span instead.

Documents are drafted for every task worth $30 a month or more. Below that, the effort of adopting a new document outweighs what it saves in the first quarter.

| Measure | Value |
|---|---|
| Emails in the archive | 3,240 |
| Unique emails | 3,198 |
| Duplicates removed | 42 |
| Undated emails | 3 |
| Archive span | 27.4 months |
| Blended rate | $85 per hour |
| Document threshold | $30 per month |
| Hours per month, active windows | 5.0 |
| Dollars per month, active windows | $427 |
| Hours per month, full archive span | 2.1 |
| Dollars per month, full archive span | $179 |

Generated 2026-09-22T20:50:46Z. Corpus hash `dcf6d96bd91e76a7baee9487c4d981fc81042c71`.

### The math for each task

**1. Auto-generated weekly California Capacity Report (o14)**

- 16 matched messages, 2001-10-26 to 2002-03-22 = 4.8 active months
- 16 / 4.8 = 3.3 instances per month
- 3.3 instances x 25 minutes / 60 = 1.4 hours per month
- 1.4 hours x $85 = $117 per month
- Over the full 27.4 month archive span: 0.6 instances, 0.2 hours, $21 per month
- Match rule: body contains any of "average deliveries to california", "san juan lateral throughput"

**2. Morning pre-flash reconciliation checklist for congestion and deal entries (o13)**

- 14 matched messages, 2001-06-29 to 2001-11-15 = 4.6 active months
- 14 / 4.6 = 3.1 instances per month
- 3.1 instances x 12 minutes / 60 = 0.6 hours per month
- 0.6 hours x $85 = $52 per month
- Over the full 27.4 month archive span: 0.5 instances, 0.1 hours, $9 per month
- Match rule: body contains any of "congestion revenue", "congestion that we relieved", "pma sheet", "bom sar", "new deal summary"

**3. Nightly flow-without-deal exception report with a prefilled extension request (o01)**

- 68 matched messages, 1999-12-27 to 2001-11-08 = 22.4 active months
- 68 / 22.4 = 3.0 instances per month
- 3.0 instances x 10 minutes / 60 = 0.5 hours per month
- 0.5 hours x $85 = $43 per month
- Over the full 27.4 month archive span: 2.5 instances, 0.4 hours, $35 per month
- Match rule: body contains any of "extend sitara deal", "extend deal", "extend the deal", "extend this deal", "extend that deal", "flow with no nom", "without a nom", "without a deal", "but there is no deal", "evergreen flag", "ua4"

**4. Prefilled monthly activity and hours survey (o07)**

- 12 matched messages, 2000-02-22 to 2000-10-10 = 7.6 active months
- 12 / 7.6 = 1.6 instances per month
- 1.6 instances x 15 minutes / 60 = 0.4 hours per month
- 0.4 hours x $85 = $34 per month
- Over the full 27.4 month archive span: 0.4 instances, 0.1 hours, $9 per month
- Match rule: body contains any of "driver survey", "opm survey", "survey for each position", "attached survey", "review your rc reports"

**5. Routed digital writeoff approval for small Strangers Gas volumes (o02)**

- 36 matched messages, 2000-03-11 to 2001-10-31 = 19.7 active months
- 36 / 19.7 = 1.8 instances per month
- 1.8 instances x 12 minutes / 60 = 0.4 hours per month
- 0.4 hours x $85 = $31 per month
- Over the full 27.4 month archive span: 1.3 instances, 0.3 hours, $22 per month
- Match rule: body contains any of "writeoff", "strangers gas"

**6. Auto-forward the Energy Market Report to the West desk list (o15)**

- 7 matched messages, 2002-01-29 to 2002-02-06 = 1.0 active months
- 7 / 1.0 = 7.0 instances per month
- 7.0 instances x 3 minutes / 60 = 0.3 hours per month
- 0.3 hours x $85 = $30 per month
- Over the full 27.4 month archive span: 0.3 instances, 0.0 hours, $1 per month
- Match rule: body contains any of "energy market report"

**7. Parse nomination attachments straight into the scheduling system (o03)**

- 30 matched messages, 1999-12-14 to 2001-04-19 = 16.2 active months
- 30 / 16.2 = 1.9 instances per month
- 1.9 instances x 7 minutes / 60 = 0.2 hours per month
- 0.2 hours x $85 = $18 per month
- Over the full 27.4 month archive span: 1.1 instances, 0.1 hours, $11 per month
- Match rule: body contains any of "gas nomination 1.doc", "calpine monthly gas", "nominates the following requirements", "(see attached file: hpl"

**8. Deal entry checklist for book assignment and cross-system links (o11)**

- 23 matched messages, 2000-08-10 to 2002-01-31 = 17.7 active months
- 23 / 17.7 = 1.3 instances per month
- 1.3 instances x 10 minutes / 60 = 0.2 hours per month
- 0.2 hours x $85 = $18 per month
- Over the full 27.4 month archive span: 0.8 instances, 0.1 hours, $12 per month
- Match rule: body contains any of "flipped", "flip these", "bankruptcy book", "link field", "link up all deals"

**9. Position notice email template generated from Enpower and CAPS (o12)**

- 20 matched messages, 2000-03-22 to 2001-11-14 = 19.8 active months
- 20 / 19.8 = 1.0 instances per month
- 1.0 instances x 10 minutes / 60 = 0.2 hours per month
- 0.2 hours x $85 = $14 per month
- Over the full 27.4 month archive span: 0.7 instances, 0.1 hours, $10 per month
- Match rule: body contains any of "we are short", "we are long", "we will be short", "we will be long"

**10. Structured on-call log filled in during the shift (o08)**

- 9 matched messages, 2000-01-17 to 2001-07-28 = 18.3 active months
- 9 / 18.3 = 0.5 instances per month
- 0.5 instances x 20 minutes / 60 = 0.2 hours per month
- 0.2 hours x $85 = $14 per month
- Over the full 27.4 month archive span: 0.3 instances, 0.1 hours, $9 per month
- Match rule: body contains any of "notes from this weekend", "on-call notes", "received a page from", "notified by gas control", "received a call from"

**11. Single book, curve, and access request form (o10)**

- 18 matched messages, 2000-03-28 to 2002-02-04 = 22.3 active months
- 18 / 22.3 = 0.8 instances per month
- 0.8 instances x 12 minutes / 60 = 0.2 hours per month
- 0.2 hours x $85 = $14 per month
- Over the full 27.4 month archive span: 0.7 instances, 0.1 hours, $11 per month
- Match rule: body contains any of "book to tagg", "added to tagg", "set up in tds", "book admin list", "book requests", "separate books", "eol product", "mapped to curves", "copy physical macro", "refresh booklist"

**12. Standard price verification request with invoice to Sitara match (o06)**

- 13 matched messages, 2000-06-22 to 2001-08-17 = 13.8 active months
- 13 / 13.8 = 0.9 instances per month
- 0.9 instances x 10 minutes / 60 = 0.2 hours per month
- 0.2 hours x $85 = $13 per month
- Over the full 27.4 month archive span: 0.5 instances, 0.1 hours, $7 per month
- Match rule: body contains any of "invoiced hpl", "confirm the pricing", "verify the pricing", "confirm the price", "changed in sitara", "sitara demand charges", "change rate on", "the deal in sitara"

**13. Coverage notice email template backed by a standing roster (o09)**

- 33 matched messages, 1999-12-15 to 2002-01-25 = 25.4 active months
- 33 / 25.4 = 1.3 instances per month
- 1.3 instances x 7 minutes / 60 = 0.1 hours per month
- 0.1 hours x $85 = $13 per month
- Over the full 27.4 month archive span: 1.2 instances, 0.1 hours, $12 per month
- Match rule: body contains any of "i will be on vacation", "i will be out on vacation", "i will be out of the", "in my absence", "backing me up", "my back up"

**14. Open variance log with age, owner, and automatic resend (o05)**

- 8 matched messages, 2000-03-21 to 2002-01-24 = 22.2 active months
- 8 / 22.2 = 0.4 instances per month
- 0.4 instances x 15 minutes / 60 = 0.1 hours per month
- 0.1 hours x $85 = $8 per month
- Over the full 27.4 month archive span: 0.3 instances, 0.1 hours, $6 per month
- Match rule: body contains any of "imbalance numbers", "variance on", "mojave interconnect", "mirrored meters", "shortpaid", "still unresolved", "faxed the daily"

**15. Standard procedure for revising nominations on flow drift, plant status, and pipeline cuts (o04)**

- 13 matched messages, 2000-01-21 to 2001-02-01 = 12.4 active months
- 13 / 12.4 = 1.1 instances per month
- 1.1 instances x 5 minutes / 60 = 0.1 hours per month
- 0.1 hours x $85 = $7 per month
- Over the full 27.4 month archive span: 0.5 instances, 0.0 hours, $3 per month
- Match rule: body contains any of "nom revised", "plant went down", "making spec product", "full production", "was cut:", "(cut of", "changed the volume"

### The processes behind the tasks

**Extending or creating a Sitara deal ticket for meter flow with no covering deal (p01)**

Schedulers and volume management analysts find gas flowing at a meter that no active Sitara deal covers, because the ticket expired, the evergreen flag was never set, or no deal was ever entered, and email Daren Farmer to extend the prior deal or create a new one so the volume can be allocated and paid. 15 minutes because each request means pulling the meter's deal history in Sitara, confirming the date range, and re-entering or extending the ticket, which the batch estimates put between 10 and 20.

Where it gets stuck. Nothing links measured flow to an active deal, so every gap is found by a person reading a flow report or the UA4 report and then waits in Daren's inbox until he traces the meter and re-keys the ticket.

Who does it. daren.farmer@enron.com, jackie.young@enron.com, aimee.lannou@enron.com, mary.poorman@enron.com, charlotte.hawkins@enron.com, stella.morris@enron.com, michael.olsen@enron.com

Matched 68 messages, 1999-12-27 to 2001-11-08, 22.4 active months. 3.0 per month over the active window, 2.5 per month over the full 27.4 month archive span. Rule: body contains any of "extend sitara deal", "extend deal", "extend the deal", "extend this deal", "extend that deal", "flow with no nom", "without a nom", "without a deal", "but there is no deal", "evergreen flag", "ua4"

> Can you please extend sitara deal ticket 16888 to the 15th?  14 dec. flowed
on this day.
>
> jackie.young@enron.com, 2000-02-17. Email `2ccf3e9de5dd`.

> This deal expired 3/2000.  There was no new deal # referenced nor was the
evergreen flag applied.

This meter flowed 556 MMBTU's on April 1, 2000.
>
> jackie.young@enron.com, 2000-04-03. Email `833ea24c1a58`.

> 98-6892 has a spill-over of 15 decatherms for 5/24/2000.  Can you please
extend deal ticket 274443 for cover this?
>
> jackie.young@enron.com, 2000-05-31. Email `8f6a51a09b44`.

> Daren - canyou get a deal set up for meter 5593 for Aug 00?  There has been a
small amount of flow everyday.
>
> aimee.lannou@enron.com, 2000-08-29. Email `4b18dcf16fe4`.

> Daren - meter 1517 has a nom of 0/day for Jan.  It flowed about 5.400 on day
1. This is a valid flow.  Could you please extend the deal from Dec. (deal #
506192) or create a new one?  Thanks.
>
> aimee.lannou@enron.com, 2001-01-02. Email `bd77d5723ce5`.

> Daren - meter 6387 for Dec. 00 has flow with no nom.  Avg flow is 273/day.
Last deal associated with this meter was 519467 in Nov. 00 for Duke Energy
Trading & Mktg. There is also a little bit of flow on 1/1 and 1/2.  Please
let me know if you create a new deal or extend the current one.
>
> aimee.lannou@enron.com, 2001-01-09. Email `c3fb116d26be`.

> For Dec. and Jan. production there are flow volumes without a deal.  Deal
502952 was good for November.  Do you want to extend this deal or should
there be another counterparty added?
>
> michael.olsen@enron.com, 2001-02-05. Email `a081ad55db4e`.

> We are currently working to clear some UA4 issues for 1998.
>
> aimee.lannou@enron.com, 2000-01-11. Email `d84b70fd3ab2`.

**Unaccounted for Gas writeoff approvals for stray meter volumes (p02)**

Clem Cernosek in Logistics finds small volumes booked to the HPL Strangers Gas Contract at meters with no deal for the month, and sends Daren Farmer a per-meter statement asking him to supply a deal or sign and return a printed approval to write the volume off to Unaccounted for Gas. 20 minutes because each case needs the meter's flow history pulled, checked against Sitara, and a paper form signed and returned, and the two batch estimates were 15 and 20.

Where it gets stuck. Each stray volume is handled as its own case through a printed sign-and-return form, often months after the flow, instead of a threshold rule or a routed digital approval.

Who does it. clem.cernosek@enron.com, daren.farmer@enron.com

Matched 36 messages, 2000-03-11 to 2001-10-31, 19.7 active months. 1.8 per month over the active window, 1.3 per month over the full 27.4 month archive span. Rule: body contains any of "writeoff", "strangers gas"

> Currently, these volumes are being booked under the HPL Strangers Gas
Contract.  Logistics needs either a deal to record these volumes which have
flowed into HPL's Pipeline or  Logistics need approval to writeoff these
volumes to Unaccounted for Gas.
>
> clem.cernosek@enron.com, 2000-08-18. Email `85141cb3f0e2`.

> Currently, this
volume is booked to the HPL Strangers Gas Contract.  Logistics needs approval
to writeoff this volume to Unaccounted for Gas Loss.
>
> clem.cernosek@enron.com, 2000-11-07. Email `36912cbd53cf`.

> On 11/30/99, the above meter has recorded flow of 26 Mmbtus.   There were no
deals at this meter during November 1999 or December 1999.  Logistics needs
approval to writeoff these volumes to Unaccounted for Gas.
>
> clem.cernosek@enron.com, 2000-12-14. Email `b7ed38f73dea`.

> On 4/18/99, the above meter recorded flow of 101 Mmbtus.  There were no deals
at this meter during  March, April, or May 1999.   Logistics needs approval
to writeoff these volumes to Unaccounted for Gas.
>
> clem.cernosek@enron.com, 2000-12-14. Email `c4e883d4c147`.

**Counterparty and plant nominations received as attachments and re-keyed (p03)**

Calpine sends a daily and monthly gas nomination as a Word document, TXU sends a daily HPL nomination spreadsheet, and Enron Methanol sends a monthly plant nomination, and a scheduler has to open each one and key the volumes into the scheduling system by hand. 10 minutes because the email body carries no usable data, so each nomination is opened, read, and re-entered, and the batch estimates ranged from 5 to 15.

Where it gets stuck. Nominations arrive only as attached documents or prose, sometimes after a phone call that already said the same thing, so every one is opened and re-keyed into the scheduling system instead of flowing in.

Who does it. rickya@calpine.com, timpowell@txu.com, michael.mitcham@enron.com, robert.lloyd@enron.com, aimee.lannou@enron.com, daren.farmer@enron.com

Matched 30 messages, 1999-12-14 to 2001-04-19, 16.2 active months. 1.9 per month over the active window, 1.1 per month over the full 27.4 month archive span. Rule: body contains any of "gas nomination 1.doc", "calpine monthly gas", "nominates the following requirements", "(see attached file: hpl"

> - CALPINE DAILY GAS NOMINATION 1.doc
>
> rickya@calpine.com, 1999-12-14. Email `e9273e5803f6`.

> - CALPINE MONTHLY GAS NOMINATION___.doc
>
> rickya@calpine.com, 1999-12-28. Email `87fa4d84ce2d`.

> (See attached file: hpl1228.xls)
>
> timpowell@txu.com, 1999-12-27. Email `b582989db190`.

> (See attached file: hpl0118.xls)
>
> timpowell@txu.com, 2000-01-17. Email `1bf6aa982b2a`.

> Enron Methanol Company nominates the following requirements for the Methanol
>
> michael.mitcham@enron.com, 1999-12-21. Email `46ffd7ec1d8f`.

> As we spoke about by phone, here is the nomination, Thanks. <<CALPINE DAILY
GAS NOMINATION 1.doc>>
>
> rickya@calpine.com, 2000-04-10. Email `6f8f1a18931d`.

> <<CALPINE DAILY GAS NOMINATION 1.doc>>

RICKY A. ARCHER
Fuel Supply
>
> rickya@calpine.com, 2000-08-10. Email `1291e4d7e37d`.

**Revising nominations when actual flow, plant output, or pipeline cuts change (p04)**

Schedulers revise nominated volumes by hand when a well or customer's metered flow drifts, when the Methanol or MTBE plant goes down or ramps up, or when a pipeline such as El Paso on Oasis cuts volumes, each announced in a prose email that someone reads and acts on. 10 minutes because each change is a quick read and a manual volume edit, which is what every batch estimate settled on.

Where it gets stuck. There is no feed from wells, plants, or pipeline confirmations into the nomination system, so a person has to notice the change, relay it by email, and re-key the nomination or MOPS estimate.

Who does it. daren.farmer@enron.com, tom.acton@enron.com, lauri.allen@enron.com, maritta.mullet@enron.com, mark.mccoy@enron.com

Matched 13 messages, 2000-01-21 to 2001-02-01, 12.4 active months. 1.1 per month over the active window, 0.5 per month over the full 27.4 month archive span. Rule: body contains any of "nom revised", "plant went down", "making spec product", "full production", "was cut:", "(cut of", "changed the volume"

> want to look at getting this nom revised for the rest of the month.
>
> lauri.allen@enron.com, 2000-02-16. Email `6bbe1ee3b5aa`.

> Daren I since you were at the offsite I went ahead and changed the volume
down to 12,400 from 13,000.
>
> tom.acton@enron.com, 2000-02-16. Email `b44260517fee`.

> The Methanol Plant is up and making spec product.  Rates will be increased to
full rates on Thursday, March 30, if oxygen is available.
>
> maritta.mullet@enron.com, 2000-03-27. Email `820e9fcc6f02`.

> The MTBE plant went down about 1 a.m. on Saturday morning, May 20, as a
result of power failure.
>
> maritta.mullet@enron.com, 2000-05-22. Email `6fcfcde2f76c`.

> Some of the gas purchased from Dynegy on gas day 6/6 was cut:

9B5P

662 cut to 599
10,000 cut to 9,061
>
> mark.mccoy@enron.com, 2000-06-07. Email `ee63969afbb2`.

> 6/8/00
9J49  Exxon 6,500 cut to 6,016
(cut of 484)
202K
Oasis kept delivery whole
>
> mark.mccoy@enron.com, 2000-06-13. Email `eb79a4d126dc`.

**Reconciling volume imbalances and variances with counterparties and interconnects (p05)**

HPL Logistics and Transwestern staff chase volume, allocation, and imbalance differences between MOPS and POPS, and with counterparties and interconnecting pipelines such as PG&E Texas, TXU Lone Star, Hesco, and El Paso at Mojave, by re-sending allocation data, spreadsheets, and faxes until each variance closes. 30 minutes because each round means pulling records from two systems, contacting the counterparty, and reallocating by hand, set between the 15 minute El Paso exchanges and the 45 minute MOPS and POPS investigations.

Where it gets stuck. Nominated and actual volumes are not diffed automatically, so variances surface weeks or months later and sit open with no owner or deadline while one side keeps re-sending the same data.

Who does it. sherlyn.schumack@enron.com, stacey.neuweiler@enron.com, charlotte.hawkins@enron.com, daren.farmer@enron.com, michelle.lokay@enron.com, susan.mayher@elpaso.com

Matched 8 messages, 2000-03-21 to 2002-01-24, 22.2 active months. 0.4 per month over the active window, 0.3 per month over the full 27.4 month archive span. Rule: body contains any of "imbalance numbers", "variance on", "mojave interconnect", "mirrored meters", "shortpaid", "still unresolved", "faxed the daily"

> Daren you are correct in that this was only in MOPS for the 26th.  It was
>
> charlotte.hawkins@enron.com, 2000-02-14. Email `2e3fb8bd2b59`.

> In reviewing some of the imbalance numbers, I discovered that Valero Texoma
>
> lauri.allen@enron.com, 2000-03-21. Email `d98a0a9c820d`.

> We do have a problem with some of our mirrored meters.  When MIPS receives an
>
> charlotte.hawkins@enron.com, 2000-03-21. Email `6645ccf1e244`.

> this issue is still unresolved as well as a 6,000 variance on
contract 5098-695.
>
> sherlyn.schumack@enron.com, 2000-03-28. Email `a6d7e21df5fe`.

> I have sent several emails, faxed the daily's and left
voice messages, but have not received any updates to this issue.
>
> sherlyn.schumack@enron.com, 2000-05-22. Email `9627c322fee7`.

> I am working on clearing an old TXU Lone Star/Gas Distribution balance from
8/99 and 9/99.  We originally billed TXU on nominated quantities and they
have shortpaid us due to meter adjustments.
>
> rebecca.griffin@enron.com, 2000-12-07. Email `b27f5fb123c8`.

> Here is a spreadsheet that will hopefully help with reconciling the Mojave interconnect.  Let's talk soon.
>
> michelle.lokay@enron.com, 2002-01-24. Email `4252f367e060`.

**Correcting Sitara deal prices and charges to match invoices and statements (p06)**

Settlements and counterparties find a price, rate, or demand charge in Sitara that does not match the counterparty invoice, confirmation, or actualized pipeline statement, and email the desk to verify the right figure and re-key it into Sitara, including a standing monthly EnerVest rate change. 15 minutes because each fix is a deal lookup, a comparison against the source document, and a manual edit plus confirmation, which four of the five batch estimates chose.

Where it gets stuck. The correct number already exists on the invoice or in settlements' spreadsheet, but nothing compares it to Sitara, so each mismatch is spotted by eye, emailed over, and re-typed before the invoice can go out.

Who does it. katherine.herrera@enron.com, cynthia.hakemack@enron.com, megan.parker@enron.com, kevin.drachenberg@enron.com, tricia.truong@enron.com, daren.farmer@enron.com, darron.giron@enron.com

Matched 13 messages, 2000-06-22 to 2001-08-17, 13.8 active months. 0.9 per month over the active window, 0.5 per month over the full 27.4 month archive span. Rule: body contains any of "invoiced hpl", "confirm the pricing", "verify the pricing", "confirm the price", "changed in sitara", "sitara demand charges", "change rate on", "the deal in sitara"

> Daren, Conoco invoiced HPL at $5.87 for 03/23 at PGEV/Waha and deal ticket 685350 shows $4.87.  Can you confirm the price?  Thanks.
>
> cynthia.hakemack@enron.com, 2001-04-12. Email `1e5f47d1b14d`.

> Daren, BP invoiced HPL at $4.955 for the deal below, and Sitara shows $4.95.  Can you please verify the pricing?  Thanks.
>
> cynthia.hakemack@enron.com, 2001-05-07. Email `6b8515f6426a`.

> Please confirm the pricing for TXU Gas deal #646679 for March 8, 2001.  We are currently showing the Katy Hub Gas Daily Midpoint for that day, but TXU shows the Waha Hub Gas Daily Midpoint.
>
> rebecca.griffin@enron.com, 2001-04-24. Email `2dd4a40887e5`.

> For June, I need a couple of things changed in Sitara:
Deal 819592 - the commodity price needs to be 3.6318
>
> valerie.vela@enron.com, 2001-08-17. Email `c69b464ea2e0`.

> Please update the Sitara demand charges on the following deals to match the
actualized pipeline statements:

#131389 -    $172,588.94
#131405 - $1,297,419.61
>
> darron.giron@enron.com, 2000-07-18. Email `37caf7d83d0e`.

> Could you please change rate on the above Sitara to $4.878216 for Oct. 00
production?
>
> darron.giron@enron.com, 2000-11-21. Email `cf856acdac89`.

> Can you please
update the deal in Sitara to reflect the correct price for 03/01?
>
> darron.giron@enron.com, 2001-04-09. Email `d00a08ab5c7c`.

**Monthly activity driver and hours survey for the cost model (p07)**

Financial Operations sends every RC manager a monthly activity driver survey and hours survey, plus an RC report review, with a hard return date, then sends reminders and follow-up questions to whoever is late or unclear. 20 minutes because each response means estimating the team's hours and driver counts and filling the spreadsheet by hand, the middle of the 15 to 30 minute batch estimates.

Where it gets stuck. Nothing carries forward from last month or from system activity counts, so every manager reconstructs hours and drivers from memory and Financial Operations chases each late response individually.

Who does it. shari.mao@enron.com, james.scribner@enron.com, lisa.cousino@enron.com, suzanne.nicholie@enron.com, daren.farmer@enron.com

Matched 12 messages, 2000-02-22 to 2000-10-10, 7.6 active months. 1.6 per month over the active window, 0.4 per month over the full 27.4 month archive span. Rule: body contains any of "driver survey", "opm survey", "survey for each position", "attached survey", "review your rc reports"

> For the month of March, please provide a
completed "Hours" survey for each position within your group.  This survey
will collect the  time your team spent on performing their activities in the
month of March.
>
> shari.mao@enron.com, 2000-03-31. Email `12a66104da87`.

> Please fill out the attached activity
driver survey with May numbers for your RC and return to Shari Mao by end of
day Friday, June 2.
>
> james.scribner@enron.com, 2000-05-30. Email `4edc3274cefb`.

> Please fill out the attached activity
driver survey with June numbers for your RC and return to Shari Mao by end of
day Friday, July 7,
>
> shari.mao@enron.com, 2000-06-27. Email `d8a0b9665f4a`.

> Please fill
out the attached activity driver survey with July numbers for your RC and
return to Shari Mao by end of day Friday, August 11.
>
> james.scribner@enron.com, 2000-08-03. Email `fdf8e5c374e3`.

> As a reminder, today is the deadline for completion of the OPM Survey.
>
> james.scribner@enron.com, 2000-10-06. Email `c5bbb0fdf8e5`.

> One more thing I need for each of you to do.  Please review your RC reports
>
> lisa.cousino@enron.com, 2000-02-22. Email `aa9da649ffc5`.

> We are starting to collect data for April.  The attached survey drives your
costs from your activities to the commercial teams.
>
> shari.mao@enron.com, 2000-05-02. Email `733b7d6922f6`.

**Weekend and holiday on-call notes written up after the shift (p08)**

The scheduler who covered the weekend or holiday on-call shift writes a call-by-call narrative of gas control pages, cuts, and well issues and emails it to the desk on Monday, and recipients then check each meter it mentions against the system. 30 minutes because the whole weekend is reconstructed from memory or scattered notes after the fact, and two of the three batch estimates said 30.

Where it gets stuck. Nothing is logged as the calls happen, so the narrative is rebuilt afterward in free text and every recipient has to cross-check the meters by hand.

Who does it. robert.cotten@enron.com, mary.poorman@enron.com, michael.olsen@enron.com, robert.lloyd@enron.com, tom.acton@enron.com, daren.farmer@enron.com

Matched 9 messages, 2000-01-17 to 2001-07-28, 18.3 active months. 0.5 per month over the active window, 0.3 per month over the full 27.4 month archive span. Rule: body contains any of "notes from this weekend", "on-call notes", "received a page from", "notified by gas control", "received a call from"

> Attached are the notes from this weekend.
>
> robert.lloyd@enron.com, 2000-08-14. Email `0c4428ce9278`.

> Here are my notes, please let me know if you have any questions.
>
> mary.poorman@enron.com, 2000-08-28. Email `e8fea4b16107`.

> Friday 1/19/01 - Received a call from Sheila at Basin regarding a well which
may be coming on this weekend (meter 9696).  Phone Lee in Gas Control
regarding same.
>
> mary.poorman@enron.com, 2001-01-22. Email `6d98361e6ed8`.

> Saturday:

Mark from Aquilla was short 5000 into the Valero Hub and it appeared that
PG&E may have to cut Aquilla's delivery into us, but Mark was able to get the
5000 he needed to make the delivery.
>
> michael.olsen@enron.com, 2001-03-05. Email `7dffc1a5ad97`.

> Friday 3/23 - Received a page from Silver in Gas Control at 8:00 pm regarding the Gulf Plains Plant.  They were cut into another pipeline (Tennessee), and wanted to overdeliver to us by 10M for the night.
>
> mary.poorman@enron.com, 2001-03-26. Email `afb2990b7e07`.

> Friday - April 13th

6:00pm Notified by gas control that we needed to deliver to Centana for operational reasons, approx. 30-50 MMBTU rate.
>
> mark.mccoy@enron.com, 2001-04-16. Email `978821804a23`.

**Out of office coverage handoff notices (p09)**

Before a vacation or absence, each scheduler writes a note naming who covers their meters, pipelines, or accounts, with extensions and pager numbers, and sends it to the desk. 10 minutes because the coverage list is retyped from scratch each time, which both batch estimates agreed on.

Where it gets stuck. There is no standing coverage roster, so every absence means rewriting who covers what and how to reach them.

Who does it. aimee.lannou@enron.com, carlos.rodriguez@enron.com, robert.lloyd@enron.com, mark.mccoy@enron.com, daren.farmer@enron.com

Matched 33 messages, 1999-12-15 to 2002-01-25, 25.4 active months. 1.3 per month over the active window, 1.2 per month over the full 27.4 month archive span. Rule: body contains any of "i will be on vacation", "i will be out on vacation", "i will be out of the", "in my absence", "backing me up", "my back up"

> I will be on vacation Friday, June 2 through  Monday, June 12.  In my absence
please direct any questions or issues to these people.
>
> aimee.lannou@enron.com, 2000-05-31. Email `061a91d5ed81`.

> I will be out on vacation the week of July 3, back at the office on July
10th. My main contact will be Stella Morris at ext. 3319.
>
> carlos.rodriguez@enron.com, 2000-06-29. Email `71e2b417d6b9`.

> FYI-- I will be out of the office Wednesday, Feb. 7th through Friday the 9th,
returning on Monday.

Mary Poorman and Tom Acton will be backing me up.
>
> mark.mccoy@enron.com, 2001-02-06. Email `093071741743`.

> I will be out of the office from 3/15 thru 3/25 on vacation. If you have any
questions Mike Olsen ext - 35796 will be the point person.
>
> carlos.rodriguez@enron.com, 2001-03-14. Email `08a02ffda803`.

> I will be on vacation from Thursday 5/10 thru Wednesday 5/16. Tom Acton will be my back up  713-571-3256, pager 713-707-3527 and Bob Cotten will do the NNGB (Black Marlin) and help Tom.
>
> carlos.rodriguez@enron.com, 2001-05-09. Email `dabe5d15b570`.

**Trading book, curve, and access setup requests in Tagg, TDS, and RiskTrac (p10)**

Desk controllers and traders email the Tagg, TDS, and RiskTrac administrators to create books and curves, map books to traders and EOL products, update the Book Admin list, and grant access, and during the Netco and UBS transition they rebuilt access matrices and curve mappings and re-pointed macros after each rename. 20 minutes because each request means spelling out naming, mappings, and user lists, then following up until it is live, the most common batch estimate across the range of 10 to 30.

Where it gets stuck. Setup is not self service, so every book, curve, or access change is an email to whichever admin currently owns it, often incomplete and sent back for another round.

Who does it. darron.giron@enron.com, kam.keiser@enron.com, m..love@enron.com, susan.trevino@enron.com, gary.stadler@enron.com, jeremy.wong@enron.com, burton.mcintyre@enron.com

Matched 18 messages, 2000-03-28 to 2002-02-04, 22.3 active months. 0.8 per month over the active window, 0.7 per month over the full 27.4 month archive span. Rule: body contains any of "book to tagg", "added to tagg", "set up in tds", "book admin list", "book requests", "separate books", "eol product", "mapped to curves", "copy physical macro", "refresh booklist"

> Please add the following book to Tagg:

 IM-CENT-MID2
>
> darron.giron@enron.com, 2000-06-14. Email `31eb3e8bfefe`.

> I set up these new curves this morning and need them added to Tagg

 NGI-MOJAVE
 GDP-MOJAVE
 GDP-PGE/TOPOCK
>
> darron.giron@enron.com, 2000-12-07. Email `3981f4d6af91`.

> I need to have FT-DENVER set up in TDS.  The trader is Jay Reitmeyer.  There
are two Tagg books that need to be mapped to this:  FT-DENVER and
INTRA-DENVER.
>
> darron.giron@enron.com, 2001-01-11. Email `460269329baa`.

> Please add Elizabeth Shim to the Book Admin list on the Web sight.  Her Tagg
user name is:  ESHIM.  Thanks.
>
> darron.giron@enron.com, 2001-05-04. Email `07a67cfb7b3f`.

> These are book requests for the Netco books for all regions.
>
> kam.keiser@enron.com, 2002-01-04. Email `b91e90955d7d`.

> Check your regions and if you see any locations mapped to curves we won't be setting anymore, make a list of those and what the new mappings should be.
>
> kam.keiser@enron.com, 2002-01-07. Email `f1e6e6f16bcc`.

> We need to assign EOL products to traders.
>
> kam.keiser@enron.com, 2002-01-11. Email `4d81aa465ccf`.

> you may need to edit your Copy Physical Macro in your P&L's that are saved in the Netco/Regions folder
>
> d..winfree@enron.com, 2002-01-30. Email `ad871179f11a`.

**Moving deals between books and linking deal numbers across Tagg, Sitara, SCI, and EOL (p11)**

The desk flags deals that sit in the wrong book and must be flipped into FT-US/CAND-ERMS or, after the bankruptcy filing, moved into the bankruptcy books, and separately chases missing cross-references so each deal carries its Tagg, Sitara, SCI, and EOL numbers. 15 minutes because a single flip or link is about 10 minutes and the bankruptcy moves ran longer at 25, so 15 reflects the typical request.

Where it gets stuck. The list of deals to move or link lives in someone's head or a spreadsheet rather than in Tagg, so deals are missed and moved only after a second or third reminder email.

Who does it. darron.giron@enron.com, stacey.vallejo@enron.com, carole.frank@enron.com, stacey.richardson@enron.com, cecilia.cheung@enron.com, m..love@enron.com

Matched 23 messages, 2000-08-10 to 2002-01-31, 17.7 active months. 1.3 per month over the active window, 0.8 per month over the full 27.4 month archive span. Rule: body contains any of "flipped", "flip these", "bankruptcy book", "link field", "link up all deals"

> I've come across this deal that needs to be flipped right away.
This deal is in the MGMT-WEST book with Aquila Canada Corp. and
ENA.  It needs to be in the FT-US/CAND-ERMS book settling between
ECC and Aquila Canada Corp.
>
> darron.giron@enron.com, 2001-03-05. Email `c31f511e108f`.

> I just came across one more deal that needs to be flipped.

QU4190.1
>
> darron.giron@enron.com, 2001-03-28. Email `edd075957b31`.

> The WEST-PERM deals have been flipped.
>
> darron.giron@enron.com, 2001-05-02. Email `3b622b6efc87`.

> Attached please find some "stragglers" that need to moved into the bankruptcy books.
>
> stacey.richardson@enron.com, 2002-01-25. Email `84f9d6656bc9`.

> 2923 deals with NG-PRICE book attached have been moved to the Bankruptcy bookand retranslated successfully.
>
> cecilia.cheung@enron.com, 2002-01-24. Email `374338c78618`.

> Please remember to link up all deals.  By this, I mean Tagg numbers in
Sitara, Sitara numbers in Tagg, Tagg numbers in SCI, and especially EOL
numbers in Tagg.
>
> darron.giron@enron.com, 2000-10-17. Email `3bff55c13fd2`.

> The deals look good in both Tagg and Sitara, but the link field in Tagg has
not been populated with the Sitara number.  When will this be ready?
>
> darron.giron@enron.com, 2000-12-20. Email `b974ef09ec82`.

**Real-time power desk short and long position notices (p12)**

Bill Williams emails the real-time group whenever the desk is short or long for an upcoming day, with megawatts, prices, delivery points, and the book, and traders then buy or sell and key the deals into Enpower and CAPS. 15 minutes because each notice means pulling positions, confirming prices with other desks, and re-keying the result into two systems, which both batch estimates said.

Where it gets stuck. Positions are typed into free-text emails and re-keyed by hand into Enpower and CAPS, with follow-up emails whenever the day's shape changes.

Who does it. bill.williams@enron.com, kate.symes@enron.com

Matched 20 messages, 2000-03-22 to 2001-11-14, 19.8 active months. 1.0 per month over the active window, 0.7 per month over the full 27.4 month archive span. Rule: body contains any of "we are short", "we are long", "we will be short", "we will be long"

> We are long 25 mws on peak for 06/27/01 in SP-15.  This should be in CAPS under ST-WBOM, deals should be under ST-WBOM in Enpower as well.
>
> bill.williams@enron.com, 2001-06-27. Email `affa2dd11baa`.

> We are short 50 mws in SP-15 for HE 7-22 on Wednesday at $61.44.  Please purchase this 50 mws under ST-WBOM.
>
> bill.williams@enron.com, 2001-07-11. Email `3593d0497185`.

> We are short 25 mws in SP15 at $43 for Tuesday.  I am unsure if ST-CALI is doing anything.
We are short 25 mws at PV at @$50 with ST-SW on EPE lending for Tuesday.
>
> bill.williams@enron.com, 2001-08-13. Email `439d7e125bd2`.

> Kate,
We are short 3 pieces tomorrow at $27.20, $28.00, and a piece at the ST-CALI index.
>
> bill.williams@enron.com, 2001-10-17. Email `6789811edc8d`.

> Kate,
We are short 2 pieces of BOM at SP-15 7-22.
Price of $27.20 and $28.00.
We are also short 1 daily piece in SP-15 at the ST-CALI index price.
>
> bill.williams@enron.com, 2001-10-15. Email `5845610dc77c`.

**Reconciling real-time congestion revenue and Enpower deals against settlements (p13)**

Bill Williams hand-calculates CAISO congestion relief revenue and checks it against the inc sheet and the flash, and separately compares Enpower deal entries with the PMA sheet, the DPR, and the SAR to get double entries, wrong prices, and counterparty changes corrected by settlements. 20 minutes because each case means pulling CAISO or settlement data, comparing it line by line, and writing up the specific deals and dollars, which most batch estimates chose.

Where it gets stuck. CAISO awards and Enpower deal changes are not reconciled against the settlement records automatically, so revenue goes missing from the flash until Bill compares the two by hand and chases a fix.

Who does it. bill.williams@enron.com, jim.reyes@enron.com, kourtney.nelson@enron.com, darren.cavanaugh@enron.com, virginia.thompson@enron.com, heather.dunton@enron.com

Matched 14 messages, 2001-06-29 to 2001-11-15, 4.6 active months. 3.1 per month over the active window, 0.5 per month over the full 27.4 month archive span. Rule: body contains any of "congestion revenue", "congestion that we relieved", "pma sheet", "bom sar", "new deal summary"

> I just wanted to bring to your attention the volume of congestion that we relieved last night.
It looks like 28 mws at $198 and 75 mws at $223.00.
This should be at total revenue of $22,269.00.
>
> bill.williams@enron.com, 2001-08-07. Email `038407f3df33`.

> We have congestion revenue again for 08_07.
We moved 272 mws at $194.
Total revenue should be $52768.
>
> bill.williams@enron.com, 2001-08-08. Email `d963c25b9710`.

> We are missing the congestion revenue from HE 7 on Saturday morning (10 mws at $99.00) in the flash we received yesterday.  Remember, the awarded congestion wheel caused the 10 mw variance we discussed on Monday.
>
> bill.williams@enron.com, 2001-08-15. Email `0365cbab23e0`.

> Darren,
Could you meet with me regarding congestion revenue for 10/05?
We had two wheels that were not in the inc sheet but were awarded by the CAISO and are in finals in CAPS.
>
> bill.williams@enron.com, 2001-10-08. Email `4debc9c2f9cc`.

> We have resolved almost all of the recent PMA sheet.  The Tacoma/MPC deal is fine if its zeroed out for HE 3.  I just need to have the cost zeroed out as well as the revenue.
>
> bill.williams@enron.com, 2001-07-06. Email `d908e32bce60`.

> We had some double deal-entry last night under the ST-WBOM book.  Consequently I zeroed the following deals out this morning after receiving the DPR and running a BOM SAR.
>
> bill.williams@enron.com, 2001-06-29. Email `d2933ba141a4`.

> First, for deal #549162, this deal was originally put in incorrectly as counterparty TacomaSupp.  This counterparty was then changed to Tacomapubuit.  Why does a change in counterparty result in a loss of revenue?
>
> bill.williams@enron.com, 2001-07-03. Email `cd021560b0d1`.

**Weekly California Capacity Report (p14)**

Michelle Lokay compiles Transwestern and El Paso delivery volumes by point, capacity percentages, and Gas Daily prices into the same report and sends it to the same distribution list every week. 30 minutes because the volumes and four price lines come from separate sources and are hand-typed into the template each week, as the batch estimate said.

Where it gets stuck. The same data is gathered from separate sources and retyped into an identical email format every week.

Who does it. michelle.lokay@enron.com

Matched 16 messages, 2001-10-26 to 2002-03-22, 4.8 active months. 3.3 per month over the active window, 0.6 per month over the full 27.4 month archive span. Rule: body contains any of "average deliveries to california", "san juan lateral throughput"

> Transwestern's average deliveries to California were 945 MMBtu/d (87%), with San Juan lateral throughput at 865 MMBtu/d.  Total East deliveries averaged 525 MMBtu/d.
>
> michelle.lokay@enron.com, 2001-10-26. Email `86c805170e90`.

> Transwestern's average deliveries to California were 1122 MMBtu/d (103%), with San Juan lateral throughput at 844 MMBtu/d.  Total East deliveries averaged 270 MMBtu/d.
>
> michelle.lokay@enron.com, 2001-12-14. Email `a5fb48e9c2c6`.

> Transwestern's average deliveries to California were 884 MMBtu/d (81%), with San Juan lateral throughput at 773 MMBtu/d.  Total East deliveries averaged 391 MMBtu/d.
>
> michelle.lokay@enron.com, 2002-03-22. Email `b16581b00998`.

**Daily Energy Market Report forward to the West power desk (p15)**

Jill Chatterton opens the Economic Insight Energy Market Report PDF each trading day and forwards it unchanged to the same West Desk distribution list. 3 minutes because it is a straight forward with no editing, which both batch estimates agreed on, and the cost comes from repeating it every day.

Where it gets stuck. The report is forwarded by hand each morning instead of being routed to the list when it arrives.

Who does it. jill.chatterton@enron.com

Matched 7 messages, 2002-01-29 to 2002-02-06, 1.0 active months. 7.0 per month over the active window, 0.3 per month over the full 27.4 month archive span. Rule: body contains any of "energy market report"

> Subject: Energy Market Report - 01/29/02

Energy Market Report
Tuesday, January 29, 2002

*See attached pdf file.
>
> jill.chatterton@enron.com, 2002-01-30. Email `1c3b3d510170`.

> Subject: Energy Market Report - 01/30/02

Energy Market Report
Wednesday, January 30, 2002

*See attached pdf file.
>
> jill.chatterton@enron.com, 2002-01-31. Email `8e2e1e5ce651`.

> Subject: Energy Market Report - 02/04/02

Energy Market Report
Monday, February 4, 2002

*See attached pdf file.
>
> jill.chatterton@enron.com, 2002-02-05. Email `309449405256`.

> Subject: Energy Market Report - 02/05/02

Energy Market Report
Tuesday, February 5, 2002

*See attached pdf file.
>
> jill.chatterton@enron.com, 2002-02-06. Email `c8376d50b73d`.
