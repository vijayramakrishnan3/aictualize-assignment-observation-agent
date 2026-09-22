# Weekly California Capacity Report Template

This is the fill-in-the-blanks version of the report Michelle Lokay sends every Friday.
Whoever pulls the week's numbers uses this instead of retyping the report from scratch.

## Fields

| Field | Where the value comes from |
|---|---|
| Week range | The Monday through Friday of the reporting week |
| Transwestern average deliveries to California (MMBtu/d and %) | Transwestern delivery data for the week |
| San Juan lateral throughput (MMBtu/d) | Transwestern delivery data, San Juan lateral only |
| Total East deliveries average (MMBtu/d) | Transwestern delivery data, East side only |
| El Paso average deliveries to California (MMBtu/d and %) | El Paso delivery data for the week |
| PG&ETop capacity, deliveries, % | El Paso delivery data, PG&ETop point |
| SoCalEhr capacity, deliveries, % | El Paso delivery data, SoCalEhr point |
| SoCalTop capacity, deliveries, % | El Paso delivery data, SoCalTop point |
| Posting day (Thursday or Friday, whichever the week's data lands on) | Gas Daily publication date |
| SoCal gas, large pkgs price and change | Gas Daily |
| PG&E, large pkgs price and change | Gas Daily |
| TW San Juan (or "San Juan (non-Bondad)") price and change | Gas Daily. Mark n/a if Gas Daily did not post a San Juan price that day |
| TW Permian price and change | Gas Daily |
| Enron basis table (Perm-CA, SJ-CA, SJ-Waha, Perm-Waha) | Enron Online or internal basis sheet, if published that week. Skip this block entirely on weeks it is not available, the same way the source reports do |

## Template

```
Subject: California Capacity Report for Week of {start_date}-{end_date}

Transwestern's average deliveries to California were {tw_volume} MMBtu/d ({tw_pct}%), with San Juan lateral throughput at {sj_volume} MMBtu/d. Total East deliveries averaged {east_volume} MMBtu/d.

El Paso's average deliveries to California were {ep_volume} MMBtu/d ({ep_pct}%):
- PG&ETop, capacity of {pgetop_cap} MMBtu/d, deliveries of {pgetop_vol} MMBtu/d ({pgetop_pct}%)
- SoCalEhr, capacity {socalehr_cap} MMBtu/d, deliveries of {socalehr_vol} MMBtu/d ({socalehr_pct}%)
- SoCalTop, capacity {socaltop_cap} MMBtu/d, deliveries of {socaltop_vol} MMBtu/d ({socaltop_pct}%)

{posting_day}'s posted Gas Daily prices:
	SoCal gas, large pkgs	  {socal_price} ({socal_change})
	PG&E, large pkgs	  {pge_price} ({pge_change})
	TW San Juan		  {twsj_price} ({twsj_change})
	TW Permian		  {twperm_price} ({twperm_change})

[Enron basis table, if published this week]
```

Send to the standing list: steven.harris@enron.com, kimberly.watson@enron.com,
lorraine.lindberg@enron.com, tk.lohman@enron.com, lindy.donoho@enron.com,
mark.mcconnell@enron.com, paul.y'barbo@enron.com, cc audrey.robertson@enron.com.

## Example, filled from the week of 10/22-10/26

```
Subject: California Capacity Report for Week of 10/22-10/26

Transwestern's average deliveries to California were 945 MMBtu/d (87%), with San Juan lateral throughput at 865 MMBtu/d. Total East deliveries averaged 525 MMBtu/d.

El Paso's average deliveries to California were 1782 MMBtu/d (66%):
- PG&ETop, capacity of 1140 MMBtu/d, deliveries of 667 MMBtu/d (59%)
- SoCalEhr, capacity 1042 MMBtu/d, deliveries of 707 MMBtu/d (68%)
- SoCalTop, capacity 512 MMBtu/d, deliveries of 408 MMBtu/d (80%)

Friday's posted Gas Daily prices:
	SoCal gas, large pkgs	  3.03 (+.69)
	PG&E, large pkgs	  3.02 (+.67)
	TW San Juan		  n/a
	TW Permian		  2.86 (+.695)
```

## Before sending

The volumes and the four price lines come from separate sources each week, so the one
step that stays manual is a quick check that the pulled numbers look right (no MMBtu/d
figure of zero, no price missing without an n/a) before the report goes out.

## Evidence

Source: 86c805170e90, michelle.lokay@enron.com, 2001-10-26, "California Capacity Report for Week of 10/22-10/26"
Source: a5fb48e9c2c6, michelle.lokay@enron.com, 2001-12-14, "California Capacity Report for Week of 12/10-12/14"
Source: b16581b00998, michelle.lokay@enron.com, 2002-03-22, "California Capacity Report for Week of 03/18-03/22"
