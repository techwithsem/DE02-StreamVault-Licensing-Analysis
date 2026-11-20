# ADR-005: Keep round-number revenues

**Status:** accepted · **Findings:** F09

## Context
4 films report revenue as an exact round figure:
- *Monsters, Inc.*: $650,000,000
- *Star Wars: Episode III – Revenge of the Sith*: $850,000,000
- *Terminator 3*: $435,000,000
- *Alien Resurrection*: $162,000,000

A counted box office total almost never ends in six zeros, so these are probably estimates.

## Decision
Keep them, and flag them (`flag_round_revenue`). An estimate of a big number is still close, and every one of these films is a known commercial release.

## Alternative rejected
Leaving them out of returns.

## Cost if wrong
Small. If they are left out, the franchise median moves from 5.62× to 5.85× (all years) and from 5.05× to 5.06× (2000 onward). The standalone median doesn't change, because all 4 are franchise films. The leader is the same. Source: `out/sensitivity.csv`, scenario "drop round-number revenues".

## What survives
The flag and the sensitivity run are automatic, so if next year's list has many more estimated figures, Adjoa will see the count and the effect without re-doing the analysis.
