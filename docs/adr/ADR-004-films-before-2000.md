# ADR-004: Show both windows everywhere, and lead with 2000 onward

**Status:** accepted · **Findings:** F03, F04, F13, F19

## Context
Yaw in Finance distrusts figures for films released before 2000 (inflation, currency reporting, how box office used to be reported). The brief says to show the comparison for all years and for 2000 onward, and to say loudly if the answer flips. 41 of the 112 films came out before 2000.

The data backs Yaw up. Median return is 11.9× before 1990, 5.9× in the 1990s and 4.9× from 2000 onward. *Star Wars* (1977) shows $775M on $11M. Public records suggest older totals include later re-releases, and TMDb has no field that separates them.

## Decision
- **Every KPI is computed twice:** all years, and films released in 2000 or later (by TMDb's main release date; 2000 counts as "onward").
- **The memo leads with 2000 onward,** because it is the figure Yaw cannot attack. All years is shown beside it.
- **The shortlist is ranked on 2000-onward films** (ADR-009).
- **Answering Yaw's three concerns:**
  - *Inflation* cancels out, because the return multiple divides two figures from the same year.
  - *Currency* also largely cancels for the same reason.
  - *Re-releases* do not cancel, so I take them out by using the 2000-onward window.

## Alternative rejected
1. **Adjusting old figures for inflation.** This doesn't help: inflation already cancels in the multiple, and an inflation adjustment does nothing about re-release revenue.
2. **Dropping pre-2000 films entirely.** This throws away 41 films, including the earlier entries of franchises still being sold, and the brief asks for both windows.

## Cost if wrong
The answer does **not** flip: franchises lead in both windows. The lead shrinks from 1.78× (all years) to 1.21× (2000 onward). The "weak later entries" pattern seen across all years (first films 7.4×, later films 4.6×) disappears from 2000 onward (5.3× → 5.1×). If Yaw is wrong and the old figures are sound, I have under-sold the strongest older franchises (*Star Wars*, *Indiana Jones*) and the older standalones (*Pulp Fiction*, *Forrest Gump*).

## What survives
The window start is one setting (`WINDOWS` in `pipeline/kpis.py`). Both windows are produced on every run, and `out/summary.md` prints a loud line if the leader ever differs between them, so Adjoa doesn't have to remember to check.
