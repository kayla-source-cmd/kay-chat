"""Creates the web server and connects everything."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.api import chat

app = FastAPI(title="Kay-Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "provider": config.PROVIDER}