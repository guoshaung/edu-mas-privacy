import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gateway.assessment_gateway import compat_router as assessment_compat_router
from gateway.assessment_gateway import router as assessment_router
from gateway.planning_gateway import router as planning_router
from gateway.privacy_lab_gateway import compat_router as privacy_compat_router
from gateway.privacy_lab_gateway import router as privacy_router
from gateway.tutoring_gateway import compat_router as tutoring_compat_router
from gateway.tutoring_gateway import router as tutoring_router
from gateway.tts_gateway import compat_router as tts_compat_router
from gateway.tts_gateway import router as tts_router


app = FastAPI(
    title="EduMAS Cloud Gateway",
    description="FastAPI privacy gateway for learning planning, adaptive tutoring, and assessment.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(planning_router)
app.include_router(tutoring_router)
app.include_router(tutoring_compat_router)
app.include_router(assessment_router)
app.include_router(assessment_compat_router)
app.include_router(privacy_router)
app.include_router(privacy_compat_router)
app.include_router(tts_router)
app.include_router(tts_compat_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "edumas-cloud-gateway"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "deploy.planning_gateway_api:app",
        host="127.0.0.1",
        port=8010,
        reload=False,
    )
