from __future__ import annotations

import os
import subprocess
import sys
import traceback
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles


ROOT_DIR = Path(__file__).resolve().parent
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))


class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"


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


app = FastAPI(
    title="EduMAS Unified Service",
    description="Frontend pages and API gateway served from a single process.",
    version="1.0.0",
    default_response_class=UTF8JSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "edumas-unified-service"}


@app.get("/", include_in_schema=False)
async def root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/login.html", status_code=307)


def _include_gateway_routers() -> None:
    if getattr(app.state, "routers_registered", False):
        return

    from gateway.assessment_gateway import compat_router as assessment_compat_router
    from gateway.assessment_gateway import router as assessment_router
    from gateway.fedgnn_gateway import router as fedgnn_router
    from gateway.governance_gateway import router as governance_router
    from gateway.planning_gateway import router as planning_router
    from gateway.privacy_lab_gateway import compat_router as privacy_compat_router
    from gateway.privacy_lab_gateway import router as privacy_router
    from gateway.teacher_gateway import router as teacher_router
    from gateway.tutoring_gateway import compat_router as tutoring_compat_router
    from gateway.tutoring_gateway import router as tutoring_router
    from gateway.tts_gateway import compat_router as tts_compat_router
    from gateway.tts_gateway import router as tts_router

    app.include_router(planning_router)
    app.include_router(tutoring_router)
    app.include_router(tutoring_compat_router)
    app.include_router(assessment_router)
    app.include_router(assessment_compat_router)
    app.include_router(fedgnn_router)
    app.include_router(governance_router)
    app.include_router(privacy_router)
    app.include_router(privacy_compat_router)
    app.include_router(teacher_router)
    app.include_router(tts_router)
    app.include_router(tts_compat_router)
    app.state.routers_registered = True


@app.on_event("startup")
async def startup_register_routes() -> None:
    print("[app] startup begin")
    try:
        _include_gateway_routers()
        if not getattr(app.state, "static_mounted", False):
            app.mount("/", StaticFiles(directory=str(ROOT_DIR), html=False), name="static")
            app.state.static_mounted = True
        print("[app] startup complete")
    except Exception:
        print("[app] startup failed")
        traceback.print_exc()
        raise


def run() -> None:
    _ensure_runtime()
    import uvicorn

    print(f"EduMAS unified service is available at: http://{HOST}:{PORT}/login.html")
    print("Serving frontend pages and API gateway from a single process.")
    uvicorn.run("app:app", host=HOST, port=PORT, reload=False)


if __name__ == "__main__":
    run()
