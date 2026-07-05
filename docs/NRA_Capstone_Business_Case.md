# Month 11 Capstone - Final Business Case Report

### Bullet 1 - Delay exposure
Number: 234 of 530 shipments (44.15%) are flagged High Delay (>14 days transit), putting Rs 305,612.65 in revenue at risk.
Reason: days_in_transit is drawn independently per shipment with no carrier-linked parameter in the generator -- the share above a 14-day cutoff is a function of the distribution's width relative to the cutoff, not a designed failure mode.
Action: Owner - pipeline lead. Confirm the 14-day cutoff against the client's real SLA (currently a placeholder) before this threshold appears in any client-facing report.

### Bullet 2 - Carrier transit-time ranking
Number: Delhivery shows the highest average transit time at 13.13 days vs. Ecom Express's lowest at 11.93 days.
Reason: days_in_transit is generated independently of carrier; this ranking reflects sampling variance across ~94-123 shipments per carrier, not a measured operational difference.
Action: Owner - carrier relationship manager. Do not reallocate volume based on this ranking; re-test against >=3 months of real transit logs first.

### Bullet 3 - Process conformance monitor
Number: Overall conformance is 71.32% (378/530), below the 80% threshold. BlueDart has the lowest carrier-level conformance at 61.7% (58/94), and also the highest high-delay share at 50.0%.
Reason: The rework/break event is injected via a delay-linked probability (45% if high-delay, 15% if not) that is carrier-independent in the generator. BlueDart's lower conformance is explained by its high-delay share feeding into that same mechanism -- not a BlueDart-specific process failure.
Action: Owner - monitoring lead. Ship the 71.32% alert as-is. Do not target BlueDart specifically; investigate root causes of high-delay shipments across all carriers, since fixing the delay rate fixes conformance for every carrier through the same mechanism. Weekly review with operations; escalate if below 80% for 2 consecutive weeks.
