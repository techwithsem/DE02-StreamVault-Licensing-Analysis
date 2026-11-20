"""stage 6 (on request): checking the pipeline's output against tmdb live, today.

for each chosen film and field i am comparing three values:
  pipeline output - what the pipeline produced (out/films.csv, directors, lead actor)
  snapshot    - the saved api answer the output was built from (data/raw)
  live        - a fresh call to tmdb right now, never from the cache

output != snapshot  -> pipeline bug (the pipeline changed a value it should not have)
snapshot != live    -> source changed (tmdb was edited after the fetch)
all three equal     -> match
tolerance is exact for every field: money is whole dollars, so any change counts.
"""

import json
import time

import numpy as np
import pandas as pd

from pipeline import config

FIELDS = ["title", "release_date", "budget", "revenue", "collection_id", "directors", "lead_actor"]


def choose_sample(df, flagged, accounting, directors, window_start=2000, seed=42):
    """picking films in four slices, so the sample is not chosen to pass.

    every pick comes from the data, not from a fixed id, so the same rules
    are working on next year's list.
    """
    picks = []

    def add(ids, reason):
        picks.extend({"tmdb_id": int(i), "why_chosen": reason} for i in ids)

    with_multiple = df.dropna(subset=["multiple"])
    add(with_multiple.nlargest(2, "multiple")["tmdb_id"], "extreme: highest return")
    add(with_multiple.nsmallest(2, "multiple")["tmdb_id"], "extreme: lowest return")
    # the film named on the most input rows (repeats and imdb ids merged into it)
    rows_per_film = accounting["tmdb_id"].dropna().astype(int).value_counts()
    add(rows_per_film.head(1).index, "most changed: named on the most input rows")
    add(flagged.loc[flagged["flag_round_revenue"], "tmdb_id"].head(1), "most changed: round revenue")
    add(directors.groupby("tmdb_id").size().nlargest(1).index, "most changed: most co-directors")
    years = df["release_year"]
    add(df.loc[years.lt(window_start)].nlargest(1, "release_date")["tmdb_id"],
        f"boundary: last release before {window_start}")
    add(df.loc[years.ge(window_start)].nsmallest(1, "release_date")["tmdb_id"],
        f"boundary: first release from {window_start}")
    add(flagged.loc[flagged["flag_alone_in_collection"], "tmdb_id"].head(1),
        "boundary: only film of its franchise on the list")
    rest = df.loc[~df["tmdb_id"].isin([p["tmdb_id"] for p in picks]), "tmdb_id"]
    # taking up to 4, so a short list is not crashing the check
    add(rest.sample(min(4, len(rest)), random_state=seed), f"random (seed {seed})")
    return pd.DataFrame(picks).drop_duplicates("tmdb_id")


def _summarise(details, credits):
    """reducing one pair of api answers to the fields being checked."""
    crew = credits.get("crew") or []
    cast = credits.get("cast") or []
    directors = sorted({p["name"] for p in crew if p.get("job") == "Director"})
    lead = next((p["name"] for p in cast if p.get("order") == 0), None)
    collection = details.get("belongs_to_collection") or {}
    return {"title": details.get("title"), "release_date": details.get("release_date"),
            "budget": details.get("budget"), "revenue": details.get("revenue"),
            "collection_id": collection.get("id"), "directors": ", ".join(directors),
            "lead_actor": lead}


def _as_text(series):
    return series.astype("string").fillna("").str.replace(r"\.0$", "", regex=True)


def run(session, df, cast, directors, flagged, accounting):
    """re-fetching the sample live and returning one row per film per field."""
    sample = choose_sample(df, flagged, accounting, directors)

    # the pipeline's output values, built from the tables the analysis used
    lead = cast.loc[cast["billing_order"].eq(0)].drop_duplicates("tmdb_id").set_index("tmdb_id")["name"]
    dirs = (directors.sort_values("name").groupby("tmdb_id")["name"].agg(", ".join))
    pipeline_out = df.drop_duplicates("tmdb_id").set_index("tmdb_id")
    pipeline_out = pd.DataFrame({
        "title": pipeline_out["title"],
        "release_date": pipeline_out["release_date"].dt.strftime("%Y-%m-%d"),
        "budget": pipeline_out["budget"], "revenue": pipeline_out["revenue"],
        "collection_id": pipeline_out["collection_id"],
        "directors": dirs.reindex(pipeline_out.index), "lead_actor": lead.reindex(pipeline_out.index),
    })

    snap_rows, live_rows = [], []
    for tmdb_id in sample["tmdb_id"]:
        folder = config.RAW_DIR / str(tmdb_id)
        d = json.loads((folder / "details.json").read_text(encoding="utf-8"))
        c = json.loads((folder / "credits.json").read_text(encoding="utf-8"))
        snap_rows.append({"tmdb_id": tmdb_id, "snapshot_at": d["fetched_at"],
                          **_summarise(d["body"], c["body"])})
        # going to tmdb directly, never to the cache, because the point is today's value
        live_d = session.get(f"{config.BASE_URL}/movie/{tmdb_id}")
        live_c = session.get(f"{config.BASE_URL}/movie/{tmdb_id}/credits")
        time.sleep(config.PAUSE_SECONDS)
        live_d.raise_for_status()
        live_c.raise_for_status()
        live_rows.append({"tmdb_id": tmdb_id, **_summarise(live_d.json(), live_c.json())})

    snap = pd.DataFrame(snap_rows).set_index("tmdb_id")
    live = pd.DataFrame(live_rows).set_index("tmdb_id")

    # grain: one row per film per checked field
    long = []
    for field in FIELDS:
        part = pd.DataFrame({
            "tmdb_id": sample["tmdb_id"].to_numpy(),
            "field": field,
            "pipeline_output": _as_text(pipeline_out[field].reindex(sample["tmdb_id"])).to_numpy(),
            "snapshot": _as_text(snap[field].reindex(sample["tmdb_id"])).to_numpy(),
            "live": _as_text(live[field].reindex(sample["tmdb_id"])).to_numpy(),
        })
        long.append(part)
    result = pd.concat(long, ignore_index=True)
    result["class"] = np.select(
        [result["pipeline_output"].ne(result["snapshot"]), result["snapshot"].ne(result["live"])],
        ["pipeline bug", "source changed"], default="match")
    result = result.merge(sample, on="tmdb_id", how="left", validate="many_to_one")
    titles = df.drop_duplicates("tmdb_id")[["tmdb_id", "title"]].rename(columns={"title": "film"})
    result = result.merge(titles,
                          on="tmdb_id", how="left", validate="many_to_one")
    result["checked_at"] = pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds")
    result = result.merge(snap["snapshot_at"].reset_index(), on="tmdb_id", how="left", validate="many_to_one")
    return result[["tmdb_id", "film", "why_chosen", "field", "pipeline_output", "snapshot", "live",
                   "class", "snapshot_at", "checked_at"]]
