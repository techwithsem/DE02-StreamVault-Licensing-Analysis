# Improvement beyond the brief: bundle completeness check

## What it is
For every franchise that has a film on the candidate list, the pipeline now:
- asks TMDb for the franchise's **full** film list
- finds the released films the candidate list left out
- fetches their budget and revenue
- works out what the **whole bundle** earned, next to what the films on the list earned

It runs automatically with `python StreamVault.py`. The results go to `out/bundle_completeness.csv` (one row per franchise) and `out/bundle_films.csv` (one row per film). Like everything else, TMDb answers are saved, so reruns are instant.

## What gap in the brief it closes
The brief says studios sell a franchise all-or-nothing ("take all six or none"). But the list Kwame was handed holds only *some* of each franchise, and the films missing tend to be the weaker later ones. Nothing in the brief asks whether the list matches what would actually be bought. Without this check, every franchise figure describes a bundle no studio is selling.

## What it found
- **19 of 32 franchises are incomplete** on the list: 39 released films are missing.
- Counting the whole bundle, the typical franchise return falls from 5.6× to 4.4×.
- The biggest drops:

| Franchise | On the list | Whole bundle | Missing films |
|---|---:|---:|---|
| Jaws | 67.2× | 11.3× | *Jaws 2*, *Jaws 3-D*, *Jaws: The Revenge* |
| Star Wars | 10.8× | 6.2× | *The Force Awakens*, *The Last Jedi*, *The Rise of Skywalker* |
| Jurassic Park | 8.9× | 5.0× | the four *Jurassic World* films |
| Indiana Jones | 7.1× | 4.1× | *Dial of Destiny* |
| Terminator | 2.8× | 2.5× | *Genisys*, *Dark Fate* |

- **The shortlist survives:**
  - *The Lord of the Rings* and *The Avengers* are complete on the list, so their numbers don't change.
  - *Ice Age* drops from 8.4× to 7.5×, still second. One of its missing films, *The Ice Age Adventures of Buck Wild*, went straight to streaming and has no box office figures, which is noted in the output.
- **It also shows films not yet released.** *The Avengers* has *Avengers: Doomsday* (Dec 2026) and *Avengers: Secret Wars* (Dec 2027) coming, and *Ice Age* has *Ice Age: Boiling Point* (Jan 2027). A "complete" bundle today may grow, so the contract should say whether future films are included. These 7 upcoming films are listed in `out/bundle_films.csv` (`released` = False).

- **It answers last quarter's question.** Kwame doesn't know whether passing on a five-film bundle was a miss. Six franchises on the list have exactly five films. Counted whole, their typical return is 3.65× (Toy Story 5.62×, Indiana Jones 4.13×, Die Hard 3.68×, Pirates 3.62×, Bourne 3.60×, Mad Max 2.16×), below a typical recent standalone (3.84×). Unless the bundle was Toy Story-strength, passing was more likely right. The same check on that exact bundle would settle it.

## What it is worth to them
- **To Kwame:** before he puts a price on any bundle, he can see exactly which films he'd be buying and what they did as a set. It stops a repeat of the trilogy that underperformed: a bundle that looks strong on its best entries but carries weak ones nobody put on the list. It also gives his negotiators a concrete point ("three of the six films returned under 3×").
- **To Adjoa:** it reruns every quarter with no extra work, and it catches a franchise that grows (a new sequel appears in TMDb and shows up as "missing") without anyone having to remember to look.

## Limits
- Films with no box office (straight-to-streaming or direct-to-video) count as missing but can't be priced. The column `missing_without_money` shows how many.
- It relies on TMDb's grouping of franchises, the same as ADR-002.
- It adds network calls: this year, 32 franchise lists plus 39 films, about 37 seconds the first time and instant after that.
- TMDb data for films outside the list is not cleaned as carefully. For example, *The Lion King 1½* (direct-to-video) shows a revenue of $1,465 with no budget, so it is left out as "no money figures" rather than counted.
