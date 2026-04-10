from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional
from urllib.parse import quote
from wsgiref.handlers import format_date_time

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from websocket import create_connection


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=True, encoding="utf-8-sig")

router = APIRouter(prefix="/tts", tags=["speech-synthesis"])
compat_router = APIRouter(tags=["speech-synthesis-compat"])

XF_HOST = "tts-api.xfyun.cn"
XF_PATH = "/v2/tts"
XF_URL = f"wss://{XF_HOST}{XF_PATH}"


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1200)
    voice_name: str = Field(default="xiaoyan")
    emotion: Literal["neutral", "bright", "calm", "firm"] = "neutral"


class TTSResponse(BaseModel):
    audio_base64: str
    mime_type: str
    voice_name: str
    engine: str
    fallback_used: bool = False


def get_xf_credentials() -> tuple[str, str, str]:
    app_id = os.getenv("XF_APP_ID", "").strip()
    api_key = os.getenv("XF_API_KEY", "").strip()
    api_secret = os.getenv("XF_API_SECRET", "").strip()
    if not app_id or not api_key or not api_secret:
        raise RuntimeError("XF_APP_ID, XF_API_KEY or XF_API_SECRET is not configured.")
    return app_id, api_key, api_secret


def build_auth_url() -> str:
    _, api_key, api_secret = get_xf_credentials()
    date = format_date_time(datetime.now().timestamp())
    signature_origin = f"host: {XF_HOST}\ndate: {date}\nGET {XF_PATH} HTTP/1.1"
    signature = hmac.new(
        api_secret.encode("utf-8"),
        signature_origin.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    signature_b64 = base64.b64encode(signature).decode("utf-8")
    authorization_origin = (
        f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", '
        f'signature="{signature_b64}"'
    )
    authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")
    return (
        f"{XF_URL}?authorization={quote(authorization)}"
        f"&date={quote(date)}&host={quote(XF_HOST)}"
    )


def get_business_params(voice_name: str, emotion: str) -> dict[str, object]:
    presets = {
        "neutral": {"speed": 50, "pitch": 50, "volume": 60},
        "bright": {"speed": 58, "pitch": 62, "volume": 65},
        "calm": {"speed": 40, "pitch": 44, "volume": 58},
        "firm": {"speed": 48, "pitch": 38, "volume": 68},
    }
    profile = presets.get(emotion, presets["neutral"])
    return {
        "aue": "lame",
        "auf": "audio/L16;rate=16000",
        "vcn": voice_name,
        "tte": "utf8",
        "ent": "intp65",
        **profile,
    }


def synthesize_with_xf(text: str, voice_name: str, emotion: str) -> bytes:
    app_id, _, _ = get_xf_credentials()
    ws = create_connection(build_auth_url(), timeout=20)
    payload = {
        "common": {"app_id": app_id},
        "business": get_business_params(voice_name, emotion),
        "data": {
            "status": 2,
            "text": base64.b64encode(text.encode("utf-8")).decode("utf-8"),
        },
    }
    audio_chunks = bytearray()

    try:
        ws.send(json.dumps(payload))
        while True:
            response = json.loads(ws.recv())
            code = response.get("code", -1)
            if code != 0:
                raise RuntimeError(response.get("message", "XF TTS request failed."))

            data = response.get("data", {})
            audio = data.get("audio")
            if audio:
                audio_chunks.extend(base64.b64decode(audio))

            if data.get("status") == 2:
                break
    finally:
        ws.close()

    if not audio_chunks:
        raise RuntimeError("XF TTS returned empty audio.")
    return bytes(audio_chunks)


def synthesize_fallback_tone() -> bytes:
    return b""


@router.post("/speak", response_model=TTSResponse)
@compat_router.post("/api/tts/speak", response_model=TTSResponse, include_in_schema=False)
async def speak_text(request: TTSRequest) -> TTSResponse:
    try:
        audio_bytes = synthesize_with_xf(request.text, request.voice_name, request.emotion)
        fallback_used = False
        engine = "xfyun"
    except Exception as exc:
        fallback_audio = synthesize_fallback_tone()
        if not fallback_audio:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        audio_bytes = fallback_audio
        fallback_used = True
        engine = "fallback"

    return TTSResponse(
        audio_base64=base64.b64encode(audio_bytes).decode("utf-8"),
        mime_type="audio/mpeg",
        voice_name=request.voice_name,
        engine=engine,
        fallback_used=fallback_used,
    )
