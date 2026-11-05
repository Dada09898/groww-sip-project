"""One place for all LLM calls, so you can switch provider in .env:
LLM_PROVIDER=gemini     -> Google Gemini (free tier, needs GEMINI_API_KEY from aistudio.google.com)
LLM_PROVIDER=anthropic  -> Claude (paid, needs ANTHROPIC_API_KEY)"""
import os, time, threading, requests
from config import (LLM_PROVIDER, TAG_MODEL, SYNTH_MODEL, GEMINI_API_KEY,
                    GEMINI_TAG_MODEL, GEMINI_SYNTH_MODEL, GEMINI_RPM)

_lock = threading.Lock()
_last = [0.0]

def _throttle():
    """Free Gemini tier has a low requests-per-minute limit. Space calls out evenly."""
    gap = 60.0 / max(GEMINI_RPM, 1)
    with _lock:
        wait = _last[0] + gap - time.time()
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()

def _gemini(system, user, max_tokens, model, json_mode):
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY missing in .env")
    body = {"contents": [{"role": "user", "parts": [{"text": user}]}],
            # generous limit: some Gemini models spend part of it on internal "thinking"
            "generationConfig": {"maxOutputTokens": max(max_tokens * 4, 2048)}}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    if json_mode:
        body["generationConfig"]["responseMimeType"] = "application/json"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    for attempt in range(6):
        _throttle()
        try:
            r = requests.post(url, json=body, timeout=300,
                              headers={"x-goog-api-key": GEMINI_API_KEY})
        except (requests.Timeout, requests.ConnectionError) as e:
            print(f"  gemini: {type(e).__name__}, retrying ({attempt + 1}/6)")
            time.sleep(10 * (attempt + 1))
            continue
        if r.status_code in (429, 500, 503):
            time.sleep(min(20 * (attempt + 1), 90))   # rate limited or busy: wait, retry
            continue
        if r.status_code != 200:
            raise RuntimeError(f"Gemini {r.status_code}: {r.text[:300]}")
        js = r.json()
        parts = js.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        if not text:
            raise RuntimeError(f"Gemini returned no text: {str(js)[:300]}")
        return text
    raise RuntimeError("Gemini: no answer after 6 tries (timeouts, or daily free quota used up)")

_anth = None
def _anthropic(system, user, max_tokens, model):
    global _anth
    import anthropic
    if _anth is None:
        _anth = anthropic.Anthropic(max_retries=6)
    kw = {"model": model, "max_tokens": max_tokens,
          "messages": [{"role": "user", "content": user}]}
    if system:
        kw["system"] = system
    return _anth.messages.create(**kw).content[0].text

def complete(user, system="", max_tokens=1000, kind="tag", json_mode=False):
    """kind='tag' uses the cheap/fast model, kind='synth' the stronger one."""
    if LLM_PROVIDER == "gemini":
        model = GEMINI_TAG_MODEL if kind == "tag" else GEMINI_SYNTH_MODEL
        return _gemini(system, user, max_tokens, model, json_mode)
    model = TAG_MODEL if kind == "tag" else SYNTH_MODEL
    return _anthropic(system, user, max_tokens, model)
