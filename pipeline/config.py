"""settings shared by every stage. paths are relative to the project folder, so
the code is running the same way on any laptop."""

import os
from pathlib import Path

from dotenv import load_dotenv

# finding the project folder from this file's location, not from where the
# command was typed
PROJECT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"            # one folder per film, holding the api answers
FIND_DIR = RAW_DIR / "_find"          # answers for imdb ids being translated
ID_FILE = DATA_DIR / "id_list.csv"
ID_ACCOUNTING_FILE = DATA_DIR / "id_accounting.csv"
FETCH_LOG_FILE = DATA_DIR / "fetch_log.csv"

BASE_URL = "https://api.themoviedb.org/3"

# waiting up to 3.05s to connect and 10s for an answer, so no call can hang
TIMEOUT = (3.05, 10)

# pausing between live calls so the run is staying well under tmdb's rate limit
PAUSE_SECONDS = 0.25

# telling tmdb who is calling, without any personal details
USER_AGENT = "streamvault-licensing-analysis/1.0 (course project)"

# the time budget for the analysis (stages 2 to 5, from the cache, not counting
# downloads). adjoa may run this live in a meeting, so it has to feel instant
TIME_BUDGET_SECONDS = 10

# text that people type when they mean "no value"
MISSING_TOKENS = {"n/a", "na", "nan", "null", "none", "-", "?"}


def get_api_key():
    """reading the tmdb key from .env and stopping loudly if it is missing."""
    load_dotenv(PROJECT_DIR / ".env")
    key = os.getenv("TMDB_API_KEY", "").strip()
    if not key or key == "put_your_tmdb_api_key_here":
        raise SystemExit(
            "no tmdb key found.\n"
            "copy .env.example to .env and put your own key after TMDB_API_KEY=\n"
            "you can get a free key at https://www.themoviedb.org/settings/api"
        )
    return key
