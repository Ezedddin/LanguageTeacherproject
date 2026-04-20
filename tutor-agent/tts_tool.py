from __future__ import annotations

import json

from langchain_core.tools import tool


@tool("pyttsx3_tts_tool")
def pyttsx3_tts_tool(text: str, rate: int = 180, volume: float = 1.0) -> str:
    """
    Convert text to speech using pyttsx3 and speak directly.

    Args:
        text: Text to synthesize.
        rate: Speech rate (words/minute style value).
        volume: Volume from 0.0 to 1.0.
    """
    if not text or not text.strip():
        raise ValueError("Text is required for TTS.")

    import pyttsx3

    volume = max(0.0, min(1.0, float(volume)))
    rate = int(rate)

    engine = pyttsx3.init()
    engine.setProperty("rate", rate)
    engine.setProperty("volume", volume)
    engine.say(text)
    engine.runAndWait()

    payload = {"status": "spoken"}
    return json.dumps(payload, ensure_ascii=True)
