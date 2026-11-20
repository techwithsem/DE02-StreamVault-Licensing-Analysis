# DE02 – StreamVault Licensing Analysis

This project settles one question for StreamVault's content team, using live data from TMDb: **do franchise bundles or standalone hits make the better back-catalogue licence?** It reads the candidate list (`data/id_list.csv`), fetches every film from TMDb, checks the data, and works out the answer for all years and for films released in 2000 onward.

**Start here:**
- [docs/client-memo.md](docs/client-memo.md): the recommendation, in one page.
- [docs/findings.md](docs/findings.md): what was wrong with the data, and where each of the 127 ids went.
- [docs/adr/](docs/adr/): every judgement call, and what it costs if it's wrong.
- [docs/measurement-report.md](docs/measurement-report.md): how fast it runs, and at 500 titles.
- [docs/spot-check.md](docs/spot-check.md): my output checked against TMDb live.
- [docs/improvements.md](docs/improvements.md): the bundle completeness check.
- [out/summary.md](out/summary.md): the key numbers, rebuilt on every run.
- [profiling/](profiling/): the data-quality files (column profile, warning flags, hard checks, join proof, number and date conversion), rebuilt on every run.

---

## Setup (once)

You need **Python 3.11 or newer** (tested end to end on 3.14; the pinned packages also install on 3.11) and a free **TMDb API key**.

**1. Get the code and open a terminal in the project folder**

```bash
git clone https://github.com/techwithsem/DE02-StreamVault-Licensing-Analysis.git
cd DE02-StreamVault-Licensing-Analysis
```

**2. Create and switch on a virtual environment**

```bash
python -m venv .venv
```

| System | Command to switch it on |
|---|---|
| Windows PowerShell | `.\.venv\Scripts\Activate.ps1` |
| Windows CMD | `.venv\Scripts\activate.bat` |
| Mac / Linux | `source .venv/bin/activate` |

In VS Code, also press `Ctrl+Shift+P` → **Python: Select Interpreter** → pick the one inside `.venv`.

**3. Install the packages** (exact versions are pinned)

```bash
pip install -r requirements.txt
```

**4. Add your TMDb key**

Copy `.env.example` to a new file called `.env` and put your key after the `=`:

```env
TMDB_API_KEY=put_your_tmdb_api_key_here
```

Get a key at <https://www.themoviedb.org/settings/api>. The short "API Key" or the long "API Read Access Token" both work. **Never commit `.env`;** it's already in `.gitignore`.

---

## Running it

| Command | What it does | Time |
|---|---|---|
| `python StreamVault.py` | The full analysis. Uses saved TMDb answers where they exist. | under 2 s with saved answers; about 3 min on a first run with none |
| `python StreamVault.py --spot-check` | The same, plus re-checks 14 films against TMDb live. | about 15 s more |
| `python StreamVault.py --refresh` | Ignores saved answers and fetches everything again (do this each quarter). | about 3 min |
| `python -m pytest` | Runs the 25 tests. They use a fake TMDb, so no key or internet is needed. | about 2 s |
| `python scripts/scale_test.py` | Times the analysis at 127, 500 and 5,000 titles. | about 3 min |
| `python scripts/benchmark_apply.py` | Times row-by-row against whole-column maths. | a few seconds |

**The run stops with a clear message if:**
- the key is missing or wrong
- a film fails to download (run it again: saved films are not fetched twice)
- a data check fails, for example two rows for the same film

It prints a **warning** if the analysis goes over its 10-second budget.

---

## Next quarter (Adjoa's checklist)

1. Replace `data/id_list.csv` with the new list (one column of TMDb ids; IMDb ids like `tt0468569` are fine too).
2. Run `python StreamVault.py --refresh --spot-check`.
3. Open `out/summary.md`. Check the line under "does the answer change" and the film counts in brackets.
4. Open `data/id_accounting.csv` to see which rows were dropped, and why.
5. Open `out/bundle_completeness.csv` before pricing any franchise.
6. Quote the snapshot date at the top of `out/summary.md` in anything you send.

To change a rule, edit one setting. Every one is explained in `docs/adr/`.

| Rule | Where to change it |
|---|---|
| Time budget | `TIME_BUDGET_SECONDS` in `pipeline/config.py` |
| Where the second window starts (2000) | `WINDOWS` in `pipeline/kpis.py` |
| What counts as a franchise | `DEFAULTS["franchise_rule"]` in `pipeline/kpis.py` |
| Minimum films for the talent table | `min_films` in `pipeline/kpis.py` |

---

## How it works

| Stage | What happens | Code | Output |
|---|---|---|---|
| 1. Fetch | Reads the id list as text, sorts every row (TMDb id, IMDb id, blank, junk), translates IMDb ids, marks repeats, fetches details and credits once per film, and saves every answer with a timestamp. | `pipeline/ids.py`, `fetch.py`, `acquire.py` | `data/id_accounting.csv`, `data/fetch_log.csv`, `data/raw/` |
| 2. Flatten | Turns the saved answers into tables: one row per film, one row per film per cast credit, one row per film per director. | `pipeline/flatten.py` | `out/films.csv` |
| 3. Check | Profiles every column, flags anything odd (never deletes), and stops if a hard check fails. | `pipeline/checks.py` | `profiling/checks.csv`, `profiling/profile.csv`, `profiling/flags.csv`, `profiling/flagged_films.csv`, `profiling/joins.csv`, `profiling/parse_report.csv` |
| 4. KPIs | Return per dollar of budget, franchise vs standalone, both windows, under four cleaning choices; first film vs sequels; franchise and talent tables; shortlist. No row loops. | `pipeline/kpis.py`, `analysis.py` | `out/kpi_by_window.csv`, `out/sensitivity.csv`, `out/entry_pattern.csv`, `out/franchises_*.csv`, `out/standalones.csv`, `out/talent.csv`, `out/shortlist_*.csv` |
| 5. Write | Saves every table, a plain-English summary and the timings. | `pipeline/report.py` | `out/summary.md`, `out/timing.csv` |
| Bundles | Fetches each franchise's full film list, to show what a whole bundle earned. | `pipeline/bundles.py` | `out/bundle_completeness.csv`, `out/bundle_films.csv` |
| Spot-check | Re-fetches a chosen sample live and compares it with the pipeline's output. | `pipeline/spotcheck.py` | `out/spot_check.csv` |

**About the saved answers (`data/raw/`).** They're committed on purpose, so anyone who clones the project gets the exact numbers in the memo (snapshot of 20 Nov 2026) without calling TMDb. Use `--refresh` to update them. They hold no API key.

