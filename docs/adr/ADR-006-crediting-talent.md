# ADR-006: How directors and lead actors are credited

**Status:** accepted · **Findings:** F14, F15

## Context
Kwame wants to know which directors and lead actors reliably signal a title worth licensing. TMDb credits list a whole cast and crew, not a "lead".

## Decision
- **Lead actor** = the first-billed cast member (`order = 0` in TMDb credits). Every film on the list has exactly one.
- **Directors** = everyone with the job "Director". Co-directors (the Russo brothers, the Wachowskis) each get full credit for the film. A person listed twice as director of the same film counts once.
- **Who appears in the table:** people with 2 or more films on the list, in that window. The film count, median return, *worst* return and rating are shown for each.
- **"Reliable"** means 3 or more films, with the median above the typical film in that window. The worst return is shown too, so one hit cannot hide a flop.

## Alternative rejected
1. **Top 3 billed as "lead".** This mixes in supporting actors and makes it hard to say who carried the film.
2. **Splitting credit between co-directors** (half each). This makes duos look half as reliable for no business reason; negotiators deal with both.
3. **Including people with 1 film.** A single film is luck, not a signal.

## Cost if wrong
Talent on this list mostly travels with the franchise: Elijah Wood's 11.7× is *Lord of the Rings*'s number. So the table is weak evidence that a person drives returns on their own. The memo presents it as a negotiating lever, not as proof. I computed the "top 3 billed" alternative (2000 onward, 3+ films). The same leads stay at the top (Elijah Wood 11.7×, Ray Romano 8.3×), but their co-stars join them with identical figures: Viggo Mortensen 11.7× next to Wood, John Leguizamo and Denis Leary 8.3× next to Romano. Identical numbers for everyone in the same films show the figure belongs to the franchise, not the person, which is why I kept the narrower "first billed" rule.

## What survives
The rules are plain settings in `pipeline/kpis.py` (`talent_table`, `min_films`). With 500 titles, many more people will reach 3 films, so the table gets more useful, not less. The film count beside each name keeps it honest.
