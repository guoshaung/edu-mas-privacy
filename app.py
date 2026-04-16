from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))


def _venv_python() -> Path:
    if os.name == "nt":
        return ROOT_DIR / ".venv" / "Scripts" / "python.exe"
    return ROOT_DIR / ".venv" / "bin" / "python"


def _running_inside_venv() -> bool:
    return ".venv" in Path(sys.executable).parts


def _ensure_runtime() -> None:
    try:
        import uvicorn  # noqa: F401
        import fastapi  # noqa: F401
    except ModuleNotFoundError:
        venv_python = _venv_python()
        if venv_python.exists() and not _running_inside_venv():
            print("Current Python is missing project dependencies. Switching to the local .venv interpreter...")
            completed = subprocess.run([str(venv_python), *sys.argv], cwd=str(ROOT_DIR))
            raise SystemExit(completed.returncode)

        raise SystemExit(
            "Required dependencies are missing. Please install requirements or run with the project virtual environment:\n"
            r".\.venv\Scripts\python.exe app.py"
        )


from fastapi.responses import RedirectResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from deploy.planning_gateway_api import app as app  # noqa: E402


@app.get("/", include_in_schema=False)
async def root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/login.html", status_code=307)


# Serve the repository root as the static site so login.html and frontend/*
# are available from the same process as the FastAPI gateway.
app.mount("/", StaticFiles(directory=str(ROOT_DIR), html=False), name="static")


def run() -> None:
    _ensure_runtime()
    import uvicorn

    print(f"EduMAS unified service is available at: http://{HOST}:{PORT}/login.html")
    print("Serving frontend pages and API gateway from a single process.")
    uvicorn.run("app:app", host=HOST, port=PORT, reload=False)


if __name__ == "__main__":
    run()
