"""checking the tables, checks and kpis on a tiny made-up dataset with known answers."""

import ast
from pathlib import Path

import pandas as pd
import pytest

from pipeline import checks, flatten, kpis


def film(fid, title, date, budget, revenue, collection=None):
    return {"id": fid, "imdb_id": f"tt{fid}", "title": title, "release_date": date,
            "budget": budget, "revenue": revenue, "runtime": 100, "vote_average": 7.0,
            "vote_count": 1000, "status": "Released", "original_language": "en",
            "belongs_to_collection": ({"id": collection, "name": f"c{collection}"} if collection else None),
            "genres": [{"id": 1, "name": "Action"}, {"id": 2, "name": "Drama"}]}


def credit(fid, director="dir", lead="lead", extra_director=None):
    crew = [{"id": 900, "name": director, "job": "Director"},
            {"id": 900, "name": director, "job": "Director"},       # listed twice on purpose
            {"id": 901, "name": "someone", "job": "Writer"}]
    if extra_director:
        crew.append({"id": 902, "name": extra_director, "job": "Director"})
    cast = [{"id": 1, "name": lead, "character": "a", "order": 0},
            {"id": 2, "name": "second", "character": "b", "order": 1},
            {"id": 2, "name": "second", "character": "c", "order": 2}]   # one actor, two parts
    return {"id": fid, "cast": cast, "crew": crew}


@pytest.fixture
def data():
    details = [
        film(1, "f1", "1995-05-01", 10, 100, collection=50),     # 10x, first entry
        film(2, "f2", "2003-05-01", 10, 40, collection=50),      # 4x, later entry
        film(3, "s1", "2001-01-01", 10, 30),                     # 3x standalone
        film(4, "s2", "1999-12-31", 10, 20, collection=60),      # 2x, alone in its franchise
        film(5, "s3", "2010-01-01", 10, 50_000_000),             # round revenue
    ]
    credits = [credit(1, extra_director="co"), credit(2), credit(3), credit(4), credit(5)]
    fetched = pd.DataFrame({"tmdb_id": [1, 2, 3, 4, 5], "details_fetched_at": "t",
                            "credits_fetched_at": "t"})
    films, _ = flatten.build_films(details, fetched)
    accounting = pd.DataFrame({
        "input_row": [2, 3, 4, 5, 6, 7], "tmdb_id": pd.array([1, 2, 3, 4, 5, 3], dtype="Int64"),
        "outcome": ["kept: details and credits fetched"] * 5 + ["dropped: duplicate of an earlier row"]})
    return films, flatten.build_cast(credits), flatten.build_directors(credits), accounting


def test_films_table_is_one_row_per_film(data):
    films, *_ = data
    assert len(films) == 5 and films["tmdb_id"].is_unique
    assert films.loc[0, "genres"] == "Action, Drama"
    assert films["collection_id"].isna().sum() == 2
    assert films.loc[3, "release_year"] == 1999


def test_cast_keeps_every_credit_and_directors_drop_repeats(data):
    _, cast, directors, _ = data
    assert len(cast) == 15                                   # 3 credits x 5 films, none lost
    assert directors.groupby("tmdb_id").size().to_dict() == {1: 2, 2: 1, 3: 1, 4: 1, 5: 1}


def test_flags_point_at_the_right_films(data):
    films, *_ = data
    flagged = checks.flag_films(films)
    assert flagged.loc[flagged["flag_round_revenue"], "tmdb_id"].tolist() == [5]
    assert flagged.loc[flagged["flag_alone_in_collection"], "tmdb_id"].tolist() == [4]


def test_profile_shows_only_real_repeats_and_date_ranges(data):
    films, *_ = data
    p = checks.profile(films).set_index("column")
    assert p.loc["title", "most_common"] == ""                  # every title is different
    assert p.loc["budget", "most_common"] == "10" and p.loc["budget", "times"] == 5
    assert (p.loc["release_date", "min"], p.loc["release_date", "max"]) == ("1995-05-01", "2010-01-01")
    assert p.loc["collection_id", "missing"] == 2
    assert "standalone" in p.loc["collection_id", "note"]


def test_hard_check_stops_on_a_missing_film(data):
    films, cast, directors, accounting = data
    ids = pd.Series([1, 2, 3, 4, 5], dtype="Int64")
    assert checks.run_checks(accounting, films, cast, directors, ids)["passed"].all()
    with pytest.raises(SystemExit, match="one film row per kept id"):
        checks.run_checks(accounting, films.iloc[:4], cast, directors, ids)


def test_multiple_and_groups(data):
    films, _, _, accounting = data
    df = kpis.prepare(films, accounting)
    assert df.set_index("tmdb_id")["multiple"].round(2).to_dict() == {
        1: 10.0, 2: 4.0, 3: 3.0, 4: 2.0, 5: 5_000_000.0}
    assert df["is_franchise"].tolist() == [True, True, False, True, False]
    two_plus = kpis.prepare(films, accounting, franchise_rule="two_plus_on_list")
    assert two_plus["is_franchise"].tolist() == [True, True, False, False, False]


def test_round_revenue_can_be_left_out(data):
    films, _, _, accounting = data
    df = kpis.prepare(films, accounting, revenue_estimates="exclude")
    assert df["multiple"].isna().tolist() == [False, False, False, False, True]


def test_counting_duplicates_repeats_only_the_repeated_film(data):
    films, _, _, accounting = data
    df = kpis.prepare(films, accounting, duplicates="count_each_row")
    assert df["tmdb_id"].value_counts().to_dict()[3] == 2 and len(df) == 6


def test_windows_and_group_sizes(data):
    films, _, _, accounting = data
    table = kpis.compare_windows(films, accounting).set_index(["window", "group"])
    assert table.loc[("all years", "franchise"), "usable"] == 3
    assert table.loc[("all years", "franchise"), "median_multiple"] == 4.0
    # from 2000 onward only f2 (franchise) and s1, s3 (standalone) remain
    assert table.loc[("2000 onward", "franchise"), "films"] == 1


def test_entry_pattern_and_talent(data):
    films, cast, directors, accounting = data
    df = kpis.prepare(films, accounting)
    entry = kpis.entry_pattern(df).set_index("position")
    assert entry.loc["first entry", "median_multiple"] == 10.0
    assert entry.loc["latest entry on list", "median_multiple"] == 4.0
    talent = kpis.talent_table(df, directors, "director", min_films=2)
    assert talent["name"].tolist() == ["dir"] and talent.loc[0, "films"] == 5


def test_no_row_loops_in_the_analysis_code():
    """failing if anyone adds iterrows, itertuples or a row-wise apply to the analysis."""
    root = Path(__file__).resolve().parent.parent / "pipeline"
    banned = []
    for name in ["flatten.py", "checks.py", "kpis.py", "analysis.py", "bundles.py", "report.py"]:
        tree = ast.parse((root / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in {"iterrows", "itertuples"}:
                banned.append(f"{name}: {node.attr}")
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "apply"
                    and any(k.arg == "axis" for k in node.keywords)):
                banned.append(f"{name}: apply(axis=...)")
    assert banned == []


def test_checked_merge_stops_a_fan_out_and_logs_matches():
    from pipeline import joins
    joins.JOIN_LOG.clear()
    films = pd.DataFrame({"tmdb_id": [1, 2, 3]})
    extra = pd.DataFrame({"tmdb_id": [1, 2], "x": ["a", "b"]})
    out = joins.checked_merge(films, extra, "test", on="tmdb_id", how="left", validate="one_to_one")
    assert len(out) == 3 and "_merge" not in out.columns
    assert joins.log_table().iloc[0][["matched", "left_only"]].tolist() == [2, 1]
    doubled = pd.DataFrame({"tmdb_id": [1, 1], "x": ["a", "b"]})
    with pytest.raises(pd.errors.MergeError):      # naming the side with the doubled key
        joins.checked_merge(films, doubled, "fan-out", on="tmdb_id", how="left", validate="one_to_one")


def test_parse_report_counts_values_that_could_not_be_read():
    details = [film(1, "a", "2001-01-01", 10, 20), film(2, "b", "not a date", "ten", 20)]
    fetched = pd.DataFrame({"tmdb_id": [1, 2], "details_fetched_at": "t", "credits_fetched_at": "t"})
    _, parsing = flatten.build_films(details, fetched)
    p = parsing.set_index("column")
    assert p.loc["release_date", "could_not_read"] == 1
    assert p.loc["budget", "could_not_read"] == 1 and p.loc["budget", "examples"] == "ten"
    assert p.loc["revenue", "could_not_read"] == 0


def test_spot_check_sample_comes_from_the_data_not_fixed_ids(data):
    from pipeline import spotcheck
    films, _, directors, accounting = data
    df = kpis.prepare(films, accounting)
    sample = spotcheck.choose_sample(df, checks.flag_films(films), accounting, directors)
    # a film already picked for one reason is not repeated, so checking the films, not the labels
    assert {3, 1, 4} <= set(sample["tmdb_id"])    # listed twice, has a co-director, 1999-12-31
    assert sample["tmdb_id"].is_unique
    assert sample["tmdb_id"].isin(df["tmdb_id"]).all()                     # every pick is a real film
