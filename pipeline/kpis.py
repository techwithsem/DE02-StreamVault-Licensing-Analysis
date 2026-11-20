"""stage 4: computing the kpis, for both time windows, under every cleaning choice.

no loops over rows: everything here is whole-column maths or groupby.
the only loops are over a handful of scenarios and the two windows.
"""

import pandas as pd

from pipeline.joins import checked_merge

# the choices i made, and the alternatives i am testing them against
DEFAULTS = {"franchise_rule": "any_collection",
            "revenue_estimates": "keep",
            "duplicates": "count_once"}

SCENARIOS = {
    "chosen approach": {},
    "franchise = 2+ films on the list": {"franchise_rule": "two_plus_on_list"},
    "drop round-number revenues": {"revenue_estimates": "exclude"},
    "count duplicate rows again": {"duplicates": "count_each_row"},
}

WINDOWS = {"all years": None, "2000 onward": 2000}


def prepare(films, accounting, franchise_rule="any_collection",
            revenue_estimates="keep", duplicates="count_once"):
    """building the analysis table for one set of cleaning choices."""
    df = films.copy()

    if duplicates == "count_each_row":
        # repeating each film once per input row that named it (the uncleaned list)
        named = accounting.loc[accounting["tmdb_id"].notna()
                               & ~accounting["outcome"].str.contains("no film|no tmdb"),
                               "tmdb_id"].astype(int).value_counts()
        df = df.loc[df.index.repeat(df["tmdb_id"].astype(int).map(named).fillna(1).astype(int))]
        df = df.reset_index(drop=True)

    has_collection = df["collection_id"].notna()
    if franchise_rule == "any_collection":
        df["is_franchise"] = has_collection
    else:
        on_list = df.groupby("collection_id")["tmdb_id"].transform("nunique")
        df["is_franchise"] = has_collection & on_list.ge(2)
    df["group"] = df["is_franchise"].map({True: "franchise", False: "standalone"})

    # return multiple: box office earned per dollar of budget. both figures are in the
    # same year's dollars, so inflation cancels out of the ratio
    usable = df["budget"].gt(0) & df["revenue"].gt(0)
    if revenue_estimates == "exclude":
        usable &= ~df["revenue"].mod(1_000_000).eq(0)
    df["multiple"] = (df["revenue"] / df["budget"]).where(usable).astype("float64")
    return df


def in_window(df, start_year):
    return df if start_year is None else df[df["release_year"].ge(start_year)]


def headline(df):
    """grain: one row per group (franchise or standalone)."""
    g = df.groupby("group")
    out = g.agg(
        films=("tmdb_id", "size"),
        usable=("multiple", "count"),
        median_multiple=("multiple", "median"),
        mean_multiple=("multiple", "mean"),
        q1_multiple=("multiple", lambda s: s.quantile(0.25)),
        q3_multiple=("multiple", lambda s: s.quantile(0.75)),
        median_revenue=("revenue", "median"),
        median_rating=("vote_average", "median"),
    )
    out["share_under_2x"] = df["multiple"].lt(2).groupby(df["group"]).mean()
    return out.reset_index()


def compare_windows(films, accounting, **options):
    """grain: one row per window per group."""
    df = prepare(films, accounting, **{**DEFAULTS, **options})
    parts = [headline(in_window(df, start)).assign(window=name) for name, start in WINDOWS.items()]
    return pd.concat(parts, ignore_index=True)[["window", *headline(df).columns]]


def sensitivity(films, accounting):
    """grain: one row per scenario per window, showing who leads under each choice."""
    rows = []
    for scenario, options in SCENARIOS.items():
        table = compare_windows(films, accounting, **options)
        wide = table.pivot(index="window", columns="group", values=["median_multiple", "usable"])
        wide.columns = [f"{group}_{stat}" for stat, group in wide.columns]
        rows.append(wide.reset_index().assign(scenario=scenario))
    out = pd.concat(rows, ignore_index=True)
    out["gap"] = out["franchise_median_multiple"] - out["standalone_median_multiple"]
    out["leader"] = out["gap"].gt(0).map({True: "franchise", False: "standalone"})
    return out[["scenario", "window", "franchise_median_multiple", "franchise_usable",
                "standalone_median_multiple", "standalone_usable", "gap", "leader"]]


def entry_pattern(df):
    """testing the 'weak middle entries' claim: first film in a franchise vs the ones after.

    grain: one row per entry position.
    """
    fr = df[df["is_franchise"]].copy()
    count = fr.groupby("collection_id")["tmdb_id"].transform("size")
    order = fr.groupby("collection_id")["release_date"].rank(method="first")
    fr["position"] = "middle entry"
    fr.loc[order.eq(1), "position"] = "first entry"
    fr.loc[order.eq(count) & count.gt(1), "position"] = "latest entry on list"
    fr = fr[count.gt(1)]          # a franchise with one film on the list has no sequence
    return (fr.groupby("position")
              .agg(films=("tmdb_id", "size"), median_multiple=("multiple", "median"),
                   median_rating=("vote_average", "median"))
              .reindex(["first entry", "middle entry", "latest entry on list"])
              .reset_index())


def franchise_table(df):
    """grain: one row per franchise (tmdb collection)."""
    fr = df[df["is_franchise"]]
    weakest = fr.loc[fr.groupby("collection_id")["multiple"].idxmin(), ["collection_id", "title", "multiple"]]
    out = (fr.groupby(["collection_id", "collection_name"])
             .agg(films_on_list=("tmdb_id", "size"),
                  first_year=("release_year", "min"),
                  last_year=("release_year", "max"),
                  median_multiple=("multiple", "median"),
                  total_budget=("budget", "sum"),
                  total_revenue=("revenue", "sum"),
                  median_rating=("vote_average", "median"),
                  median_votes=("vote_count", "median"))
             .reset_index())
    out["bundle_multiple"] = out["total_revenue"] / out["total_budget"]
    out = out.merge(weakest.rename(columns={"title": "weakest_film", "multiple": "weakest_multiple"}),
                    on="collection_id", how="left", validate="one_to_one")
    return out.sort_values("median_multiple", ascending=False).reset_index(drop=True)


def standalone_table(df):
    """grain: one row per standalone film."""
    cols = ["tmdb_id", "title", "release_year", "budget", "revenue", "multiple",
            "vote_average", "vote_count"]
    return df.loc[~df["is_franchise"], cols].sort_values("multiple", ascending=False).reset_index(drop=True)


def talent_table(df, people, role, min_films=2, window="all years"):
    """grain: one row per person, for people with at least min_films films on the list."""
    # an inner join on purpose: credits for films outside the window are left out.
    # many_to_one stops the run if a film appeared twice, which would double-count people
    joined = checked_merge(people, df[["tmdb_id", "title", "multiple", "vote_average"]],
                           f"{role} credits <- films ({window})", keep_rows=False,
                           on="tmdb_id", how="inner", validate="many_to_one")
    assert len(joined) <= len(people), f"joining {role}s to films created extra rows"
    overall = df["multiple"].median()
    out = (joined.groupby(["person_id", "name"])
                 .agg(films=("tmdb_id", "nunique"),
                      median_multiple=("multiple", "median"),
                      worst_multiple=("multiple", "min"),
                      median_rating=("vote_average", "median"),
                      titles=("title", " | ".join))
                 .reset_index())
    out = out[out["films"].ge(min_films)].copy()
    out["vs_typical_film"] = out["median_multiple"] / overall
    out["role"] = role
    return out.sort_values(["median_multiple", "films"], ascending=False).reset_index(drop=True)
