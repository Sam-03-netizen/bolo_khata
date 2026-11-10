"""Text to speech with Gnani Timbre (REST). Returns MP3 bytes."""
import os, requests

URL = "https://api.vachana.ai/api/v1/tts/inference"
VOICES = {  # (voice, language code)
    "hi": (os.getenv("TTS_VOICE", "Nalini"), "hi-IN"),
    "bn": (os.getenv("TTS_VOICE_BN", "Kirra"), "bn-IN"),
}

def speak(text, lang="hi"):
    voice, code = VOICES.get(lang, VOICES["hi"])
    r = requests.post(
        URL,
        headers={"X-API-Key-ID": os.environ["GNANI_API_KEY"]},
        json={
            "text": text,
            "voice": voice,
            "model": os.getenv("TTS_MODEL", "timbre-v2.5"),
            "language": code,
            "speed": 1.0,
            "audio_config": {"container": "mp3", "sample_rate": 24000, "num_channels": 1},
        },
        timeout=60,
    )
    if r.status_code != 200:
        raise RuntimeError(f"Text-to-speech failed ({r.status_code}): {r.text[:200]}")
    return r.content
