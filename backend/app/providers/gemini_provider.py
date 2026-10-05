"""Google Gemini through its free API tier."""
import json
from typing import Iterator

import httpx

from app import config
from app.providers.base import BaseProvider, ProviderError

API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self, api_key=None, model=None, client=None):
        self.api_key = api_key or config.GEMINI_API_KEY
        self.model = model or config.GEMINI_MODEL
        self._client = client

    def stream(self, messages: list[dict], system: str) -> Iterator[str]:
        if not self.api_key:
            raise ProviderError("GEMINI_API_KEY is missing. Add it to backend/.env")

        url = f"{API_ROOT}/{self.model}:streamGenerateContent?alt=sse"
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [
                {
                    "role": "model" if m["role"] == "assistant" else "user",
                    "parts": [{"text": m["content"]}],
                }
                for m in messages
            ],
        }
        headers = {"x-goog-api-key": self.api_key}
        client = self._client or httpx.Client(timeout=config.REQUEST_TIMEOUT)
        try:
            with client.stream("POST", url, json=payload, headers=headers) as r:
                if r.status_code != 200:
                    r.read()
                    raise ProviderError(self._explain(r.status_code))
                for line in r.iter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if not raw:
                        continue
                    data = json.loads(raw)
                    for cand in data.get("candidates", []):
                        for part in cand.get("content", {}).get("parts", []):
                            text = part.get("text", "")
                            if text:
                                yield text
        except httpx.ConnectError:
            raise ProviderError("Can't reach Gemini. Check your internet connection.") from None
        except httpx.TimeoutException:
            raise ProviderError("Gemini took too long to answer. Try again.") from None

    def _explain(self, status: int) -> str:
        if status in (400, 401, 403):
            return "Gemini rejected the request. Check that GEMINI_API_KEY is correct."
        if status == 404:
            return f"Model '{self.model}' was not found. Set a current GEMINI_MODEL in backend/.env"
        if status == 429:
            return "Free-tier limit reached. Wait a minute and try again."
        return f"Gemini error {status}."