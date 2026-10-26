"""Wait for the web app to answer /api/health; print one line or exit 1."""

import json
import os
import sys
import time
import urllib.error
import urllib.request

URL = f"http://127.0.0.1:{os.environ.get('WEB_APP_PORT', '3000')}/api/health"
TIMEOUT_SECONDS = 60


def main() -> int:
    deadline = time.monotonic() + TIMEOUT_SECONDS
    last_error = "no answer"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(URL, timeout=3) as response:  # noqa: S310 - fixed local URL
                body = json.load(response)
            print(
                f"web app: {body['status']} · database: {body['database']} · "
                f"JobDiva: {body['jobdiva_mode']} · model: {body['model_provider']}"
            )
            return 0
        except (urllib.error.URLError, OSError, ValueError) as exc:
            last_error = str(exc)
            time.sleep(1)
    print(f"web app did not become healthy at {URL}: {last_error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
