# ADR-008: A 10-second budget for the analysis, with downloads excluded

**Status:** accepted · **Measurement:** [measurement-report.md](../measurement-report.md)

## Context
The brief requires a measured time budget but leaves the number to Evalu8. Adjoa may run the analysis live in a meeting, so it has to feel instant. TMDb's response time varies from run to run for reasons unrelated to my code.

## Decision
- **Budget:** stages 2 to 5 (read the saved answers, build tables, run checks, compute every KPI in both windows and all scenarios, write outputs) must finish within **10 seconds** on an ordinary laptop. *If Evalu8 states a different budget, change `TIME_BUDGET_SECONDS` in `pipeline/config.py`.*
- **What is not timed:** downloading from TMDb (stage 1) and the bundle and spot-check calls. They depend on the network and happen once per quarter. They are timed separately and printed.
- **How:** every run prints the time per stage and writes `out/timing.csv`. A loud warning is printed if the total goes over budget.
- **No row loops:** every result is computed with whole-column maths or groupby. A test (`test_no_row_loops_in_the_analysis_code`) fails if anyone adds `iterrows`, `itertuples` or a row-wise `apply`.

## Alternative rejected
1. **Timing the whole run, downloads included.** This measures TMDb and the Wi-Fi, not my code.
2. **A tighter budget** (say 1 second). I meet it at 127 titles on a good run (0.86 s), not on a noisy one (1.4 s), and not at 500 (about 3.5 s). Getting there would mean less readable code for Adjoa.

## Cost if wrong
If the real budget on Evalu8 is under 3 seconds, 500 titles won't fit as written. The fix is known: stage 2 (reading about 1,000 JSON files) takes about 90% of the time, so saving the flattened tables to one file after the first run would cut it to well under a second.

## What survives
Measured at 127, 500 and 5,000 titles (`python -m scripts.scale_test`): about 6–7 ms per title, rising roughly in a straight line. 500 titles take about 3–3.5 seconds (5.2 s on the slowest run ever recorded), inside the budget with room to spare.
