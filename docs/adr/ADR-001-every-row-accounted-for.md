# ADR-001: Count each film once, and keep every input row on record

**Status:** accepted · **Findings:** F06, F07, F11, F17, F18

## Context
The 127-row list came from three sources over four years. It contains 7 repeated ids (one disguised as an IMDb id), 5 ids TMDb does not know, a blank row, `-1` and `N/A`. The brief says every id must be accounted for, and that deleting without checking costs more than keeping and explaining.

## Decision
- `data/id_list.csv` is never edited.
- Every input row gets one outcome in `data/id_accounting.csv` (kept, duplicate of row N, not found, invalid, blank, placeholder). The run stops if any row has no outcome.
- IMDb ids (`tt…`) are translated to TMDb ids with TMDb's `/find` before duplicates are checked, so a repeat in disguise is caught.
- Each distinct film is fetched once and counted once in the analysis. Duplicates point to the first row that named the film.
- A film is "the same" if TMDb gives it the same id. Same title and year under two ids would be flagged for a person to look at, not merged.

## Alternative rejected
Counting each row as it appears (so *The Dark Knight* counts three times). This treats the list as a vote, not as a set of films.

## Cost if wrong
If the repeats were deliberate (for example, a source saying "this one twice as important"), I have under-weighted 6 films. Under the alternative, the standalone median falls from 3.84× to 3.24× and the franchise lead grows from 1.78× to 2.39× (all years). The recommendation is the same either way: franchises lead. Source: `out/sensitivity.csv`, scenario "count duplicate rows again".

## What survives
All of it. The rules are written as code with tests (`tests/test_ids.py`, `tests/test_fetch.py`), so next year's 500 rows are sorted the same way and the counts must still add up, or the run stops. New kinds of bad value (say, `#N/A` or an id with a letter in it) land in "not a valid id", not in the analysis.
