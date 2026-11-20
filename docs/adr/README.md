# Decision notes

One note per judgement call the brief left open. Each follows the same layout:
- **Context:** why a decision was needed.
- **Decision:** what I did.
- **Alternative rejected:** what I considered instead.
- **Cost if wrong:** what it would cost Kwame, and what the answer looks like under the alternative.
- **What survives:** what still holds when Adjoa reruns this next year on about 500 titles without me.

| # | Decision | Moves the answer? |
|---|---|---|
| [ADR-001](ADR-001-every-row-accounted-for.md) | Count each film once; keep every input row on record | Yes: the lead would be a third bigger if repeats were counted |
| [ADR-002](ADR-002-what-counts-as-a-franchise.md) | A franchise film is any film TMDb puts in a collection | Yes: the biggest single mover, though the leader holds |
| [ADR-003](ADR-003-how-success-is-measured.md) | Success = revenue ÷ budget, reported as a median with counts | Yes: the means would hide the gap |
| [ADR-004](ADR-004-films-before-2000.md) | Both windows everywhere; lead with 2000 onward | Yes: the size of the lead, not who leads |
| [ADR-005](ADR-005-round-number-revenues.md) | Keep round-number revenues | No |
| [ADR-006](ADR-006-crediting-talent.md) | Lead actor = first billed; co-directors get full credit; 2+ films, count shown | Talent table only |
| [ADR-007](ADR-007-cached-snapshot.md) | Fetch once, cache with timestamps, commit the snapshot | Reproducibility |
| [ADR-008](ADR-008-time-budget.md) | 10-second budget for the analysis, downloads excluded | No |
| [ADR-009](ADR-009-shortlist-rule.md) | Rank the shortlist on 2000-onward films | Yes: which titles are named |
