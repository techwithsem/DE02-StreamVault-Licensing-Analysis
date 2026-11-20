# Data findings: StreamVault candidate list

**Data snapshot:** TMDb answers fetched 20 Nov 2026, 07:54–07:56 UTC (stored in `data/raw/`).
**Rebuild the evidence:** `python StreamVault.py` (every number below comes from a file in `data/`, `profiling/` or `out/`).

## Summary

The list I was given has 127 rows. 112 of them became films in the analysis. The other 15 are accounted for below, and none were deleted from the source file.

The faults that matter most are not untidy rows. They are gaps in what the list can tell me:
- most franchises are only partly on the list
- the revenue for older films seems to include later re-releases
- there are only 16 standalone films to compare against

None of these changes the answer (franchises earn more per film), but they change how big the lead is. They are ranked here by how much they could move the recommendation.

---

## 1. Where every one of the 127 rows went

Source: [`data/id_accounting.csv`](../data/id_accounting.csv) (one row per line of `id_list.csv`).

| Outcome | Rows | Input rows (line in file) |
|---|---:|---|
| Kept: details and credits fetched | 112 | — |
| Duplicate of an earlier row | 7 | 43, 60, 90, 91, 94, 95, 102 |
| TMDb has no film with this id | 5 | 18, 35, 73, 93, 99 |
| Not a valid id (`-1`) | 1 | 30 |
| Blank row | 1 | 69 |
| Placeholder text (`N/A`) | 1 | 111 |
| **Total** | **127** | Checked by code on every run (`every input row has an outcome`). |

Reconciliation: 112 + 7 + 5 + 1 + 1 + 1 = 127. The 112 kept rows are 112 different films, with no film counted twice.

**What the gap costs:** 15 rows (12%) did not become films. 10 of them (the 7 duplicates, the blank and the two text entries) cost nothing, because they never pointed to a film I am missing. The real loss is the **5 dead ids**: I cannot know which films they were meant to be, so if any was a strong title, it is missing from the shortlist. That is 5 of 117 distinct ids (4%).

---

## 2. Findings, ranked by risk to the recommendation

"Risk" means how far the fault could move the franchise-vs-standalone answer or the shortlist. It does not mean how odd the fault looked.

| ID | What I saw | The spec said | Verdict | Decision | Handled in | Proved by | Decided in |
|---|---|---|---|---|---|---|---|
| F01 | **Most franchises are only partly on the list.** 19 of 32 franchises are missing released films (39 films in total), often the weaker later ones: *Indiana Jones and the Dial of Destiny*, *Terminator Genisys*, *A Good Day to Die Hard*. Counting the whole franchise, the median bundle return falls from 5.56× to 4.36×. Star Wars falls from 10.8× to 6.2×, Jurassic Park from 8.9× to 5.0×. | Studios sell a franchise as a bundle: "take all six or none". | **Real fault** (the list does not match what is actually sold). | Keep the film-level comparison, and add a whole-bundle check. The three shortlisted franchises hold up: two are complete, and Ice Age only slips from 8.4× to 7.5×. | `pipeline/bundles.py` | `out/bundle_completeness.csv` | ADR-002, [improvements](improvements.md) |
| F02 | **The franchise definition moves the answer most.** 9 films are the only film from their TMDb collection on the list (*Jaws*, *The Lion King*, *Blade Runner*…). If they count as standalones, the franchise lead shrinks from 1.78× to 0.53× (all years) and from 1.21× to 0.56× (2000 onward). | "Franchise bundles vs standalone hits"; the term is not defined. | **Real ambiguity**, not a data error. | A film is a franchise film if TMDb puts it in a collection, because that is how it would be sold. The other rule is computed alongside. Franchises lead under both. | `kpis.prepare(franchise_rule=…)` | `out/sensitivity.csv` | ADR-002 |
| F03 | **Older films show much bigger returns.** Median return is 11.9× before 1990, 5.9× in the 1990s and 4.9× from 2000 onward. *Star Wars* (1977) shows $775M on an $11M budget (70×) and *Jaws* 67×. Public records suggest these totals include later re-releases, but TMDb has a single revenue field, so I cannot split them. | Yaw in Finance distrusts anything released before 2000; both windows are required. | **Real risk, cannot be fully verified.** | Report both windows everywhere. Rank the shortlist on 2000-onward films. The franchise lead holds in both windows, but shrinks from 1.78× to 1.21× from 2000 onward. | `kpis.WINDOWS`, `analysis.shortlists` | `out/kpi_by_window.csv`, `out/entry_pattern.csv` | ADR-004, ADR-009 |
| F04 | **The "weak later entries" pattern only appears in the all-years view.** Across all years, first films earn 7.4×, middle ones 5.4× and the latest 4.6×. From 2000 onward the pattern is flat: 5.3×, 5.2×, 5.1×. | Half the team says StreamVault overpays for weak middle entries. | **Real, and it depends on the window.** It is probably caused by F03, because older first films carry re-release revenue. | Say so plainly in the memo. Do not use the decline as evidence on its own. | `kpis.entry_pattern` | `out/entry_pattern.csv` | ADR-004 |
| F05 | **Only 16 standalone films (8 since 2000)**, against 96 franchise films (63 since 2000). A couple of films can swing the standalone median. | Group sizes must sit beside every statistic. | **Real limit** of the list; it cannot be fixed. | Show the film count next to every figure, plus the middle-half range (IQR). Flag it in the memo as a weakness. | `kpis.headline` | `out/kpi_by_window.csv` (`usable` column) | ADR-003 |
| F06 | **Repeated ids: 7 rows.** 6 plain repeats (155, 278, 550, 603, 680, 1891) and one hidden repeat: row 95 is `tt0468569`, an IMDb id that TMDb maps to 155 (*The Dark Knight*). 5 of the 7 are in the last third of the file, which fits one source sending titles again. | The list came from three sources over four years and was never cleaned. | **Real fault.** | Count each film once. Keep every row in the accounting file with a pointer to the row it repeats. If the repeats were counted, the standalone median would fall from 3.84× to 3.24× and the lead would grow by a third (1.78× → 2.39×), because 3 of the repeats are standalones. | `ids.mark_duplicates`, `fetch.resolve_imdb_id` | `test_duplicates_point_to_the_first_row`, `test_every_input_row_gets_exactly_one_outcome`, `out/sensitivity.csv` | ADR-001 |
| F07 | **5 ids that TMDb does not know:** 8471293, 8471294, 9412887, 9412888, 7733901. Two are consecutive pairs, which looks like typing or copy errors in one source. | Every id must be accounted for. | **Real fault**, and the films behind them are unknown. | Record them as "no film with this id". They are not retried on every run (the "not found" answer is saved). | `fetch.get_cached`, `acquire.build_outcome` | `data/fetch_log.csv` (404 on details and credits) | ADR-001 |
| F08 | **The list holds only well-known hits.** Every film has more than 4,000 TMDb votes and only 2% of franchise films earned under 2×. | — | **Real limitation** (the list is pre-selected). | Results describe *these candidates*, not franchises in general. Said in the memo. | — | `profiling/profile.csv` (`vote_count` min 4,138) | ADR-003 |
| F09 | **Round-number revenues on 4 films:** *Monsters, Inc.* $650,000,000; *Revenge of the Sith* $850,000,000; *Terminator 3* $435,000,000; *Alien Resurrection* $162,000,000. These are likely estimates. | — | **Real, low impact.** | Keep them. Dropping them moves the franchise median from 5.62× to 5.85× (all years) and from 5.05× to 5.06× (2000 onward); the leader does not change. | `checks.flag_films` (`flag_round_revenue`) | `out/sensitivity.csv` | ADR-005 |
| F10 | **Money is very lopsided.** The franchise and standalone means are almost equal (8.5× and 8.3×), while the medians are not (5.6× and 3.8×). The outlier rule flags 11 films, all well-known hits. | — | **Not an error: these are real extremes.** | Keep every flagged film. Lead with the median and show the mean beside it. | `checks.flag_films` (`flag_extreme_return`) | `profiling/flagged_films.csv` | ADR-003 |
| F11 | **Blank row (line 69), `-1` (line 30) and `N/A` (line 111).** pandas silently skips blank lines when reading a CSV, which would have hidden one row (126 instead of 127). | Account for all 127. | **Real fault**, low impact. | Read the file with blank lines kept, and record each row as dropped with its reason. | `ids.load_ids` (`skip_blank_lines=False`), `ids.classify_ids` | `test_reading_keeps_every_row_as_text`, `test_sorting_each_kind_of_value` | ADR-001 |

### Checked and dismissed (false alarms)

The brief warns that not everything that looks wrong is wrong. These were looked at and kept, with the reason.

| ID | What I saw | The spec said | Verdict | Decision | Handled in | Proved by | Decided in |
|---|---|---|---|---|---|---|---|
| F12 | No film has a zero budget or zero revenue, although TMDb usually uses 0 for "unknown". | A zero can be a genuine zero, or a gap. | **Not present this year.** | The check stays in the code, so next year's list will be caught. A zero is treated as unknown and left out of returns only. | `kpis.prepare` (`usable`), `checks.flag_films` | `profiling/flags.csv` (0 films) | ADR-003 |
| F13 | *The Good, the Bad and the Ugly*: Italian-language, 1966, $1.2M budget, 32× return. | — | **Correct for that film** (a famously low-budget production). | Kept. It falls in the all-years window only. | — | `out/standalones.csv` | ADR-004 |
| F14 | One actor appears twice in the cast of *Terminator Salvation*. | — | **Genuine:** one person credited for two parts. | Kept. Talent counts distinct films, so the actor is not double-counted. | `flatten.build_cast` (grain: film × credit), `kpis.talent_table` (`nunique`) | `test_cast_keeps_every_credit_and_directors_drop_repeats` | ADR-006 |
| F15 | 9 films have 2 or 3 directors (*Shrek 2*, *Avengers: Endgame*, *The Matrix*…). | — | **Genuine co-directors.** | Each co-director gets full credit for the film. | `flatten.build_directors` | spot-check on *Shrek 2* (match) | ADR-006 |
| F16 | Titles like "Alien³" and "WALL·E" print as "Alien�" in the Windows terminal. | — | **Display only:** the data is correct. | Output files are saved so Excel shows them correctly (UTF-8 with BOM). | `report.write_csv` | open `out/films.csv` in Excel | — |
| F17 | Could TMDb answer with a different film than the id I asked for (merged records)? | — | **Not happening:** 0 of 224 answers. | The check stays in the fetch log. | `fetch.fetch_film` (`returned_id`) | `data/fetch_log.csv` | ADR-001 |
| F18 | Could the same film appear under two ids (same title and year)? | A duplicate can be two different releases. | **None found.** | Nothing removed; the check stays. | `checks.flag_films` (`flag_same_title_year`) | `profiling/flags.csv` (0 films) | ADR-001 |
| F19 | Does a film near the 2000 boundary land in the wrong window? | Both windows are required. | **No.** *Toy Story 2* (30 Oct 1999) and *Mission: Impossible II* (24 May 2000) match TMDb live. | Window = TMDb's main release date, 2000 inclusive. | `kpis.in_window` | `out/spot_check.csv` | ADR-004 |
| F20 | Budgets repeat a lot: only 60 different values across 112 films, and $150,000,000 appears 9 times. | — | **Normal:** studios report budgets as rounded figures. | Kept as they are. Returns use the reported figure. | — | `profiling/profile.csv` (`budget`: 60 distinct, most common 150000000 × 9) | ADR-003 |

---

## 3. How the faults were found

1. **Reading the raw file as text.** Every value was sorted into tmdb / imdb / blank / placeholder / invalid. Code: `pipeline/ids.py`.
2. **Accounting before analysis.** One row per input line, with an outcome that must exist for every row, or the run stops. Code: `pipeline/acquire.py`.
3. **Profiling every column:** type, missing values, zeros, min, max, most common. Output: `profiling/profile.csv`.
4. **Flags, never filters.** Each suspicious pattern adds a yes/no column. Nothing is deleted by a flag. Output: `profiling/flagged_films.csv`, counts in `profiling/flags.csv`.
5. **Hard checks that stop the run** if an assumption breaks (one row per film, every film has cast and a director, no negative money, plausible years). Output: `profiling/checks.csv`.
   - **Every join proven:** each merge states the relationship it expects (one-to-one or many-to-one), so a doubled key stops the run, and records rows before and after plus how many matched. For example, input rows ← fetch results: 127 → 127, 124 matched, and 3 left over (the blank row, `-1` and `N/A`). Output: `profiling/joins.csv`.
   - **Every conversion counted:** numbers and dates that could not be read would turn blank, so they are counted, not hidden. This year: 0 of 672 values failed. Output: `profiling/parse_report.csv`.
6. **Measuring each cleaning choice by its effect.** The full analysis runs under each alternative, and the results sit side by side. Output: `out/sensitivity.csv`.
7. **Spot-check against TMDb live:** 14 films chosen in four groups (highest and lowest return, most transformed, boundary cases, random), 7 fields each. All 98 values matched. Details: [spot-check.md](spot-check.md).

## 4. What I could not verify

- **Whether older revenues include re-releases** (F03). TMDb gives one total. This is why the shortlist is ranked on 2000-onward films.
- **What the 5 dead ids were meant to be** (F07).
- **Licensing value.** Box office return measures how a film did in cinemas, not how many people will stream it now. Budget does not include marketing. Both are stated in the memo.
