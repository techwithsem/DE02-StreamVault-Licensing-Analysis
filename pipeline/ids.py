"""reading the candidate id list and sorting every row into a kind, so each of
the input rows can be accounted for later."""

import pandas as pd

from pipeline import config


def load_ids(path=None):
    """reading the id list as text, so nothing gets rounded or turned into nan."""
    path = path or config.ID_FILE
    # grain: one row per line of the input file
    # keeping blank lines too: pandas skips them by default, which would hide a row
    df = pd.read_csv(path, dtype=str, keep_default_na=False, skip_blank_lines=False)
    if df.shape[1] != 1:
        raise SystemExit(f"{path} should have exactly one column, found {df.shape[1]}")
    df = df.rename(columns={df.columns[0]: "raw_value"})
    # keeping the line number as it shows in a text editor (the header is line 1)
    df.insert(0, "input_row", df.index + 2)
    return df


def classify_ids(df):
    """labelling each row as tmdb, imdb, blank, placeholder or invalid."""
    out = df.copy()
    # trimming spaces and dropping a trailing ".0" that spreadsheets sometimes add
    cleaned = out["raw_value"].str.strip().str.replace(r"\.0$", "", regex=True)

    is_blank = cleaned.eq("")
    is_placeholder = cleaned.str.lower().isin(config.MISSING_TOKENS)
    is_number = cleaned.str.fullmatch(r"\d+")
    is_positive = is_number & pd.to_numeric(cleaned.where(is_number), errors="coerce").gt(0)
    is_imdb = cleaned.str.fullmatch(r"tt\d+", case=False)

    out["id_kind"] = "invalid"
    out.loc[is_imdb, "id_kind"] = "imdb"
    out.loc[is_positive, "id_kind"] = "tmdb"
    out.loc[is_placeholder, "id_kind"] = "placeholder"
    out.loc[is_blank, "id_kind"] = "blank"

    # turning good tmdb ids into whole numbers, which also removes leading zeros
    out["tmdb_id"] = pd.to_numeric(cleaned.where(is_positive), errors="coerce").astype("Int64")
    out["imdb_id"] = cleaned.where(is_imdb).str.lower()
    return out


def mark_duplicates(df):
    """flagging rows whose tmdb id already appeared higher up the list."""
    out = df.copy()
    has_id = out["tmdb_id"].notna()
    out["is_duplicate"] = has_id & out.duplicated("tmdb_id", keep="first")
    # pointing every duplicate back at the first row that carried the same id
    first_row = out.loc[has_id].groupby("tmdb_id")["input_row"].transform("min")
    out["duplicate_of_row"] = first_row.where(out["is_duplicate"]).astype("Int64")
    return out
