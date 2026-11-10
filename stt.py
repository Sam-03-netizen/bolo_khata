"""Speech to text with Gnani Prisma v3.0 (REST)."""
import json, os, requests

URL = "https://api.vachana.ai/stt/v3"
LANGS = {"hi": "hi-IN,en-IN", "bn": "bn-IN,en-IN"}  # the language you picked + English
TERMS = {"hi": ["उधार", "वापस", "हिसाब", "बाकी", "जमा", "रुपये"],
         "bn": ["ধার", "ফেরত", "হিসাব", "বাকি", "জমা", "টাকা"]}

def transcribe(path, names=(), lang="hi"):
    lang = lang if lang in LANGS else "hi"
    terms = (TERMS[lang] + list(names))[:200]
    with open(path, "rb") as f:
        r = requests.post(
            URL,
            headers={"X-API-Key-ID": os.environ["GNANI_API_KEY"]},
            files={"audio_file": ("clip.wav", f, "audio/wav")},
            data={
                "model": "prisma-v3.0",
                "language_code": LANGS[lang],
                "format": "transcribe",  # numbers come back as digits, e.g. ₹500
                "keyterms": json.dumps(terms, ensure_ascii=False),
            },
            timeout=60,
        )
    if r.status_code != 200:
        raise RuntimeError(f"Speech-to-text failed ({r.status_code}): {r.text[:200]}")
    return r.json().get("transcript", "").strip()
