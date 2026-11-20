# ADR-007: Fetch once, save every answer with a timestamp, and commit the snapshot

**Status:** accepted · **Findings:** F07, F17

## Context
TMDb is a free, shared service. Its data is edited by its community and changes daily. Adjoa will rerun the analysis every quarter, sometimes live in a meeting, and a board member may ask why a figure differs from someone else's.

## Decision
- **Every TMDb answer is saved** in `data/raw/<id>/` with the time it was fetched. Later runs read the saved copy and make no calls. `--refresh` fetches again on purpose.
- **"Not found" answers are saved too,** so dead ids are not asked about again. Network failures are not saved, so they are retried on the next run.
- **Polite fetching:**
  - a 0.25-second pause between live calls
  - a time limit on every call
  - retries only for "busy" or server errors, with growing waits and obeying TMDb's "retry after"
  - never retrying "not found" or "bad key"
  - a plain User-Agent with no personal details
- **The run stops with a clear message** if the key is missing or refused, or if any film fails to download.
- **I recommend committing `data/raw/` to the repository,** so anyone who clones it can reproduce the exact numbers in the memo. They are as of 20 Nov 2026, and the memo quotes that date. The API key is never saved in these files; this was checked by searching every file for it.

## Alternative rejected
1. **Fetching live on every run.** This is slower (about 2 minutes against 0.2 seconds), unkind to TMDb, and gives different answers on different days for reasons no one can explain in the room.
2. **One call per film using `append_to_response=credits`.** This would halve the number of calls, but the brief names the two endpoints, and the spot-check compares them separately. It's noted as a possible change.

## Cost if wrong
A snapshot ages. The live spot-check on 20 Nov 2026 found 0 differences in 98 values, so the snapshot matched TMDb on the day. Next quarter, Adjoa should run `--refresh` and then `--spot-check`.

## What survives
The cache, the retry rules and the stop-on-failure behaviour are all tested without the network (`tests/test_fetch.py`). With 500 titles, the first fetch takes about 10 minutes (about 1,000 calls with pauses); every rerun after that takes seconds.
