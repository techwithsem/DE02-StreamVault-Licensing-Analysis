# Questions for Kwame, and what I assumed instead

Kwame was not available, so every open question became a stated assumption. If any answer turns out different, the decision note named here says what changes.

| # | Question I would have asked | What I assumed | Decision note |
|---|---|---|---|
| Q1 | What counts as a "franchise"? | Any film TMDb puts in a collection, because that is how a studio would sell it. | ADR-002 |
| Q2 | What does "worked" mean for a title: cinema takings, streaming views, profit? | Box office earned per dollar of budget, as a way to rank candidates, not as a forecast of streaming income. | ADR-003 |
| Q3 | Should repeated entries on the list count more? | No. Each film counts once; repeats are recorded. | ADR-001 |
| Q4 | Which ids were meant by the 5 numbers that match no film? | Unknown. Recorded as gaps, not guessed. | ADR-001 |
| Q5 | Does Finance accept any pre-2000 figure? | Both periods are shown; the memo and shortlist lead with 2000 onward. | ADR-004, ADR-009 |
| Q6 | Will studios sell part of a franchise, or only the whole set? | Only the whole set, as the brief says, so bundles are checked in full. | ADR-002, [improvements](improvements.md) |
| Q7 | Who is the "lead actor" of a film? | The first-billed cast member. | ADR-006 |
| Q8 | How fast must Adjoa's rerun be? | Under 10 seconds for about 500 titles, downloads excluded. | ADR-008 |
| Q9 | Should the data be refreshed before the board, or frozen? | Frozen at 20 Nov 2026 and quoted as such; Adjoa refreshes each quarter. | ADR-007 |
| Q10 | Which five-film bundle did StreamVault pass on last quarter? | Unknown. The memo answers the general question instead (whole five-film bundles on the list typically returned 3.65×: the median of `multiple_whole_bundle` for franchises with `films_released` = 5 in [`out/bundle_completeness.csv`](../out/bundle_completeness.csv)), and the bundle check can test that exact bundle once it is named. | [improvements](improvements.md) |
