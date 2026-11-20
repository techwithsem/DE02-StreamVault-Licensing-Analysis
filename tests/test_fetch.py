"""checking the fetch rules with a fake tmdb, so no real calls are being made."""

import json

import pytest

from pipeline import acquire, config, fetch


class FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body


class FakeSession:
    """pretending to be tmdb: answering from a dict and counting the calls."""

    def __init__(self, answers):
        self.answers = answers
        self.calls = []

    def get(self, url, params=None):
        path = url.replace(config.BASE_URL, "")
        self.calls.append(path)
        return FakeResponse(*self.answers.get(path, (404, {"status_code": 34})))


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """pointing every output at a temporary folder and skipping the pauses."""
    monkeypatch.setattr(config, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(config, "FIND_DIR", tmp_path / "raw" / "_find")
    monkeypatch.setattr(config, "ID_ACCOUNTING_FILE", tmp_path / "id_accounting.csv")
    monkeypatch.setattr(config, "FETCH_LOG_FILE", tmp_path / "fetch_log.csv")
    monkeypatch.setattr(config, "PAUSE_SECONDS", 0)
    return tmp_path


def test_saving_answers_and_reusing_them(sandbox):
    session = FakeSession({"/movie/1": (200, {"id": 1, "title": "a"})})
    cache = sandbox / "raw" / "1" / "details.json"

    first, from_cache_1 = fetch.get_cached(session, "/movie/1", cache)
    second, from_cache_2 = fetch.get_cached(session, "/movie/1", cache)

    assert (from_cache_1, from_cache_2) == (False, True)
    assert len(session.calls) == 1                      # only one live call
    saved = json.loads(cache.read_text(encoding="utf-8"))
    assert saved["http_status"] == 200 and saved["fetched_at"]
    assert second["body"]["title"] == "a"


def test_not_found_is_saved_so_it_is_not_asked_again(sandbox):
    session = FakeSession({})
    cache = sandbox / "raw" / "9" / "details.json"
    fetch.get_cached(session, "/movie/9", cache)
    record, from_cache = fetch.get_cached(session, "/movie/9", cache)
    assert from_cache and fetch.status_of(record) == "not_found"
    assert len(session.calls) == 1


def test_bad_key_stops_the_run(sandbox):
    session = FakeSession({"/movie/1": (401, {"status_code": 7})})
    with pytest.raises(SystemExit, match="refused the key"):
        fetch.get_cached(session, "/movie/1", sandbox / "x.json")


def test_server_errors_are_not_cached(sandbox):
    session = FakeSession({"/movie/1": (503, {})})
    cache = sandbox / "raw" / "1" / "details.json"
    record, _ = fetch.get_cached(session, "/movie/1", cache)
    assert fetch.status_of(record) == "http_503"
    assert not cache.exists()                            # next run is trying again


def test_retry_policy_only_retries_temporary_failures():
    retry = fetch.make_session("abc").get_adapter("https://x").max_retries
    assert set(retry.status_forcelist) == {429, 500, 502, 503, 504}
    assert retry.respect_retry_after_header
    assert 404 not in retry.status_forcelist and 401 not in retry.status_forcelist


def test_both_kinds_of_key_are_accepted():
    assert fetch.make_session("abc123").params == {"api_key": "abc123"}
    bearer = fetch.make_session("eyJhbGciOi.token")
    assert bearer.headers["Authorization"] == "Bearer eyJhbGciOi.token"


def test_every_input_row_gets_exactly_one_outcome(sandbox, monkeypatch):
    id_file = sandbox / "ids.csv"
    id_file.write_text("tmdb_id\n1\n2\n1\n\nN/A\n-1\ntt001\ntt999\n3\n", encoding="utf-8")
    monkeypatch.setattr(config, "ID_FILE", id_file)

    session = FakeSession({
        "/movie/1": (200, {"id": 1}), "/movie/1/credits": (200, {"id": 1}),
        "/movie/2": (200, {"id": 2}), "/movie/2/credits": (200, {"id": 2}),
        "/find/tt001": (200, {"movie_results": [{"id": 2}]}),   # imdb id hiding film 2
        "/find/tt999": (200, {"movie_results": []}),
    })
    accounting, log = acquire.run(session)

    assert len(accounting) == 9
    assert accounting["outcome"].notna().all()
    outcomes = dict(zip(accounting["raw_value"], accounting["outcome"], strict=True))
    assert outcomes["2"] == "kept: details and credits fetched"
    assert outcomes["tt001"] == "dropped: duplicate of an earlier row"
    assert outcomes["tt999"] == "dropped: imdb id with no tmdb match"
    assert outcomes["3"] == "dropped: tmdb has no film with this id"
    assert outcomes[""] == "dropped: blank row"
    assert outcomes["N/A"] == "dropped: placeholder text, not an id"
    assert outcomes["-1"] == "dropped: not a valid id"
    # each distinct film is fetched once: details and credits for 1, 2 and 3
    assert len(log) == 6
