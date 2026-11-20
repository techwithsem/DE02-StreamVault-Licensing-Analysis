"""tying the saved api answers in data/raw to one snapshot.

data/raw_manifest.csv is listing every saved file with its checksum (sha256),
its size and the time tmdb answered. comparing a fresh manifest with the one
already on disk is showing straight away if any saved answer was added,
removed or changed since the snapshot the memo quotes.
"""

import hashlib
import json

import pandas as pd

from pipeline import config

MANIFEST_FILE = config.DATA_DIR / "raw_manifest.csv"


def build(raw_dir=None):
    """grain: one row per saved answer file."""
    raw_dir = raw_dir or config.RAW_DIR
    rows = []
    for path in sorted(raw_dir.rglob("*.json")):
        data = path.read_bytes()
        rows.append({
            "file": path.relative_to(raw_dir).as_posix(),
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "fetched_at": json.loads(data).get("fetched_at", ""),
        })
    return pd.DataFrame(rows, columns=["file", "sha256", "bytes", "fetched_at"])


def compare(old, new):
    """counting files added, removed and changed between two manifests."""
    both = old.merge(new, on="file", how="outer", suffixes=("_old", "_new"), indicator=True)
    return {
        "added": int(both["_merge"].eq("right_only").sum()),
        "removed": int(both["_merge"].eq("left_only").sum()),
        "changed": int((both["_merge"].eq("both") & both["sha256_old"].ne(both["sha256_new"])).sum()),
    }


def update(raw_dir=None, path=None):
    """rebuilding the manifest, reporting drift against the saved one, and saving it."""
    path = path or MANIFEST_FILE
    new = build(raw_dir)
    drift = compare(pd.read_csv(path), new) if path.exists() else None
    new.to_csv(path, index=False)
    return new, drift
