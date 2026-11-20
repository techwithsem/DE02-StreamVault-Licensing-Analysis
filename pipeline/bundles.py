"""improvement beyond the brief: checking how complete each franchise bundle is.

studios sell a franchise as all-or-nothing, but the candidate list only holds
some of each franchise's films. this is fetching each franchise's full film list
from tmdb (GET /collection/{id}) and the money figures for the films the list
left out, so kwame can see what the whole bundle earned, not just the part on
the list. answers are cached like every other call.
"""

import pandas as pd

from pipeline import config
from pipeline.fetch import get_cached, status_of
from pipeline.joins import checked_merge


def run(session, films, refresh=False):
    """returning (bundle_summary, bundle_films)."""
    collection_ids = films["collection_id"].dropna().astype(int).unique()

    parts = []
    for cid in collection_ids:
        record, _ = get_cached(session, f"/collection/{cid}",
                               config.RAW_DIR / "_collection" / f"{cid}.json", refresh=refresh)
        body = record.get("body") or {}
        parts.extend({"collection_id": cid, "tmdb_id": p.get("id"), "title": p.get("title"),
                      "release_date": p.get("release_date")} for p in body.get("parts", []))
    # grain: one row per film per franchise
    bundle = pd.DataFrame(parts, columns=["collection_id", "tmdb_id", "title", "release_date"])
    bundle["release_date"] = pd.to_datetime(bundle["release_date"], errors="coerce")
    bundle["released"] = bundle["release_date"].le(pd.Timestamp.now())
    bundle["on_list"] = bundle["tmdb_id"].isin(films["tmdb_id"].astype(int))

    # fetching budget and revenue for released films the candidate list left out
    missing = bundle.loc[bundle["released"] & ~bundle["on_list"], "tmdb_id"].unique()
    money = []
    for tmdb_id in missing:
        record, _ = get_cached(session, f"/movie/{tmdb_id}",
                               config.RAW_DIR / str(tmdb_id) / "details.json", refresh=refresh)
        body = record.get("body") or {}
        money.append({"tmdb_id": tmdb_id, "budget": body.get("budget"),
                      "revenue": body.get("revenue"), "fetch_status": status_of(record)})
    money = pd.DataFrame(money, columns=["tmdb_id", "budget", "revenue", "fetch_status"])
    listed = films[["tmdb_id", "budget", "revenue"]].astype({"tmdb_id": int})

    bundle = checked_merge(bundle, pd.concat([listed, money], ignore_index=True),
                           "bundle films <- money figures", on="tmdb_id", how="left",
                           validate="many_to_one")
    bundle["budget"] = pd.to_numeric(bundle["budget"], errors="coerce")
    bundle["revenue"] = pd.to_numeric(bundle["revenue"], errors="coerce")
    bundle["has_money"] = bundle["budget"].gt(0) & bundle["revenue"].gt(0)

    released = bundle[bundle["released"]].copy()
    released["missing"] = ~released["on_list"]
    released["missing_title"] = released["title"].where(released["missing"])
    released["money_budget"] = released["budget"].where(released["has_money"])
    released["money_revenue"] = released["revenue"].where(released["has_money"])
    released["list_budget"] = released["money_budget"].where(released["on_list"])
    released["list_revenue"] = released["money_revenue"].where(released["on_list"])

    # grain: one row per franchise
    summary = (released.groupby("collection_id")
               .agg(films_released=("tmdb_id", "nunique"),
                    films_on_list=("on_list", "sum"),
                    films_missing=("missing", "sum"),
                    missing_without_money=("has_money", lambda s: (~s).sum()),
                    missing_titles=("missing_title", lambda s: " | ".join(s.dropna())),
                    list_budget=("list_budget", "sum"), list_revenue=("list_revenue", "sum"),
                    bundle_budget=("money_budget", "sum"), bundle_revenue=("money_revenue", "sum"))
               .reset_index())
    summary["multiple_on_list"] = summary["list_revenue"] / summary["list_budget"]
    summary["multiple_whole_bundle"] = summary["bundle_revenue"] / summary["bundle_budget"]
    summary["change"] = summary["multiple_whole_bundle"] - summary["multiple_on_list"]
    names = films.dropna(subset=["collection_id"]).drop_duplicates("collection_id")
    names = names[["collection_id", "collection_name"]].astype({"collection_id": int})
    summary = checked_merge(summary, names,
                            "franchises <- names", on="collection_id", how="left", validate="one_to_one")
    cols = ["collection_name", "films_released", "films_on_list", "films_missing",
            "missing_without_money", "multiple_on_list", "multiple_whole_bundle", "change",
            "missing_titles", "collection_id"]
    return summary[cols].sort_values("change").reset_index(drop=True), bundle
