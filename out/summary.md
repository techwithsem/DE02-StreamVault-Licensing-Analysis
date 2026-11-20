# results summary (rebuilt on every run)

data snapshot: tmdb answers fetched between 2026-11-20T07:54:14+00:00 and 2026-11-20T07:56:29+00:00 (utc).
return multiple = box office revenue / production budget, per film. median, not mean.

## franchise vs standalone

| window | group | films | median multiple | mean multiple | share under 2x |
|---|---|---|---|---|---|
| all years | franchise | 96 | 5.62x | 8.54x | 2% |
| all years | standalone | 16 | 3.84x | 8.28x | 25% |
| 2000 onward | franchise | 63 | 5.05x | 5.41x | 2% |
| 2000 onward | standalone | 8 | 3.84x | 4.90x | 12% |

## does the answer change under other cleaning choices?

| scenario | window | franchise | standalone | leader |
|---|---|---|---|---|
| chosen approach | 2000 onward | 5.05x (63) | 3.84x (8) | franchise |
| chosen approach | all years | 5.62x (96) | 3.84x (16) | franchise |
| franchise = 2+ films on the list | 2000 onward | 5.05x (59) | 4.49x (12) | franchise |
| franchise = 2+ films on the list | all years | 5.53x (87) | 5.00x (25) | franchise |
| drop round-number revenues | 2000 onward | 5.06x (60) | 3.84x (8) | franchise |
| drop round-number revenues | all years | 5.85x (92) | 3.84x (16) | franchise |
| count duplicate rows again | 2000 onward | 5.07x (65) | 3.84x (8) | franchise |
| count duplicate rows again | all years | 5.62x (100) | 3.24x (19) | franchise |

the leader is the same under every choice and in both windows.

## first film vs later films in a franchise

| window | position | films | median multiple |
|---|---|---|---|
| all years | first entry | 23 | 7.36x |
| all years | middle entry | 41 | 5.41x |
| all years | latest entry on list | 23 | 4.55x |
| 2000 onward | first entry | 17 | 5.30x |
| 2000 onward | middle entry | 22 | 5.19x |
| 2000 onward | latest entry on list | 17 | 5.07x |

## shortlist (ranked on 2000-onward films)

| franchise | films since 2000 | median multiple | weakest film | all-years median |
|---|---|---|---|---|
| The Lord of the Rings Collection | 3 | 11.73x | The Lord of the Rings: The Fellowship of the Ring (9.37x) | 11.73x |
| Ice Age Collection | 3 | 8.26x | Ice Age (6.50x) | 8.26x |
| The Avengers Collection | 4 | 6.87x | Avengers: Age of Ultron (5.98x) | 6.87x |

| standalone | year | multiple | rating |
|---|---|---|---|
| Spirited Away | 2001 | 14.47x | 8.5 |
| Inception | 2010 | 5.24x | 8.4 |
| Interstellar | 2014 | 4.52x | 8.5 |
| Memento | 2000 | 4.45x | 8.2 |
| The Departed | 2006 | 3.24x | 8.2 |
