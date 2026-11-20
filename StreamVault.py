"""streamvault licensing analysis: the one command that is running everything.

    python StreamVault.py               # using saved api answers where they exist
    python StreamVault.py --refresh     # asking tmdb again for every film
    python StreamVault.py --spot-check  # also re-checking a sample of films live
"""

import argparse
import sys
import time

import pandas as pd

from pipeline import acquire, analysis, bundles, config, joins, manifest, report, spotcheck
from pipeline.fetch import make_session


def print_table(title, rows):
    print(f"\n{title}")
    for name, value in rows:
        print(f"  {value:>10}  {name}")


def main():
    parser = argparse.ArgumentParser(description="streamvault licensing analysis")
    parser.add_argument("--refresh", action="store_true",
                        help="ignore saved api answers and fetch everything again")
    parser.add_argument("--spot-check", action="store_true",
                        help="re-fetch a chosen sample live and compare it with the pipeline's output")
    args = parser.parse_args()

    session = make_session(config.get_api_key())
    joins.JOIN_LOG.clear()          # starting a fresh record of every join

    # ---- stage 1: fetching (network, so timed apart from the analysis) ----
    print("stage 1: fetching films from tmdb")
    t = time.perf_counter()
    accounting, fetch_log = acquire.run(session, refresh=args.refresh)
    fetch_seconds = time.perf_counter() - t

    counts = accounting["outcome"].value_counts()
    assert counts.sum() == len(accounting), "some input rows have no outcome"
    print_table(f"where the {len(accounting)} input rows went", list(counts.items()))
    print(f"  live calls: {(~fetch_log['from_cache']).sum()}, from cache: "
          f"{fetch_log['from_cache'].sum()}, took {fetch_seconds:.1f}s")

    unresolved = accounting["outcome"].str.startswith("unresolved")
    if unresolved.any():
        sys.exit(f"\n{unresolved.sum()} films failed to fetch. run the command again to "
                 "retry them; saved answers will not be fetched twice.")

    kept_ids = accounting.loc[accounting["outcome"].str.startswith("kept"), "tmdb_id"].astype(int).tolist()

    # ---- stages 2 to 4: the analysis, from the cache ----
    print("\nstages 2-4: building tables, checking them, computing kpis")
    results, timings = analysis.run_timed(kept_ids, accounting)

    # ---- stage 5: writing outputs ----
    t = time.perf_counter()
    df = results["analysis_table"]
    # writing the data-quality files to profiling/, kept apart from the answers
    profile_files = {
        "profile.csv": results["profile"], "flags.csv": results["flag_summary"],
        "flagged_films.csv": results["flagged"], "checks.csv": results["checks"],
        "parse_report.csv": results["parsing"],
    }
    for name, table in profile_files.items():
        report.write_csv(table, name, folder=report.PROFILE_DIR)

    outputs = {
        "films.csv": results["films"],
        "kpi_by_window.csv": results["windows"], "sensitivity.csv": results["sensitivity"],
        "entry_pattern.csv": results["entry_pattern"],
        "franchises_all_years.csv": results["franchises_all_years"],
        "franchises_2000_onward.csv": results["franchises_2000_onward"],
        "standalones.csv": results["standalones"], "talent.csv": results["talent"],
        "shortlist_franchises.csv": results["franchise_shortlist"],
        "shortlist_standalones.csv": results["standalone_shortlist"],
    }
    for name, table in outputs.items():
        report.write_csv(table, name)
    snapshot = pd.concat([results["films"]["details_fetched_at"], results["films"]["credits_fetched_at"]])
    report.write_summary(results["windows"], results["sensitivity"], results["entry_pattern"],
                         results["franchise_shortlist"], results["standalone_shortlist"],
                         snapshot.min(), snapshot.max())
    timings["5 write outputs"] = time.perf_counter() - t

    total = sum(timings.values())
    timing_table = pd.DataFrame({"stage": list(timings), "seconds": list(timings.values())})
    timing_table.loc[len(timing_table)] = ["total (stages 2-5)", total]
    report.write_csv(timing_table, "timing.csv", round_to=4)
    print_table("time per stage (seconds)", [(s, f"{v:.3f}") for s, v in timings.items()])
    print(f"  {total:>10.3f}  total, budget {config.TIME_BUDGET_SECONDS}s")
    if total > config.TIME_BUDGET_SECONDS:
        print(f"\nWARNING: the analysis took {total:.1f}s, over the "
              f"{config.TIME_BUDGET_SECONDS}s budget.", file=sys.stderr)

    # ---- improvement: how complete is each franchise bundle? (network, cached) ----
    t = time.perf_counter()
    bundle_summary, bundle_films = bundles.run(session, results["films"], refresh=args.refresh)
    report.write_csv(bundle_summary, "bundle_completeness.csv")
    report.write_csv(bundle_films, "bundle_films.csv")
    print(f"\nbundle completeness: {int(bundle_summary['films_missing'].sum())} released franchise "
          f"films are not on the list ({time.perf_counter() - t:.1f}s)")

    # writing the proof that every join kept the rows it should have
    report.write_csv(joins.log_table(), "joins.csv", folder=report.PROFILE_DIR)

    # tying data/raw to one snapshot: listing every saved answer with its checksum
    saved, drift = manifest.update()
    if drift is None:
        print(f"\nsnapshot manifest: created for {len(saved)} saved answers")
    elif any(drift.values()):
        print(f"\nsnapshot manifest: {drift['added']} added, {drift['removed']} removed, "
              f"{drift['changed']} changed since the last run. quote the new snapshot date.")
    else:
        print(f"\nsnapshot manifest: all {len(saved)} saved answers unchanged")

    # ---- stage 6 (on request): spot-check against tmdb live ----
    if args.spot_check:
        print("\nspot-check: re-fetching a sample live from tmdb")
        check = spotcheck.run(session, df, results["cast"], results["directors"],
                              results["flagged"], accounting)
        report.write_csv(check, "spot_check.csv")
        print_table("spot-check result (film x field)", list(check["class"].value_counts().items()))

    print(f"\ndone. results are in {report.OUT_DIR.name}/ (start with summary.md), "
          f"data-quality files in {report.PROFILE_DIR.name}/")


if __name__ == "__main__":
    main()
