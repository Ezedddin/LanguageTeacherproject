"""
Live voice -> STT -> CEFR assessment (no audio files saved).

Records from your microphone in memory, sends audio to Whisper, and then
uses assessment_agent.py to determine CEFR level.

Requirements:
    pip install openai sounddevice numpy google-genai pydantic
"""

from __future__ import annotations

import io
import os
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import sounddevice as sd
from openai import OpenAI

from assessment_agent import AssessmentAgent


QUESTIONS = [
    "Vraag 1: Vertel je naam.",
    "Vraag 2: Waar kom je vandaan?",
    "Vraag 3: Wat zijn je hobby's?",
    "Vraag 4: Vertel wat je vandaag hebt gedaan.",
]


@dataclass
class RecordingConfig:
    sample_rate: int = 16000
    channels: int = 1
    whisper_model: str = "whisper-1"
    whisper_language: str | None = None


def load_local_env_file() -> None:
    """Load .env from project root if present (without extra dependencies)."""
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def record_audio_to_wav_bytes(config: RecordingConfig) -> bytes:
    """Record from microphone until Enter is pressed, then return WAV bytes."""
    chunks: list[np.ndarray] = []

    def _callback(indata: np.ndarray, frames: int, time: object, status: object) -> None:
        del frames, time
        if status:
            print(f"  Audio status: {status}")
        chunks.append(indata.copy())

    print("  Opnemen gestart. Druk Enter om te stoppen...")
    with sd.InputStream(
        samplerate=config.sample_rate,
        channels=config.channels,
        dtype="int16",
        callback=_callback,
    ):
        input()

    if not chunks:
        raise RuntimeError("Geen audio opgenomen. Probeer opnieuw.")

    print("  Opname gestopt.")
    audio_np = np.concatenate(chunks, axis=0).astype(np.int16)
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(config.channels)
        wav_file.setsampwidth(2)  # int16 = 2 bytes
        wav_file.setframerate(config.sample_rate)
        wav_file.writeframes(audio_np.tobytes())
    return wav_buffer.getvalue()


def transcribe_wav_bytes(
    wav_bytes: bytes,
    client: OpenAI,
    config: RecordingConfig,
) -> str:
    """Send in-memory WAV bytes to Whisper and return transcript."""
    file_obj = io.BytesIO(wav_bytes)
    file_obj.name = "live_input.wav"  # OpenAI SDK expects a filename hint
    transcript = client.audio.transcriptions.create(
        model=config.whisper_model,
        file=file_obj,
        language=config.whisper_language,
        response_format="text",
    )
    return str(transcript).strip()


def run_live_assessment() -> None:
    load_local_env_file()

    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not openai_key:
        raise ValueError("Missing OPENAI_API_KEY in environment.")
    if not gemini_key:
        raise ValueError("Missing GEMINI_API_KEY in environment.")

    config = RecordingConfig()
    openai_client = OpenAI(api_key=openai_key)
    assessor = AssessmentAgent(api_key=gemini_key)

    print("Live stemtest gestart.")
    print("Je antwoord wordt NIET als bestand opgeslagen.")
    print("Per vraag: Enter om te starten, Enter om te stoppen.\n")

    answers: list[str] = []
    for idx, question in enumerate(QUESTIONS, start=1):
        input(f"[{idx}/4] {question}\nDruk Enter om opname te starten...")
        wav_bytes = record_audio_to_wav_bytes(config)
        text = transcribe_wav_bytes(wav_bytes, openai_client, config)
        answers.append(text)
        print(f"  Transcript: {text}\n")

    result = assessor.assess(
        answer1=answers[0],
        answer2=answers[1],
        answer3=answers[2],
        answer4=answers[3],
    )

    print("\n=== CEFR RESULTAAT ===")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    run_live_assessment()
