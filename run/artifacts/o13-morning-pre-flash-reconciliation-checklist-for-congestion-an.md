# Morning Pre-Flash Reconciliation Checklist for Congestion and Deal Entries

Run this before the morning flash goes out. It catches the congestion wheels and deal entry errors that otherwise turn up as a correction email after the fact.

## Stage 1: CAISO congestion revenue against the inc sheet and CAPS finals

- [ ] Pull every CAISO congestion award for the prior gas day from CAPS finals.
- [ ] **Check each award against the inc sheet. This is the step that usually gets skipped**, and a missed wheel is exactly what goes wrong. On 10/08/01 two wheels, EPMI_CISO_GREEN for HE 17 and HE 18, were awarded by CAISO and sitting in CAPS finals but were never in the inc sheet, worth $3,891.31 at $54.90 per mw (38.96 mws HE 17, 31.92 mws HE 18).
- [ ] Check each award against the prior day's flash. A wheel can be in the inc sheet and still miss the flash. On 8/11/01 a 10 mw congestion wheel for HE 7 on Saturday, 10 mws at $99.00, was missing from the flash even though it had already been flagged as a variance days earlier.
- [ ] Total the mws and dollars for every award found this way. Write the total next to each entry, the way Bill Williams reports it: mws moved, price, total revenue (example: "272 mws at $194, total revenue $52,768").

## Stage 2: Enpower deal entries against the DPR and BOM SAR

- [ ] Pull the Daily Position Report (DPR) and run a BOM SAR for the book being reconciled.
- [ ] Compare Enpower deal entries against the DPR for duplicate entries. On 6/27/01, a double deal entry under ST-WBOM (deals 665907, buy from imbalance, and 665913, sell to PowerX) added $10,875 of revenue that should not have been there.
- [ ] Zero out any duplicate found, and note which deal number was zeroed and why.
- [ ] Flag any deal whose price looks like an outlier against the book's normal range for that day.

## Stage 3: PMA sheet against Enpower deal history

- [ ] Pull the current PMA sheet and match each line to its Enpower deal number.
- [ ] Check for a counterparty change on any deal. A counterparty change from TacomaSupp to Tacomapubuit on deal #549162 caused a loss of revenue with no explanation on file, the kind of change that needs a reason recorded before it goes through.
- [ ] Check for a price change that was made in Enpower but never came through as revenue. Deal #590753 needed a $108,000 PMA for a price change, originally input as a buy at $320 and a sell at $30, later corrected to $320 and $300, and the revenue never appeared until someone tracked it down by hand.
- [ ] Confirm both the cost and the revenue side were zeroed out together. The Tacoma/MPC deal for HE 3 had only the revenue side zeroed out at first, leaving the cost side still open.

## Stage 4: Send the exception list

- [ ] Combine everything flagged in Stages 1 through 3 into one list: meter or deal number, mws or dollar amount, what is wrong, what system it lives in.
- [ ] Send the list to settlements before the flash goes out, the same people who currently get these one at a time: Jim Reyes and Darren Cavanaugh for congestion items, Virginia Thompson and Heather Dunton for PMA and deal entry items.
- [ ] Hold the flash until every item on the list is either cleared or explicitly accepted as-is.

## Evidence

- Source: 4debc9c2f9cc, 2001-10-08, bill.williams@enron.com, "Congestion Revenue for 10/05"
- Source: d2933ba141a4, 2001-06-29, bill.williams@enron.com, "Adjustments for ST-WBOM for 06/27/01"
- Source: cd021560b0d1, 2001-07-03, bill.williams@enron.com, "PMA's"
- Source: 0365cbab23e0, 2001-08-15, bill.williams@enron.com, "Congestion for Saturday"
