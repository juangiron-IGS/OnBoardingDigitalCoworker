import json
from datetime import date
from pathlib import Path

SEED = Path(__file__).resolve().parents[3] / "db" / "seed" / "jobdiva" / "starts.json"


class MockJobDiva:
    """JobDiva on synthetic data (JOBDIVA_MODE=mock, the default). Reads only."""

    def __init__(self, seed: Path = SEED) -> None:
        data = json.loads(seed.read_text(encoding="utf-8"))
        self._starts = {s["start_id"]: s for s in data["starts"]}
        self._onboarding = data["onboarding_records"]

    def read_start(self, start_id: str) -> dict:
        start = self._starts[start_id]
        return {k: v for k, v in start.items() if k != "notes"}

    def read_start_notes(self, start_id: str) -> dict:
        return dict(self._starts[start_id]["notes"])

    def search_duplicate(self, person_ref: str, start_date: date) -> dict:
        """An onboarding already in JobDiva for the same person and start date."""
        for record in self._onboarding:
            if record["person_ref"] == person_ref and record["start_date"] == str(
                start_date
            ):
                return {"found": True, "start_id": record["start_id"]}
        return {"found": False, "start_id": None}
