"""stage 3: profiling the data and turning every assumption into a check.

hard checks stop the run if they fail. soft checks are flags that a person
should look at; they feed the findings, they do not delete anything.
"""

import pandas as pd


def _as_text(value):
    """showing whole numbers without ".0" and dates without a time."""
    if pd.isna(value):
        return ""
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def profile(films):
    """summarising every column: type, gaps, zeros, range and the most repeated value."""
    # grain: one row per column of the films table (the loop is over columns, not rows)
    rows = []
    for name in films.columns:
        col = films[name]
        counts = col.value_counts(dropna=True)
        repeats = counts.iloc[0] > 1 if len(counts) else False
        has_range = pd.api.types.is_numeric_dtype(col) or pd.api.types.is_datetime64_any_dtype(col)
        rows.append({
            "column": name,
            "dtype": str(col.dtype),
            "missing": int(col.isna().sum()),
            "distinct": int(col.nunique(dropna=True)),
            # showing a "most common" value only when it really repeats
            "most_common": _as_text(counts.index[0]) if repeats else "",
            "times": int(counts.iloc[0]) if repeats else "",
            "zeros": int(col.eq(0).sum()) if pd.api.types.is_numeric_dtype(col) else "",
            "min": _as_text(col.min()) if has_range else "",
            "max": _as_text(col.max()) if has_range else "",
        })
    summary = pd.DataFrame(rows)

    # writing a plain note so a reader knows which patterns are expected
    n = len(films)
    summary["note"] = ""
    all_different = summary["distinct"].eq(n) & summary["missing"].eq(0)
    summary.loc[all_different, "note"] = "every film has a different value"
    summary.loc[summary["distinct"].eq(1), "note"] = "only one value in the whole table"
    is_collection = summary["column"].str.startswith("collection_")
    summary.loc[is_collection & summary["missing"].gt(0), "note"] = (
        "missing means the film is standalone (no franchise), which is expected")
    summary.loc[summary["column"].isin(["budget", "revenue"]) & summary["zeros"].eq(0), "note"] = (
        "no zeros, so no hidden 'unknown' values this year")
    return summary


def flag_films(films):
    """adding yes/no flags that point at rows worth a second look."""
    f = films.copy()
    f["flag_zero_budget"] = f["budget"].fillna(0).eq(0)
    f["flag_zero_revenue"] = f["revenue"].fillna(0).eq(0)
    # a revenue ending in six zeros is usually a press estimate, not a counted figure
    f["flag_round_revenue"] = f["revenue"].gt(0) & f["revenue"].mod(1_000_000).eq(0)
    # a budget under $100k for a cinema release is usually a units mistake
    f["flag_tiny_budget"] = f["budget"].between(1, 99_999)
    f["flag_not_released"] = f["status"].ne("Released")
    f["flag_bad_date"] = f["release_date"].isna()
    # films before 1990 have usually picked up re-release revenue on top of the first run
    f["flag_pre_1990"] = f["release_year"].lt(1990)
    # the same title and year twice would be the same film under two ids
    key = f["title"].str.strip().str.casefold() + "|" + f["release_year"].astype("string")
    f["flag_same_title_year"] = key.duplicated(keep=False)
    # a film whose franchise has only this one film on the candidate list
    on_list = f.groupby("collection_id")["tmdb_id"].transform("count")
    f["flag_alone_in_collection"] = f["collection_id"].notna() & on_list.eq(1)
    # films with a much higher or lower return than the rest (iqr rule), to look at, not to drop
    multiple = f["revenue"] / f["budget"].where(f["budget"].gt(0))
    q1, q3 = multiple.quantile([0.25, 0.75])
    f["flag_extreme_return"] = (multiple < q1 - 1.5 * (q3 - q1)) | (multiple > q3 + 1.5 * (q3 - q1))
    return f


def run_checks(accounting, films, cast, directors, credit_ids, parsing=None):
    """checking every assumption the analysis rests on. returns one row per check."""
    unread = 0 if parsing is None else int(parsing["could_not_read"].sum())
    kept = accounting["outcome"].str.startswith("kept")
    kept_ids = set(accounting.loc[kept, "tmdb_id"].astype(int))
    checks = [
        # name, passed, hard?, detail
        ("every input row has an outcome",
         accounting["outcome"].notna().all() and len(accounting) == accounting["input_row"].nunique(),
         True, f"{len(accounting)} input rows"),
        ("one film row per kept id",
         len(films) == len(kept_ids) and set(films["tmdb_id"].astype(int)) == kept_ids,
         True, f"{len(films)} film rows, {len(kept_ids)} kept ids"),
        ("film id is unique", films["tmdb_id"].is_unique, True, ""),
        ("credits belong to the film asked for",
         set(credit_ids.astype(int)) == kept_ids, True, ""),
        ("every film has cast", cast["tmdb_id"].nunique() == len(films), True,
         f"{cast['tmdb_id'].nunique()} of {len(films)} films have cast rows"),
        ("every film has a lead actor (billing order 0)",
         cast.loc[cast["billing_order"].eq(0), "tmdb_id"].nunique() == len(films), True, ""),
        ("every film has a director", directors["tmdb_id"].nunique() == len(films), True,
         f"{directors['tmdb_id'].nunique()} of {len(films)} films"),
        ("imdb id is unique across films", films["imdb_id"].dropna().is_unique, False, ""),
        # a soft check: a value that failed to convert is a finding, not a reason to stop
        ("every number and date could be read", unread == 0, False,
         f"{unread} values could not be read (see parse_report.csv)"),
        ("no money is negative",
         bool(films["budget"].ge(0).all() and films["revenue"].ge(0).all()), True, ""),
        ("release year is plausible (1900 to next year)",
         bool(films["release_year"].between(1900, pd.Timestamp.now().year + 1).all()), True,
         f"{films['release_year'].min()} to {films['release_year'].max()}"),
    ]
    report = pd.DataFrame(checks, columns=["check", "passed", "hard", "detail"])
    failed_hard = report[report["hard"] & ~report["passed"]]
    if len(failed_hard):
        raise SystemExit("data checks failed:\n" + failed_hard.to_string(index=False))
    return report


def flag_summary(flagged):
    """counting how many films each flag points at."""
    cols = [c for c in flagged.columns if c.startswith("flag_")]
    return (flagged[cols].sum().rename("films_flagged").rename_axis("flag").reset_index())
