"""The common interface every model provider follows."""
from abc import ABC, abstractmethod
from typing import Iterator


class ProviderError(Exception):
    """Raised with a friendly message when a model provider fails."""


class BaseProvider(ABC):
    name = "base"

    @abstractmethod
    def stream(self, messages: list[dict], system: str) -> Iterator[str]:
        """Yield the reply in small text chunks.

        messages look like: [{"role": "user" | "assistant", "content": "..."}]
        """