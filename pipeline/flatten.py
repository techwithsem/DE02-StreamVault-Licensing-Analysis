"""stage 2: turning the saved api answers into flat tables.

every table states its grain (what one row means) where it is created.
"""

import json

import pandas as pd

from pipeline import config
from pipeline.joins import checked_merge


def read_raw(tmdb_ids):
    """loading the saved details and credits bodies for the films that were kept."""
    details, credits, fetched = [], [], []
    for tmdb_id in tmdb_ids:
        folder = config.RAW_DIR / str(tmdb_id)
        d = json.loads((folder / "details.json").read_text(encoding="utf-8"))
        c = json.loads((folder / "credits.json").read_text(encoding="utf-8"))
        details.append(d["body"])
        credits.append(c["body"])
        fetched.append({"tmdb_id": tmdb_id, "details_fetched_at": d["fetched_at"],
                        "credits_fetched_at": c["fetched_at"]})
    return details, credits, pd.DataFrame(fetched)


def build_films(details, fetched):
    """grain: one row per film. returns (films, parse_report)."""
    raw = pd.json_normalize(details, sep="_", max_level=1)
    # making sure the collection columns exist even if no film has a collection
    raw = raw.reindex(columns=raw.columns.union(
        ["belongs_to_collection_id", "belongs_to_collection_name"]))

    films = pd.DataFrame({
        "tmdb_id": raw["id"].astype("Int64"),
        "imdb_id": raw["imdb_id"].astype("string"),
        "title": raw["title"].astype("string"),
        "release_date": pd.to_datetime(raw["release_date"], errors="coerce"),
        "budget": pd.to_numeric(raw["budget"], errors="coerce").astype("Int64"),
        "revenue": pd.to_numeric(raw["revenue"], errors="coerce").astype("Int64"),
        "runtime": pd.to_numeric(raw["runtime"], errors="coerce"),
        "vote_average": pd.to_numeric(raw["vote_average"], errors="coerce"),
        "vote_count": pd.to_numeric(raw["vote_count"], errors="coerce").astype("Int64"),
        "status": raw["status"].astype("string"),
        "original_language": raw["original_language"].astype("string"),
        "collection_id": raw["belongs_to_collection_id"].astype("Int64"),
        "collection_name": raw["belongs_to_collection_name"].astype("string"),
    })
    films["release_year"] = films["release_date"].dt.year.astype("Int64")
    # counting values that failed to convert, while rows still line up with raw
    parsing = parse_report(raw, films)

    # turning the list of genres into one text column, still one row per film
    genres = pd.json_normalize(details, record_path="genres", meta=["id"], meta_prefix="film_")
    if len(genres):
        genre_text = genres.groupby("film_id")["name"].agg(", ".join).rename("genres")
        films = checked_merge(films, genre_text.reset_index().rename(columns={"film_id": "tmdb_id"}),
                              "films <- genres", on="tmdb_id", how="left", validate="one_to_one")
    else:
        films["genres"] = pd.NA

    films = checked_merge(films, fetched, "films <- fetch times",
                          on="tmdb_id", how="left", validate="one_to_one")
    return films, parsing


def parse_report(raw, films):
    """counting values that were present but could not be read as a number or date.

    grain: one row per converted column. a value that fails becomes blank, so
    without this count a bad value would hide among the genuine gaps.
    """
    pairs = {"release_date": "release_date", "budget": "budget", "revenue": "revenue",
             "runtime": "runtime", "vote_average": "vote_average", "vote_count": "vote_count"}
    rows = []
    for raw_col, col in pairs.items():
        present = raw[raw_col].notna() & raw[raw_col].astype("string").str.strip().ne("")
        failed = present & films[col].isna()
        rows.append({"column": col, "values_present": int(present.sum()),
                     "could_not_read": int(failed.sum()),
                     "examples": ", ".join(raw.loc[failed, raw_col].astype(str).head(3))})
    return pd.DataFrame(rows)


def build_cast(credits):
    """grain: one row per film per cast credit (an actor playing two parts is two rows)."""
    cast = pd.json_normalize(credits, record_path="cast", meta=["id"], meta_prefix="film_")
    cast = cast.rename(columns={"film_id": "tmdb_id", "id": "person_id", "order": "billing_order"})
    cast["tmdb_id"] = cast["tmdb_id"].astype("Int64")
    return cast[["tmdb_id", "person_id", "name", "character", "billing_order"]]


def build_directors(credits):
    """grain: one row per film per director (co-directors are separate rows)."""
    crew = pd.json_normalize(credits, record_path="crew", meta=["id"], meta_prefix="film_")
    crew = crew.rename(columns={"film_id": "tmdb_id", "id": "person_id"})
    directors = crew.loc[crew["job"].eq("Director"), ["tmdb_id", "person_id", "name"]]
    # removing a person listed twice as director of the same film, which would double-count them
    directors = directors.drop_duplicates(["tmdb_id", "person_id"])
    directors["tmdb_id"] = directors["tmdb_id"].astype("Int64")
    return directors.reset_index(drop=True)


def run(kept_ids):
    """running stage 2 and returning (films, cast, directors, credits_film_ids, parsing)."""
    details, credits, fetched = read_raw(kept_ids)
    films, parsing = build_films(details, fetched)
    cast = build_cast(credits)
    directors = build_directors(credits)
    credit_ids = pd.Series([c.get("id") for c in credits], dtype="Int64")
    return films, cast, directors, credit_ids, parsing
