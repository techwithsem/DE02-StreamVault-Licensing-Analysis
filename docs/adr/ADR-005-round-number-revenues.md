# ADR-005: Keep round-number revenues

**Status:** accepted · **Findings:** F09

## Context
Some films report revenue as an exact whole number of millions (six trailing zeros). A counted box office total almost never ends that way, so these are probably estimates.

The rule is `flag_round_revenue` in `pipeline/checks.py`, and it is tested on its own (`test_round_revenue_rule_is_six_trailing_zeros`). Every run recounts it, so this note doesn't go stale when the data changes:
- **How many films:** `profiling/flags.csv`, row `flag_round_revenue`.
- **Which films:** `profiling/flagged_films.csv`, where `flag_round_revenue` is True.

On the 20 Nov 2026 snapshot it flags 4 films, all from franchises (for example *Monsters, Inc.* at $650,000,000).

## Decision
Keep them, and flag them (`flag_round_revenue`). An estimate of a big number is still close, and every film it flags on this list is a known commercial release.

## Alternative rejected
Leaving them out of returns.

## Cost if wrong
Small. If they are left out, the franchise median moves from 5.62× to 5.85× (all years) and from 5.05× to 5.06× (2000 onward). The standalone median doesn't change, because all 4 are franchise films. The leader is the same. Source: `out/sensitivity.csv`, scenario "drop round-number revenues".

## What survives
The flag and the sensitivity run are automatic, so if next year's list has many more estimated figures, Adjoa will see the count and the effect without re-doing the analysis.
