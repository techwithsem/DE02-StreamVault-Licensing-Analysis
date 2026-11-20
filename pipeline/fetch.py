"""fetching film details and credits from tmdb.

every answer is being saved to data/raw with the time it was fetched, and the
cache is checked first, so re-running the pipeline is not calling the api again.
"""

import json
import time
from datetime import UTC, datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from pipeline import config


class TimeoutAdapter(HTTPAdapter):
    """making a timeout the default, so nobody has to remember to pass one."""

    def __init__(self, *args, timeout=config.TIMEOUT, **kwargs):
        self.timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        if kwargs.get("timeout") is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


def make_session(api_key):
    """building one session that is retrying only the failures worth retrying."""
    retry = Retry(
        total=5,
        backoff_factor=1,                              # waiting 1s, 2s, 4s, 8s ...
        status_forcelist=[429, 500, 502, 503, 504],    # busy or broken, try again
        allowed_methods=["GET"],
        respect_retry_after_header=True,               # obeying tmdb when it says wait
        raise_on_status=False,                         # handing back the last answer
    )
    session = requests.Session()
    session.mount("https://", TimeoutAdapter(max_retries=retry))
    session.headers.update({"Accept": "application/json", "User-Agent": config.USER_AGENT})

    # accepting both kinds of tmdb key: the long read token or the short api key
    if api_key.startswith("eyJ"):
        session.headers["Authorization"] = f"Bearer {api_key}"
    else:
        session.params = {"api_key": api_key}
    return session


def _now():
    return datetime.now(UTC).isoformat(timespec="seconds")


def get_cached(session, path, cache_file, params=None, refresh=False):
    """returning the saved answer if there is one, otherwise calling tmdb once.

    gives back (record, came_from_cache). a record holds the http status, the
    fetch time and the body. 404s are being saved too, so a dead id is not
    asked about again on the next run.
    """
    if cache_file.exists() and not refresh:
        return json.loads(cache_file.read_text(encoding="utf-8")), True

    try:
        response = session.get(config.BASE_URL + path, params=params)
    except requests.exceptions.RequestException as error:
        # not caching network trouble, so the next run is trying again
        return {"http_status": None, "error": type(error).__name__,
                "fetched_at": _now(), "body": None}, False
    finally:
        time.sleep(config.PAUSE_SECONDS)

    if response.status_code in (401, 403):
        raise SystemExit(
            f"tmdb refused the key (http {response.status_code}). "
            "check TMDB_API_KEY in your .env file."
        )

    try:
        body = response.json()
    except ValueError:
        body = None

    record = {"path": path, "http_status": response.status_code,
              "fetched_at": _now(), "body": body}

    # saving only final answers: a good answer or a confirmed "not found"
    if response.status_code in (200, 404) and body is not None:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record, False


def status_of(record):
    """turning an http result into a short word for the logs."""
    code = record.get("http_status")
    if code == 200:
        return "ok"
    if code == 404:
        return "not_found"
    if code is None:
        return "network_error"
    return f"http_{code}"


def resolve_imdb_id(session, imdb_id, refresh=False):
    """translating an imdb id (tt...) into a tmdb film id using tmdb's /find."""
    record, _ = get_cached(
        session, f"/find/{imdb_id}", config.FIND_DIR / f"{imdb_id}.json",
        params={"external_source": "imdb_id"}, refresh=refresh,
    )
    body = record.get("body") or {}
    films = body.get("movie_results") or []
    return (films[0]["id"] if films else None), status_of(record)


def fetch_film(session, tmdb_id, refresh=False):
    """fetching details and credits for one film and logging what happened."""
    rows = []
    for endpoint, path in (("details", f"/movie/{tmdb_id}"),
                           ("credits", f"/movie/{tmdb_id}/credits")):
        cache_file = config.RAW_DIR / str(tmdb_id) / f"{endpoint}.json"
        record, from_cache = get_cached(session, path, cache_file, refresh=refresh)
        body = record.get("body") or {}
        rows.append({
            "tmdb_id": tmdb_id,
            "endpoint": endpoint,
            "status": status_of(record),
            "http_status": record.get("http_status"),
            # checking tmdb sent back the film that was asked for, not a different one
            "returned_id": body.get("id") if record.get("http_status") == 200 else None,
            "fetched_at": record.get("fetched_at"),
            "from_cache": from_cache,
        })
    return rows
