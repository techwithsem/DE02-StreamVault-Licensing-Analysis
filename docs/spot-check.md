# Spot-check: my output against TMDb live

**Checked:** 20 Nov 2026 · **Rebuild:** `python StreamVault.py --spot-check` → `out/spot_check.csv`

## In three sentences
I checked 14 films, 7 fields each, chosen in four deliberate groups (listed below), not at random alone. All 98 values matched: my output equals the saved snapshot, and the snapshot equals what TMDb shows today. No discrepancy was found, so nothing in the recommendation moves.

## How the sample was chosen
| Group | Films | Why |
|---|---|---|
| Extremes: highest return | *Star Wars* (70×), *Jaws* (67×) | They pull the all-years figures most, so an error here costs most. |
| Extremes: lowest return | *The Shawshank Redemption* (1.1×), *Blade Runner* (1.5×) | The other end of the same lever. |
| Most changed by the pipeline | *The Dark Knight* (named on the most input rows: 3, one an IMDb id), *Monsters, Inc.* (round revenue), *Shrek 2* (the most co-directors: 3) | Every transformation is a chance to be wrong. |
| Boundary cases | *Toy Story 2* (last release before 2000), *Mission: Impossible II* (first release from 2000), *The Lion King* (only film of its franchise on the list) | They sit exactly on a rule: the 2000 split and the franchise definition. |
| Random (fixed seed 42) | *The Departed*, *Harry Potter and the Philosopher's Stone*, *Mission: Impossible III*, *The Smurfs* | So the check can't be accused of being picked to pass. |

Every pick is chosen by a rule applied to the data, never by a fixed film id, so the same check works on next year's list.

**Fields checked:** title, release date, budget, revenue, franchise (collection id), directors, lead actor.

## Tolerance (set before looking)
Exact match for every field. Money is stored in whole dollars, so any change at all counts as a difference.

## How a difference would be classed
| My output vs snapshot | Snapshot vs live | Class | What I would do |
|---|---|---|---|
| different | — | **Pipeline bug** | Fix it, then rerun the whole spot-check. |
| same | different | **Source changed** (TMDb was edited) | Record both values and both dates; decide whether to `--refresh`. |
| same | same | **Match** | Nothing. |

Two other classes from the course are handled elsewhere:
- **Definition mismatch:** for example, my "revenue" is TMDb's worldwide box office. It's written down in ADR-003.
- **Genuinely missing:** the 5 dead ids. They're recorded in `data/id_accounting.csv`.

## Result
| Class | Values |
|---|---:|
| Match | 98 |
| Pipeline bug | 0 |
| Source changed | 0 |

**Does any discrepancy change the recommendation?** No. There were none, and the snapshot matched TMDb on the day of the analysis.

**Limit:** a check on 14 of 112 films can't prove every row is right. The hard checks in `profiling/checks.csv` cover the rest (one row per film, every film has a director and a lead actor, and so on). This check is a sample of the source, which those checks can't see.
