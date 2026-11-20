"""writing results to disk.

profiling/ is holding the "is the data ok?" files (profile, flags, checks).
out/ is holding the "what is the answer?" files (kpis, shortlists, summary).

csv files are saved with a byte-order mark (utf-8-sig) so excel is showing
names like "Alien³" and "WALL·E" correctly.
"""

import numpy as np
import pandas as pd

from pipeline import config

OUT_DIR = config.PROJECT_DIR / "out"
PROFILE_DIR = config.PROJECT_DIR / "profiling"


def write_csv(df, name, round_to=3, folder=OUT_DIR):
    folder.mkdir(exist_ok=True)
    path = folder / name
    numeric = df.select_dtypes("float").columns
    df.assign(**{c: df[c].round(round_to) for c in numeric}).to_csv(
        path, index=False, encoding="utf-8-sig")
    return path


def _x(values):
    """formatting a whole column of multiples at once, e.g. 5.62 -> "5.62x"."""
    return pd.Series(np.char.mod("%.2fx", values.to_numpy(dtype=float)), index=values.index)


def _table(header, columns):
    """building markdown table rows column by column, never row by row."""
    body = columns[0].astype(str)
    for col in columns[1:]:
        body = body + " | " + col.astype(str)
    return [header, "|" + "---|" * len(columns)] + ("| " + body + " |").tolist()


def write_summary(windows, sensitivity, entry, franchise_short, standalone_short,
                  snapshot_from, snapshot_to):
    """writing a short plain-english results page, rebuilt on every run."""
    lines = ["# results summary (rebuilt on every run)", "",
             f"data snapshot: tmdb answers fetched between {snapshot_from} and {snapshot_to} (utc).",
             "return multiple = box office revenue / production budget, per film. median, not mean.", ""]

    w = windows
    lines += ["## franchise vs standalone", ""] + _table(
        "| window | group | films | median multiple | mean multiple | share under 2x |",
        [w["window"], w["group"], w["usable"], _x(w["median_multiple"]), _x(w["mean_multiple"]),
         pd.Series(np.char.mod("%.0f%%", w["share_under_2x"].to_numpy(dtype=float) * 100), index=w.index)])

    s = sensitivity
    flips = s["leader"].nunique() > 1
    lines += ["", "## does the answer change under other cleaning choices?", ""] + _table(
        "| scenario | window | franchise | standalone | leader |",
        [s["scenario"], s["window"],
         _x(s["franchise_median_multiple"]) + " (" + s["franchise_usable"].astype(int).astype(str) + ")",
         _x(s["standalone_median_multiple"]) + " (" + s["standalone_usable"].astype(int).astype(str) + ")",
         s["leader"]])
    lines += ["", "**THE RECOMMENDATION FLIPS UNDER AT LEAST ONE CHOICE.**" if flips
              else "the leader is the same under every choice and in both windows.", ""]

    e = entry
    lines += ["## first film vs later films in a franchise", ""] + _table(
        "| window | position | films | median multiple |",
        [e["window"], e["position"], e["films"], _x(e["median_multiple"])])

    f = franchise_short
    lines += ["", "## shortlist (ranked on 2000-onward films)", ""] + _table(
        "| franchise | films since 2000 | median multiple | weakest film | all-years median |",
        [f["collection_name"], f["films_on_list"], _x(f["median_multiple"]),
         f["weakest_film"] + " (" + _x(f["weakest_multiple"]) + ")", _x(f["all_years_median"])])

    a = standalone_short
    lines += [""] + _table(
        "| standalone | year | multiple | rating |",
        [a["title"], a["release_year"], _x(a["multiple"]),
         pd.Series(np.char.mod("%.1f", a["vote_average"].to_numpy(dtype=float)), index=a.index)])

    path = OUT_DIR / "summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
