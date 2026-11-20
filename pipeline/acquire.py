"""stage 1: turning the id list into cached api answers, plus a record of where
every input row ended up."""

import pandas as pd

from pipeline import config
from pipeline.fetch import fetch_film, resolve_imdb_id
from pipeline.ids import classify_ids, load_ids, mark_duplicates
from pipeline.joins import checked_merge


def build_outcome(df):
    """writing one plain-english outcome for every input row."""
    details = df["details_status"]
    credits = df["credits_status"]
    conditions = [
        df["id_kind"].eq("blank"),
        df["id_kind"].eq("placeholder"),
        df["id_kind"].eq("invalid"),
        df["id_kind"].eq("imdb") & df["tmdb_id"].isna(),
        df["is_duplicate"],
        details.eq("ok") & credits.eq("ok"),
        details.eq("not_found"),
        details.eq("ok") & credits.ne("ok"),
    ]
    choices = [
        "dropped: blank row",
        "dropped: placeholder text, not an id",
        "dropped: not a valid id",
        "dropped: imdb id with no tmdb match",
        "dropped: duplicate of an earlier row",
        "kept: details and credits fetched",
        "dropped: tmdb has no film with this id",
        "kept: details fetched, credits missing",
    ]
    out = df.copy()
    out["outcome"] = pd.Series(pd.NA, index=df.index, dtype="string")
    # picking the first condition that is true for each row, without a loop
    for condition, choice in zip(reversed(conditions), reversed(choices), strict=True):
        out.loc[condition.fillna(False), "outcome"] = choice
    out["outcome"] = out["outcome"].fillna("unresolved: fetch failed, re-run to retry")
    return out


def run(session, refresh=False):
    """running stage 1 and returning (id_accounting, fetch_log)."""
    ids = classify_ids(load_ids())

    # translating imdb ids first, so a duplicate hiding behind one is caught
    imdb_ids = ids["imdb_id"].dropna().unique()
    lookup = {imdb: resolve_imdb_id(session, imdb, refresh)[0] for imdb in imdb_ids}
    from_imdb = ids["imdb_id"].map(lookup).astype("Int64")
    ids["tmdb_id"] = ids["tmdb_id"].fillna(from_imdb)

    ids = mark_duplicates(ids)

    # fetching each distinct film once, however many rows carried its id
    to_fetch = ids.loc[ids["tmdb_id"].notna() & ~ids["is_duplicate"], "tmdb_id"]
    log_rows = []
    for n, tmdb_id in enumerate(to_fetch, start=1):
        log_rows.extend(fetch_film(session, int(tmdb_id), refresh))
        if n % 25 == 0:
            print(f"  fetched {n} of {len(to_fetch)} films")
    fetch_log = pd.DataFrame(log_rows)

    # grain: one row per film (details and credits side by side)
    status = (fetch_log.pivot(index="tmdb_id", columns="endpoint", values="status")
              .rename(columns={"details": "details_status", "credits": "credits_status"})
              .reset_index())
    status["tmdb_id"] = status["tmdb_id"].astype("Int64")

    # left only = input rows with no fetch (blank, invalid, duplicate), which is expected
    accounting = checked_merge(ids, status, "input rows <- fetch results",
                               on="tmdb_id", how="left", validate="many_to_one")

    # leaving duplicates without a fetch status, because their film is counted once
    accounting.loc[accounting["is_duplicate"], ["details_status", "credits_status"]] = pd.NA
    accounting = build_outcome(accounting)

    accounting = accounting[["input_row", "raw_value", "id_kind", "imdb_id", "tmdb_id",
                             "duplicate_of_row", "details_status", "credits_status", "outcome"]]
    accounting.to_csv(config.ID_ACCOUNTING_FILE, index=False)
    fetch_log.to_csv(config.FETCH_LOG_FILE, index=False)
    return accounting, fetch_log
