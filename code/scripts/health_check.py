"""Wait for the web app (and, over MCP, its servers) to be healthy; print one line
or exit 1."""

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
            servers = body.get("mcp_servers", {})
            if any(state != "ok" for state in servers.values()):
                # MCP servers may still be starting: keep waiting until the deadline.
                last_error = f"MCP servers: {servers}"
                time.sleep(1)
                continue
            line = (
                f"web app: {body['status']} · database: {body['database']} · "
                f"transport: {body['transport']} · JobDiva: {body['jobdiva_mode']} · "
                f"model: {body['model_provider']}"
            )
            if servers:
                line += " · MCP: " + ", ".join(f"{n} {s}" for n, s in servers.items())
            print(line)
            return 0
        except (urllib.error.URLError, OSError, ValueError) as exc:
            last_error = str(exc)
            time.sleep(1)
    print(f"web app did not become healthy at {URL}: {last_error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
