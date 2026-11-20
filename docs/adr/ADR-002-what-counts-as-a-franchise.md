# ADR-002: A franchise film is any film TMDb puts in a collection

**Status:** accepted · **Findings:** F01, F02

## Context
The whole question is "franchise bundles vs standalone hits", but the brief never defines a franchise. TMDb's `belongs_to_collection` field groups films that belong together (the *Alien* films, the *Toy Story* films). 9 films on the list are the only member of their collection on the list (*Jaws*, *The Lion King*, *Blade Runner*, *Ghostbusters*…).

## Decision
A film is a franchise film if TMDb puts it in any collection, even if it is the only film from that collection on the list. The reason: if Kwame wants *Jaws*, the studio will sell it as part of the *Jaws* bundle. The list doesn't change how the film is sold.

I also check how complete each bundle is (see [improvements](../improvements.md)), because the list holds only part of 19 of the 32 franchises.

## Alternative rejected
"A franchise needs 2 or more films on the list." This judges the film by how the list was put together, not by how it is sold.

## Cost if wrong
This is the choice that moves the answer most. Under the alternative, the 9 lone films become standalones and the franchise lead shrinks:

| Window | Chosen rule | Alternative |
|---|---|---|
| All years | 5.62× vs 3.84× (lead 1.78×) | 5.53× vs 5.00× (lead 0.53×) |
| 2000 onward | 5.05× vs 3.84× (lead 1.21×) | 5.05× vs 4.49× (lead 0.56×) |

Franchises still lead under both rules, so the recommendation holds. But under the alternative the lead is small enough that the memo should not promise a large premium. That is why the memo says franchises "earn more", and prices the deal against the franchise average, not against standalones.

## What survives
The rule is a single setting (`franchise_rule` in `pipeline/kpis.py`), and both versions are computed on every run, so Adjoa sees whether next year's list changes the picture. It relies on TMDb's collections, which TMDb's community maintains. If TMDb regroups a franchise, the numbers follow on the next `--refresh`.
