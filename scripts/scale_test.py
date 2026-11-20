"""timing the analysis (stages 2 to 4) on 127, 500 and 5,000 made-up titles.

it is copying the real cached answers under new ids into a temporary folder,
so the test needs no network and leaves data/raw untouched.

    python scripts/scale_test.py
"""

import json
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import analysis, config  # noqa: E402

SIZES = [127, 500, 5000]
RUNS = 5


def build_fake_cache(real_ids, size, folder):
    """writing `size` films into folder, each a copy of a real one with a new id."""
    new_ids = []
    for n in range(size):
        source = real_ids[n % len(real_ids)]
        copy = n // len(real_ids)                   # 0 for the first pass, 1 for the second ...
        new_id = source + copy * 10_000_000
        for endpoint in ("details", "credits"):
            source_file = config.RAW_DIR / str(source) / f"{endpoint}.json"
            record = json.loads(source_file.read_text(encoding="utf-8"))
            body = record["body"]
            body["id"] = new_id
            # giving each copy its own franchise id, so franchises are not merging together
            if endpoint == "details" and body.get("belongs_to_collection"):
                collection = body["belongs_to_collection"]
                body["belongs_to_collection"] = {**collection, "id": collection["id"] + copy * 10_000_000}
            out = folder / str(new_id)
            out.mkdir(parents=True, exist_ok=True)
            (out / f"{endpoint}.json").write_text(json.dumps(record), encoding="utf-8")
        new_ids.append(new_id)
    return new_ids


def main():
    accounting = pd.read_csv(config.ID_ACCOUNTING_FILE, dtype={"tmdb_id": "Int64"})
    real_ids = accounting.loc[accounting["outcome"].str.startswith("kept"), "tmdb_id"].astype(int).tolist()
    real_raw = config.RAW_DIR
    rows = []
    try:
        for size in SIZES:
            folder = Path(tempfile.mkdtemp(prefix=f"scale{size}_"))
            ids = build_fake_cache(real_ids, size, folder)
            fake_accounting = pd.DataFrame({
                "input_row": range(2, size + 2), "tmdb_id": pd.array(ids, dtype="Int64"),
                "outcome": "kept: details and credits fetched"})
            config.RAW_DIR = folder
            seconds, stages = [], []
            for _ in range(RUNS):
                t = time.perf_counter()
                _, timings = analysis.run_timed(ids, fake_accounting)
                seconds.append(time.perf_counter() - t)
                stages.append(timings)
            config.RAW_DIR = real_raw
            shutil.rmtree(folder, ignore_errors=True)
            # keeping the median time of each stage, to see which one grows fastest
            per_stage = pd.DataFrame(stages).median().to_dict()
            rows.append({"titles": size, "first_run_s": seconds[0],
                         "median_of_5_s": statistics.median(seconds), "slowest_s": max(seconds),
                         **{f"stage {k.split()[0]} s": v for k, v in per_stage.items()}})
            print(f"{size:>6} titles: median {statistics.median(seconds):.3f}s "
                  f"(first {seconds[0]:.3f}s, slowest {max(seconds):.3f}s)")
    finally:
        config.RAW_DIR = real_raw

    table = pd.DataFrame(rows)
    table["per_title_ms"] = table["median_of_5_s"] / table["titles"] * 1000
    out = config.PROJECT_DIR / "out" / "scale_test.csv"
    table.round(4).to_csv(out, index=False, encoding="utf-8-sig")
    print(f"written: {out.relative_to(config.PROJECT_DIR)}")


if __name__ == "__main__":
    main()
