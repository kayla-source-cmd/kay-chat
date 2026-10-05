"""The main chat loop: keeps history, calls the model, streams the reply."""
from typing import Iterator

from app import config
from app.core.prompts import SYSTEM_PROMPT
from app.providers.base import BaseProvider


class ChatEngine:
    def __init__(self, provider: BaseProvider, system_prompt: str = SYSTEM_PROMPT,
                 max_messages: int | None = None):
        self.provider = provider
        self.system_prompt = system_prompt
        self.max_messages = max_messages or config.MAX_HISTORY_MESSAGES
        self.history: list[dict] = []

    def reply(self, user_text: str) -> Iterator[str]:
        """Send a message and yield the answer chunk by chunk."""
        self.history.append({"role": "user", "content": user_text})
        parts: list[str] = []
        try:
            for chunk in self.provider.stream(self._window(), self.system_prompt):
                parts.append(chunk)
                yield chunk
        finally:
            if parts:
                self.history.append({"role": "assistant", "content": "".join(parts)})
            else:  # nothing came back, so forget the unanswered message
                self.history.pop()

    def reset(self) -> None:
        self.history.clear()

    def _window(self) -> list[dict]:
        """Only the most recent messages, always starting with a user message."""
        recent = self.history[-self.max_messages:]
        while recent and recent[0]["role"] != "user":
            recent = recent[1:]
        return recent