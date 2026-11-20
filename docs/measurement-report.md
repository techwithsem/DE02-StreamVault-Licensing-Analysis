# Measurement report: analysis run time

## Target
Stages 2 to 5 must finish within **10 seconds** for next year's list of about 500 titles, on an ordinary laptop. That covers: read the saved TMDb answers, build the tables, run the checks, compute every KPI for both windows and all four cleaning scenarios, and write the outputs. The reasons for the target are in ADR-008. The value is set in `pipeline/config.py` (`TIME_BUDGET_SECONDS`).

## Method
| Item | Detail |
|---|---|
| Machine | Windows 11 laptop, 8 logical CPUs, 16 GB RAM, project folder on OneDrive |
| Software | Python 3.14, pandas 3.1.1, NumPy 2.4.6 (pinned in `requirements.txt`) |
| What is timed | From the start of stage 2 (reading `data/raw/`) to the end of stage 5 (all files in `profiling/` and `out/` written). Timed with `time.perf_counter()`. |
| What is not timed | Stage 1 (downloads), the bundle check and the spot-check. These depend on TMDb and the network, so they're timed and printed separately. |
| Runs | The real 127-row list: one run per `python StreamVault.py`. The scaling test: 5 runs per size, and I report the **median** run. |
| Warm or cold | Warm: the saved answers already on disk, Python already installed. The first run after installing can be much slower on this laptop, because Windows security scans new files (seen once at about 7 minutes for the test suite). That is outside my code, so it's left out of the figures. |
| Test data at 500 and 5,000 | The 112 real films copied under new ids (each copy gets its own franchise id), written to a temporary folder. Same shape as real data; no network. |
| How to reproduce | `python StreamVault.py` (prints the per-stage table, writes `out/timing.csv`) · `python scripts/scale_test.py` → `out/scale_test.csv` · `python scripts/benchmark_apply.py` → `out/benchmark_apply.csv` |

## Results

### The real run (127 input rows, 112 films)
| Stage | Seconds |
|---|---:|
| 2: read saved answers and build tables | 0.864 |
| 3: checks and profile | 0.035 |
| 4: KPIs, both windows, all scenarios | 0.458 |
| 5: write outputs | 0.067 |
| **Total** | **1.424** (budget 10) |

This is the last of three back-to-back runs (2.10 s, 1.45 s, 1.42 s). On an earlier day the same code took 0.86 s, and after the final audit changes it took 0.96 s. `out/timing.csv` is rewritten on every run, so it always shows the latest run, not these figures. Downloads (stage 1) took 137.5 s the first time (234 calls) and 0.2 s on later runs (all from the saved copies).

### Growing the list
| Titles | Median of 5 (s) | Slowest (s) | Stage 2 (s) | Stage 3 (s) | Stage 4 (s) | Per title (ms) |
|---:|---:|---:|---:|---:|---:|---:|
| 127 | 1.70 | 1.77 | 1.08 | 0.04 | 0.59 | 13.4 |
| **500** | **3.50** | **5.22** | 3.05 | 0.04 | 0.43 | 7.0 |
| 5,000 | 33.91 | 35.41 | 33.05 | 0.09 | 0.56 | 6.8 |

Above 500 titles, the time per title stays flat at about 7 ms, so the run grows in a straight line. (At 127 titles, fixed start-up costs make the per-title figure look higher.) **500 titles take about 3.5 seconds, with the slowest of 5 runs at 5.2 seconds, inside the budget.** Stage 2 (opening and reading about 1,000 small files) is about 90% of the time. The KPI stage hardly grows: about half a second whether there are 127 titles or 5,000.

### Before and after: row by row vs whole column
The core calculation (return multiple, franchise or standalone, median per group), written both ways, with the same answer checked each time:

| Titles | Row by row (`apply`, before) | Whole column (after) | Faster by |
|---:|---:|---:|---:|
| 127 | 43.2 ms | 1.51 ms | 29× |
| 500 | 167.5 ms | 1.61 ms | 104× |
| 5,000 | 1,939.4 ms | 5.21 ms | 372× |

The gap widens as the list grows: row-by-row time rises with every film, while the whole-column version hardly moves. The pipeline uses only the whole-column version, and a test fails if a row loop is added (`test_no_row_loops_in_the_analysis_code`).

## Caveats
- **Single machine, noisy:** all figures come from one laptop, and the same code took between 0.86 s and 2.10 s on different runs. Windows security scanning and OneDrive syncing both add noise. Adjoa's laptop may be slower; even the slowest 500-title run (5.2 s) leaves room for her laptop to be nearly twice as slow before reaching the budget.
- **OneDrive:** the project sits in a OneDrive folder, which can slow down reading many small files. A local folder would likely be faster.
- **Made-up titles:** the 500 and 5,000 lists are copies of real films. Real new films with very long cast lists would add a little to stage 2.
- **If the budget is tighter than 3 seconds:** the fix is to save the flattened tables to one file after the first read, which skips about 1,000 file opens. It isn't done now because the current version is simpler for Adjoa to follow.
- **Not timed:** the downloads. At 500 titles, expect about 10 minutes for the first fetch (with polite pauses). After that, every run uses the saved copies.
