# Writeoff Approval Request, HPL Strangers Gas Contract Meter

This is the form Logistics fills out and routes to Daren Farmer whenever a meter has
flow booked to the HPL Strangers Gas Contract with no deal covering it, so he can
approve the writeoff to Unaccounted for Gas or supply a deal in one pass instead of a
printed sign-and-return round trip.

## Fields

| Field | Where it comes from |
|---|---|
| Meter number and name | The flow report line that flagged the stray volume, for example "985355 Brown Common Point." |
| Requesting analyst | The Logistics person who pulled the flow history and is sending the request. |
| Period checked for a deal | The date range Logistics searched in Sitara and found no deal at this meter. |
| Flow history (date, MMBtu per day) | Pulled straight from the meter's flow record for the period above. |
| Total volume (MMBtu) | Sum of the flow history rows. |
| Contract currently booking the volume | Fixed value, HPL Strangers Gas Contract, unless the meter is on a different stranger contract. |
| Auto-writeoff threshold check | Compare total volume against the threshold Logistics management sets for automatic approval. That threshold number is not in any of these emails and has to be set before this field can be checked automatically. Until it is set, route every request to Daren. |
| Decision | Approve writeoff to Unaccounted for Gas, or supply a deal. Daren's choice. |
| If supplying a deal | Deal number, counterparty, and the dates the deal should cover. |
| Approver | Daren Farmer, or whoever owns deal entry for this meter. |
| Date approved | The date Daren returns the decision. |

## Example, filled from a real request

| Field | Value |
|---|---|
| Meter number and name | 985355, Brown Common Point |
| Requesting analyst | Clem Cernosek |
| Period checked for a deal | 1/1/99 through 7/31/00 |
| Flow history | 3/30/99: 22, 4/30/99: 21, 8/3/99: 5, 8/30/99: 73, 10/28/99: 10, 10/29/99: 5, 1/30/00: 7, 1/31/00: 29, 4/27/00: 13, 7/31/00: 18 (MMBtu) |
| Total volume | 203 MMBtu |
| Contract currently booking the volume | HPL Strangers Gas Contract |
| Auto-writeoff threshold check | Not yet defined, route to Daren |
| Decision | Approve writeoff to Unaccounted for Gas |
| Approver | Daren Farmer |
| Date approved | (fill in when returned) |

## How this replaces the old process

Clem used to type the flow history into a plain email or a printed form, mail or print
it for a signature, and wait for it to come back before the volume could clear. Filling
this form once, with the flow history pulled automatically instead of typed by hand,
gets the same decision to Daren in one message. Once a threshold is agreed, any request
whose total volume falls under it can skip Daren entirely and go straight to a monthly
writeoff list, with only the requests over threshold routed for his approval.

## Evidence

Source: 85141cb3f0e2, 2000-08-18, clem.cernosek@enron.com, "HPL Meter #985355 Brown Common Point"
Source: b7ed38f73dea, 2000-12-14, clem.cernosek@enron.com, "HPL Meter #980417 HPL/KMID - SEVEN OAKS"
Source: 36912cbd53cf, 2000-11-07, clem.cernosek@enron.com, "HPL Meter #981525 Texoma D/P- GSU HPL"
Source: c4e883d4c147, 2000-12-14, clem.cernosek@enron.com, "HPL Meter #985369 TAFT PLANT RESID ARCO HPL"
