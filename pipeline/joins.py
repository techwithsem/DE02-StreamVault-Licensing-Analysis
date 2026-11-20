"""merging two tables and keeping proof that nothing was lost or doubled.

every merge in the pipeline goes through checked_merge, which:
  - states the expected relationship (validate=), so a doubled key stops the run
  - labels every row as matched, left only or right only (indicator=True)
  - records rows before and after in JOIN_LOG, written to profiling/joins.csv
"""

import pandas as pd

JOIN_LOG = []


def checked_merge(left, right, name, keep_rows=True, **kwargs):
    """merging left and right; with keep_rows=True the row count must not change."""
    before = len(left)
    merged = left.merge(right, indicator=True, **kwargs)
    labels = merged["_merge"].value_counts()
    JOIN_LOG.append({
        "join": name,
        "relationship": kwargs.get("validate", ""),
        "how": kwargs.get("how", "inner"),
        "rows_before": before,
        "rows_after": len(merged),
        "matched": int(labels.get("both", 0)),
        "left_only": int(labels.get("left_only", 0)),
        "right_only": int(labels.get("right_only", 0)),
    })
    if keep_rows and len(merged) != before:
        raise SystemExit(f"join '{name}' changed the row count from {before} to {len(merged)}")
    return merged.drop(columns="_merge")


def log_table():
    return pd.DataFrame(JOIN_LOG)
