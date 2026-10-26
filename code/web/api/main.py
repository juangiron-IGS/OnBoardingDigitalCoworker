"""Web app and API for the five views, on 127.0.0.1 only (TC-002)."""

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .routers import alerts, cases, health, inbox

UI = Path(__file__).resolve().parents[1] / "ui"

app = FastAPI(title="Onboarding Digital Coworker")
app.include_router(inbox.router)
app.include_router(cases.router)
app.include_router(alerts.router)
app.include_router(health.router)
app.include_router(cases.chat_router)


@app.middleware("http")
async def revalidate_ui(request: Request, call_next):  # noqa: ANN001, ANN201
    """The browser revalidates the UI files, so a restart never serves stale code."""
    response = await call_next(request)
    if not request.url.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-cache"
    return response


@app.exception_handler(RequestValidationError)
def invalid_input(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Bad input is a 400 that names each field, never a 500."""
    errors = [
        {
            "field": ".".join(str(p) for p in e["loc"] if p != "body"),
            "message": e["msg"],
        }
        for e in exc.errors()
    ]
    return JSONResponse(status_code=400, content={"detail": errors})


app.mount("/", StaticFiles(directory=UI, html=True), name="ui")


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("WEB_APP_PORT", "3000")))


if __name__ == "__main__":
    main()
