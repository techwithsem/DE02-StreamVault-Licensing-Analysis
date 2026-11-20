"""merging two tables and keeping proof that nothing was lost or doubled.

every merge in the pipeline goes through checked_merge, which:
  - requires the expected relationship (validate), so a doubled key stops the run
  - labels every row as matched, left only or right only (indicator=True)
  - records rows before and after in JOIN_LOG, written to profiling/joins.csv
"""

import pandas as pd

JOIN_LOG = []

RELATIONSHIPS = {"one_to_one", "one_to_many", "many_to_one", "many_to_many"}


class JoinRowCountError(RuntimeError):
    """raised when a join that should keep every row has gained or lost rows."""


def checked_merge(left, right, name, *, on, how, validate, keep_rows=True):
    """merging left and right on `on`, stating the relationship up front.

    validate has no default on purpose: every caller is saying which side may
    repeat, so pandas is stopping the run if that is not true. with keep_rows=True
    the result must have exactly as many rows as `left`.
    """
    if validate not in RELATIONSHIPS:
        raise ValueError(f"join '{name}': validate must be one of {sorted(RELATIONSHIPS)}")
    before = len(left)
    merged = left.merge(right, on=on, how=how, validate=validate, indicator=True)
    labels = merged["_merge"].value_counts()
    JOIN_LOG.append({
        "join": name,
        "relationship": validate,
        "how": how,
        "rows_before": before,
        "rows_after": len(merged),
        "matched": int(labels.get("both", 0)),
        "left_only": int(labels.get("left_only", 0)),
        "right_only": int(labels.get("right_only", 0)),
    })
    if keep_rows and len(merged) != before:
        raise JoinRowCountError(f"join '{name}' changed the row count from {before} to {len(merged)}")
    return merged.drop(columns="_merge")


def log_table():
    return pd.DataFrame(JOIN_LOG)
