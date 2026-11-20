"""comparing a row-by-row version of the core calculation with the whole-column
version the pipeline uses, at 127, 500 and 5,000 titles.

the row-by-row version is here only as the "before" in the measurement report.
the pipeline never uses it.

    python scripts/benchmark_apply.py
"""

import statistics
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import config  # noqa: E402

RUNS = 5


def row_by_row(df):
    """the slow way: python is looking at one film at a time."""
    def one(r):
        ok = r["budget"] > 0 and r["revenue"] > 0
        return pd.Series({"multiple": r["revenue"] / r["budget"] if ok else np.nan,
                          "group": "franchise" if pd.notna(r["collection_id"]) else "standalone"})
    out = df.join(df.apply(one, axis=1))
    return out.groupby("group")["multiple"].median()


def whole_column(df):
    """the way the pipeline does it: one calculation over the whole column."""
    usable = df["budget"].gt(0) & df["revenue"].gt(0)
    multiple = (df["revenue"] / df["budget"]).where(usable)
    group = np.where(df["collection_id"].notna(), "franchise", "standalone")
    return multiple.groupby(group).median()


def timed(fn, df):
    times = []
    for _ in range(RUNS):
        t = time.perf_counter()
        result = fn(df)
        times.append(time.perf_counter() - t)
    return statistics.median(times), result


def main():
    films = pd.read_csv(config.PROJECT_DIR / "out" / "films.csv")[["budget", "revenue", "collection_id"]]
    rows = []
    for size in [127, 500, 5000]:
        df = films.sample(size, replace=True, random_state=1).reset_index(drop=True)
        slow, a = timed(row_by_row, df)
        fast, b = timed(whole_column, df)
        assert np.allclose(a.sort_index(), b.sort_index()), "the two versions disagree"
        rows.append({"titles": size, "row_by_row_ms": slow * 1000, "whole_column_ms": fast * 1000,
                     "times_faster": slow / fast})
        print(f"{size:>5} titles: row by row {slow*1000:8.1f} ms, whole column "
              f"{fast*1000:6.2f} ms, {slow/fast:5.0f}x faster (same answer)")
    out = config.PROJECT_DIR / "out" / "benchmark_apply.csv"
    pd.DataFrame(rows).round(3).to_csv(out, index=False, encoding="utf-8-sig")
    print(f"written: {out.relative_to(config.PROJECT_DIR)}")


if __name__ == "__main__":
    main()
