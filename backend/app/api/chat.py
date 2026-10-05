"""The chat URL: receives a message and streams the reply back."""
import json
import logging
import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.chat_engine import ChatEngine
from app.providers import get_provider
from app.providers.base import ProviderError

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])

# Temporary: chats live in memory and disappear when the server restarts.
# A later phase replaces this with the database.
_engines: dict[str, ChatEngine] = {}


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    conversation_id: str | None = None


def _sse(event: dict) -> str:
    """Format one event for the browser (Server-Sent Events)."""
    return f"data: {json.dumps(event)}\n\n"


@router.post("/chat")
def chat(req: ChatRequest):
    conversation_id = req.conversation_id or uuid.uuid4().hex

    def event_stream():
        yield _sse({"type": "meta", "conversation_id": conversation_id})
        try:
            engine = _engines.get(conversation_id)
            if engine is None:
                engine = ChatEngine(get_provider())
                _engines[conversation_id] = engine
            for chunk in engine.reply(req.message):
                yield _sse({"type": "token", "text": chunk})
        except ProviderError as e:
            yield _sse({"type": "error", "message": str(e)})
        except Exception:
            log.exception("Unexpected error while chatting")
            yield _sse({"type": "error", "message": "Something went wrong on the server."})
        yield _sse({"type": "done"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.delete("/chat/{conversation_id}")
def reset_chat(conversation_id: str):
    _engines.pop(conversation_id, None)
    return {"status": "cleared"}