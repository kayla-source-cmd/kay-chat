from app import config
from app.providers.base import BaseProvider, ProviderError
from app.providers.gemini_provider import GeminiProvider
from app.providers.ollama_provider import OllamaProvider


def get_provider(name: str | None = None) -> BaseProvider:
    """Return the provider chosen in .env (or by name)."""
    name = (name or config.PROVIDER).lower()
    if name == "ollama":
        return OllamaProvider()
    if name == "gemini":
        return GeminiProvider()
    raise ProviderError(f"Unknown PROVIDER '{name}'. Use 'ollama' or 'gemini' in backend/.env")