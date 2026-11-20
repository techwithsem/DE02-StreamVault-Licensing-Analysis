"""checking the id list is being read and sorted correctly, with no network."""

import pandas as pd

from pipeline.ids import classify_ids, load_ids, mark_duplicates


def make_list(tmp_path, values):
    path = tmp_path / "ids.csv"
    path.write_text("tmdb_id\n" + "\n".join(values) + "\n", encoding="utf-8")
    return load_ids(path)


def test_reading_keeps_every_row_as_text(tmp_path):
    df = make_list(tmp_path, ["155", "", "N/A", "0603"])
    assert len(df) == 4
    assert df["raw_value"].tolist() == ["155", "", "N/A", "0603"]
    assert df["input_row"].tolist() == [2, 3, 4, 5]


def test_sorting_each_kind_of_value(tmp_path):
    df = classify_ids(make_list(tmp_path, [
        "155", " 278 ", "155.0", "", "N/A", "-1", "0", "tt0468569", "abc", "12x"]))
    assert df["id_kind"].tolist() == [
        "tmdb", "tmdb", "tmdb", "blank", "placeholder",
        "invalid", "invalid", "imdb", "invalid", "invalid"]
    assert df["tmdb_id"].tolist()[:3] == [155, 278, 155]
    assert df.loc[7, "imdb_id"] == "tt0468569"


def test_leading_zeros_are_the_same_film(tmp_path):
    df = mark_duplicates(classify_ids(make_list(tmp_path, ["603", "0603"])))
    assert df["is_duplicate"].tolist() == [False, True]
    assert df.loc[1, "duplicate_of_row"] == 2


def test_duplicates_point_to_the_first_row(tmp_path):
    df = mark_duplicates(classify_ids(make_list(tmp_path, ["1", "2", "1", "", "1"])))
    assert df["is_duplicate"].tolist() == [False, False, True, False, True]
    assert df["duplicate_of_row"].tolist()[2] == 2
    assert df["duplicate_of_row"].tolist()[4] == 2
    assert pd.isna(df["duplicate_of_row"].tolist()[3])   # a blank row is not a duplicate
