import logging
from collections import Counter

logger = logging.getLogger(__name__)


class ModelBudgetExceeded(Exception):
    """A run reached MODEL_USAGE_CAP_PER_RUN (TC-004)."""


class UsageMeter:
    """Counts model calls per run and per case and refuses calls past the cap.

    Every model call goes through record() before it is made (TC-004).
    """

    def __init__(self, cap_per_run: int) -> None:
        if cap_per_run < 1:
            raise ValueError("cap_per_run must be at least 1")
        self._cap = cap_per_run
        self._per_run: Counter[str] = Counter()
        self._per_case: Counter[tuple[str, str]] = Counter()

    def record(self, *, run_id: str, case_id: str, provider: str) -> None:
        if self._per_run[run_id] >= self._cap:
            raise ModelBudgetExceeded(f"run {run_id} reached its cap of {self._cap}")
        self._per_run[run_id] += 1
        self._per_case[(run_id, case_id)] += 1
        logger.info(
            "model call",
            extra={"case_id": case_id, "run_id": run_id, "provider": provider},
        )

    def calls(self, *, run_id: str, case_id: str | None = None) -> int:
        if case_id is None:
            return self._per_run[run_id]
        return self._per_case[(run_id, case_id)]
