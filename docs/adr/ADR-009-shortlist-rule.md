# ADR-009: Rank the shortlist on 2000-onward films

**Status:** accepted · **Findings:** F01, F03

## Context
Kwame asked for his 3 strongest franchises and 5 strongest standalones. The ranking changes completely depending on the window:

| | Ranked on all years | Ranked on 2000 onward |
|---|---|---|
| Franchises | *Star Wars* 13.4×, *Lord of the Rings* 11.7×, *Indiana Jones* 10.9× (counting only franchises with 2+ films on the list) | *Lord of the Rings* 11.7×, *Ice Age* 8.3×, *The Avengers* 6.9× |
| Standalones | *The Good, the Bad and the Ugly* 32×, *Pulp Fiction* 27×, *Schindler's List* 15×, *Spirited Away* 14×, *Forrest Gump* 12× | *Spirited Away* 14.5×, *Inception* 5.2×, *Interstellar* 4.5×, *Memento* 4.5×, *The Departed* 3.2× |

## Decision
- **Rank on 2000-onward films,** by median return.
- **A franchise needs 2 or more films since 2000 on the list,** so one hit cannot carry it. Its weakest film is shown beside it.
- **Every shortlisted franchise was checked against its whole bundle** (improvement). *Lord of the Rings* and *The Avengers* are complete on the list. *Ice Age* has 3 more films; with them, its return falls from 8.4× to 7.5×, still second.

## Alternative rejected
Ranking on all years. Four of the five standalones and two of the three franchises would rest on pre-1995 figures that Yaw will challenge (ADR-004). And *Star Wars* and *Indiana Jones* fall sharply once their missing sequels are counted: 10.8× to 6.2× and 7.1× to 4.1×.

## Cost if wrong
If the older figures are sound, I have left strong older titles off the list: *Pulp Fiction*, *Forrest Gump*, *Schindler's List*, and *Back to the Future*, whose whole trilogy is on the list and returned 9.8× as a bundle. The memo names them as a second tier to negotiate if price allows. Only 8 standalones were released since 2000, so the standalone list is "top 5 of 8". That is a thin choice, and the memo says so.

## What survives
The rule is code (`analysis.shortlists`). With 500 titles there will be many more post-2000 films, so the "top 5 of 8" weakness should go away on its own.
