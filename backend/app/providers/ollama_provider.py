"""Free, local models through Ollama."""
import json
from typing import Iterator

import httpx

from app import config
from app.providers.base import BaseProvider, ProviderError


class OllamaProvider(BaseProvider):
    name = "ollama"

    def __init__(self, url=None, model=None, client=None):
        self.url = (url or config.OLLAMA_URL).rstrip("/")
        self.model = model or config.OLLAMA_MODEL
        self._client = client

    def stream(self, messages: list[dict], system: str) -> Iterator[str]:
        payload = {
            "model": self.model,
            "stream": True,
            "messages": [{"role": "system", "content": system}, *messages],
        }
        client = self._client or httpx.Client(timeout=config.REQUEST_TIMEOUT)
        try:
            with client.stream("POST", f"{self.url}/api/chat", json=payload) as r:
                if r.status_code == 404:
                    raise ProviderError(
                        f"Model '{self.model}' is not installed. Run: ollama pull {self.model}"
                    )
                if r.status_code != 200:
                    r.read()
                    raise ProviderError(f"Ollama error {r.status_code}: {r.text[:200]}")
                for line in r.iter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    chunk = data.get("message", {}).get("content", "")
                    if chunk:
                        yield chunk
                    if data.get("done"):
                        break
        except httpx.ConnectError:
            raise ProviderError(
                "Can't reach Ollama. Make sure it is installed and running (open the Ollama app)."
            ) from None
        except httpx.TimeoutException:
            raise ProviderError("Ollama took too long to answer. Try a smaller model.") from None