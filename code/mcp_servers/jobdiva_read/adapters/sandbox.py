"""JobDiva sandbox, read only (JOBDIVA_MODE=sandbox). The Coworker never writes to
JobDiva in any mode (BR-014, ADR-004).

Authentication uses the API user, not the web login: a Client ID from JobDiva
support plus a dedicated API user. The token lives in memory only and never
reaches a log, the database or a response. The endpoint paths follow integrator
guides and must be confirmed against JobDiva's API documentation before use.
"""

import logging
from datetime import date

import httpx

logger = logging.getLogger(__name__)
# httpx logs full request URLs at INFO; the authenticate call carries credentials.
logging.getLogger("httpx").setLevel(logging.WARNING)

AUTHENTICATE = "/apiv2/authenticate"
START_BY_ID = "/apiv2/jobdiva/searchStart"
START_NOTES = "/apiv2/jobdiva/getStartNotes"


class ReadOnlyViolation(Exception):
    """A non-read request to JobDiva was attempted and refused."""


class SandboxJobDiva:
    def __init__(
        self,
        *,
        base_url: str,
        client_id: str,
        api_user: str,
        api_password: str,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(base_url=base_url, transport=transport, timeout=20)
        self._credentials = {
            "clientid": client_id,
            "username": api_user,
            "password": api_password,
        }
        self._token: str | None = None

    def __repr__(self) -> str:
        return "SandboxJobDiva(read-only, token=<hidden>)"

    def read_start(self, start_id: str) -> dict:
        rows = self.request("GET", START_BY_ID, params={"startid": start_id})
        return rows[0] if rows else {}

    def read_start_notes(self, start_id: str) -> dict:
        rows = self.request("GET", START_NOTES, params={"startid": start_id})
        return rows[0] if rows else {}

    def search_duplicate(self, person_ref: str, start_date: date) -> dict:
        rows = self.request(
            "GET",
            START_BY_ID,
            params={"candidateid": person_ref, "startdate": start_date.isoformat()},
        )
        if rows:
            return {"found": True, "start_id": str(rows[0].get("STARTID"))}
        return {"found": False, "start_id": None}

    def request(self, method: str, path: str, params: dict | None = None) -> list[dict]:
        """The only way out to JobDiva. Anything but a read is refused (BR-014)."""
        if method.upper() != "GET":
            logger.warning("JobDiva write refused: %s %s", method.upper(), path)
            raise ReadOnlyViolation(f"{method.upper()} {path}")
        response = self._client.get(
            path,
            params=params,
            headers={"Authorization": f"Bearer {self._get_token()}"},
        )
        response.raise_for_status()
        body = response.json()
        return body.get("data", []) if isinstance(body, dict) else body

    def _get_token(self) -> str:
        if self._token is None:
            try:
                response = self._client.get(AUTHENTICATE, params=self._credentials)
                response.raise_for_status()
            except httpx.HTTPError as error:
                raise _without_credentials(error) from None
            self._token = response.text.strip()
        return self._token


def _without_credentials(error: httpx.HTTPError) -> httpx.HTTPError:
    """The sign-in call carries the API password in its query string, so httpx's
    error (its message and its request) would carry it too (NFR-SEC-005, DEF-002).
    Return the same kind of error naming only the path and the status; the
    original is dropped (``from None``) so no traceback shows it either."""
    original = error.request
    safe = httpx.Request(original.method, original.url.copy_with(query=None))
    if isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code
        return httpx.HTTPStatusError(
            f"JobDiva sign-in failed: HTTP {status} from {safe.url}",
            request=safe,
            response=httpx.Response(status, request=safe),
        )
    return type(error)(
        f"JobDiva sign-in failed: {type(error).__name__} for {safe.url}", request=safe
    )
