"""stages 2 to 4 as one function of the cached data, so they can be timed
together and re-run on bigger, made-up lists for the scaling test."""

import time

import pandas as pd

from pipeline import checks, flatten, kpis


def shortlists(df):
    """picking 3 franchises and 5 standalones, ranked on 2000-onward films."""
    recent = kpis.in_window(df, 2000)
    ft_recent = kpis.franchise_table(recent)
    ft_all = kpis.franchise_table(df)[["collection_id", "median_multiple"]].rename(
        columns={"median_multiple": "all_years_median"})
    # needing at least 2 films since 2000 to judge how steady a franchise is
    franchise_short = (ft_recent[ft_recent["films_on_list"].ge(2)]
                       .merge(ft_all, on="collection_id", how="left", validate="one_to_one")
                       .head(3))
    standalone_short = kpis.standalone_table(recent).head(5)
    return franchise_short, standalone_short


def analyse(films, cast, directors, accounting):
    """running every kpi. returns a dict of tables, all built without row loops."""
    df = kpis.prepare(films, accounting, **kpis.DEFAULTS)
    lead = cast[cast["billing_order"].eq(0)]
    results = {
        "windows": kpis.compare_windows(films, accounting),
        "sensitivity": kpis.sensitivity(films, accounting),
        "entry_pattern": pd.concat(
            [kpis.entry_pattern(kpis.in_window(df, s)).assign(window=w)
             for w, s in kpis.WINDOWS.items()], ignore_index=True),
        "franchises_all_years": kpis.franchise_table(df),
        "franchises_2000_onward": kpis.franchise_table(kpis.in_window(df, 2000)),
        "standalones": kpis.standalone_table(df),
        "talent": pd.concat(
            [pd.concat([kpis.talent_table(kpis.in_window(df, s), directors, "director", window=w),
                        kpis.talent_table(kpis.in_window(df, s), lead, "lead actor", window=w)])
               .assign(window=w) for w, s in kpis.WINDOWS.items()], ignore_index=True),
    }
    results["franchise_shortlist"], results["standalone_shortlist"] = shortlists(df)
    results["analysis_table"] = df
    return results


def run_timed(kept_ids, accounting):
    """running stages 2-4 and returning (results, timings in seconds per stage)."""
    timings = {}
    t = time.perf_counter()
    films, cast, directors, credit_ids, parsing = flatten.run(kept_ids)
    timings["2 flatten (read cache + build tables)"] = time.perf_counter() - t

    t = time.perf_counter()
    report = checks.run_checks(accounting, films, cast, directors, credit_ids, parsing)
    flagged = checks.flag_films(films)
    profile = checks.profile(films)
    timings["3 checks and profile"] = time.perf_counter() - t

    t = time.perf_counter()
    results = analyse(films, cast, directors, accounting)
    timings["4 kpis, both windows, all scenarios"] = time.perf_counter() - t

    results.update({"films": films, "cast": cast, "directors": directors,
                    "checks": report, "flagged": flagged, "profile": profile, "parsing": parsing,
                    "flag_summary": checks.flag_summary(flagged)})
    return results, timings
