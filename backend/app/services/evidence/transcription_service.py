"""Speech-to-text transcription for visit recordings (Azure AI Speech --
Fast Transcription REST API).

Design contract (same shape as note_draft_service.py / ai_extraction_service.py):
    - NEVER raises. Any failure (not configured, network error, malformed
      response, unsupported audio) is logged and results in `None` -- the
      caller (app.api.visit_recordings) always still preserves the audio
      and the recording row untouched, and is responsible for persisting
      the FAILED/RETRYING state.
    - NEVER fabricates. If the API call fails or returns no transcript,
      this returns None -- it is never acceptable to invent a transcript.

Required environment variables:
    AZURE_SPEECH_KEY
    AZURE_SPEECH_REGION

Uses the Fast Transcription API (POST .../speechtotext/transcriptions:transcribe),
a synchronous, single-file endpoint that returns the transcript directly in
the response body -- no separate blob storage / polling infrastructure is
required, which fits this app's own (non-Azure-Blob) recording storage.
Audio must be under 2 hours / 250MB; hospice visit recordings are always
far smaller than that limit.
"""

from __future__ import annotations

import json
import logging
import os

import httpx

logger = logging.getLogger("sns_emr")

DEFAULT_TIMEOUT_SECONDS = 120.0
API_VERSION = "2024-11-15"
DEFAULT_LOCALE = "en-US"


def azure_speech_configured() -> bool:
    """True if AZURE_SPEECH_KEY/AZURE_SPEECH_REGION are both set. Lets
    callers report NOT_CONFIGURED distinctly from a genuine call failure."""
    return _azure_speech_config() is not None


def _azure_speech_config() -> dict[str, str] | None:
    key = os.getenv("AZURE_SPEECH_KEY")
    region = os.getenv("AZURE_SPEECH_REGION")
    if not (key and region):
        return None
    return {"key": key, "region": region}


def _filename_for_content_type(content_type: str | None) -> str:
    ct = (content_type or "").lower()
    if "webm" in ct:
        return "recording.webm"
    if "wav" in ct:
        return "recording.wav"
    if "mpeg" in ct or "mp3" in ct:
        return "recording.mp3"
    if "ogg" in ct or "opus" in ct:
        return "recording.ogg"
    return "recording.audio"


def transcribe_audio_bytes(
    audio_bytes: bytes,
    *,
    content_type: str | None,
    locale: str = DEFAULT_LOCALE,
) -> str | None:
    """Synchronously transcribe one audio file via Azure AI Speech's Fast
    Transcription API. Returns the combined transcript text, or None if not
    configured, the audio is empty, or the call fails/returns nothing for
    any reason. Never raises.
    """
    config = _azure_speech_config()
    if config is None:
        logger.info("transcription_service: AZURE_SPEECH_KEY/REGION not configured -- skipping")
        return None
    if not audio_bytes:
        return None

    url = (
        f"https://{config['region']}.api.cognitive.microsoft.com"
        f"/speechtotext/transcriptions:transcribe?api-version={API_VERSION}"
    )
    filename = _filename_for_content_type(content_type)
    definition = json.dumps({"locales": [locale]})

    try:
        response = httpx.post(
            url,
            headers={"Ocp-Apim-Subscription-Key": config["key"]},
            files={"audio": (filename, audio_bytes, content_type or "application/octet-stream")},
            data={"definition": definition},
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        body = response.json()
    except Exception:
        logger.exception("transcription_service: Azure Speech fast-transcription call failed")
        return None

    combined = body.get("combinedPhrases")
    if isinstance(combined, list) and combined:
        text = " ".join(str(p.get("text") or "").strip() for p in combined if isinstance(p, dict))
        text = text.strip()
        return text or None

    logger.warning("transcription_service: Azure Speech returned no combinedPhrases")
    return None
