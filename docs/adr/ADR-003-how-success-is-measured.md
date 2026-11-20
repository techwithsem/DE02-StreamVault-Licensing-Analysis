# ADR-003: Success = revenue ÷ budget, reported as a median with the count beside it

**Status:** accepted · **Findings:** F05, F08, F10, F12

## Context
Kwame needs one number that says whether a title "worked". TMDb gives worldwide box office revenue and production budget. Film money is very lopsided: a few huge hits and many modest films.

## Decision
- **Measure:** the *return multiple* = revenue ÷ budget, per film. "5×" means the film took five dollars at the box office for every dollar it cost to make. Both figures are in the same year's dollars, so inflation cancels out (this matters for ADR-004).
- **Headline:** the **median** (the middle film), with the mean shown beside it, plus the middle-half range (25th to 75th percentile) and the number of films behind every figure.
- **Missing values:** a budget or revenue of 0 is treated as unknown, and that film is left out of returns only. It still counts as a film. This year no film has a 0; the rule is there for next year.
- **Secondary signals:** TMDb rating and vote count are shown beside returns as a sign of how well liked and how widely seen a film is today.

## Alternative rejected
1. **The mean.** The franchise and standalone means are almost equal (8.5× vs 8.3×, all years), because *Star Wars* (70×) and *The Good, the Bad and the Ugly* (32×) pull each average up. The medians (5.6× vs 3.8×) show what a typical film does.
2. **Profit in dollars** (revenue − budget). This rewards size, not efficiency: every big-budget film looks good, and the dollar figures are not comparable across decades.
3. **Ratio of totals** (all revenue ÷ all budget). This lets the biggest film decide. It is shown per franchise as `bundle_multiple`, but not used for ranking.

## Cost if wrong
- Box office is not streaming value, and budget leaves out marketing (often as much again). A film at 2× may have lost money in cinemas. Returns are a *comparison* between candidates, not a forecast of streaming income. The memo says so.
- With only 16 standalone films (8 since 2000), the standalone median rests on a few films. Taking out the 2 highest or the 2 lowest of the 8 post-2000 standalones moves that median from 3.84× to 3.07× or 4.49×, about a fifth either way. The memo lists it under what I could not stand behind.
- The list holds only well-known hits (every film has 4,000+ votes), so results describe *these candidates*, not franchises in general.

## What survives
The definition is simple enough to explain in the room and to recompute by hand. Every results table in `out/` (by window, by scenario, by franchise, by person) carries a film count, so Adjoa can see at a glance when a figure rests on too few films. If next year's list includes films with no budget, they drop out of returns automatically and the `usable` count shows how many.
