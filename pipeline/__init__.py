# the streamvault pipeline: each module is handling one stage of the run

import sys

# stopping early with a plain message on an old python, before any package fails oddly
if sys.version_info < (3, 11):  # noqa: UP036 (kept on purpose for older pythons)
    raise SystemExit(
        f"this project needs python 3.11 or newer; you are running {sys.version.split()[0]}."
    )
