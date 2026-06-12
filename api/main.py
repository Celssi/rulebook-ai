"""FastAPI application for rulebook-ai."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import brambletrek, chat, deck, games, index, session, warhammer_40k

app = FastAPI(title="rulebook-ai", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games.router)
app.include_router(session.router)
app.include_router(chat.router)
app.include_router(brambletrek.router)
app.include_router(deck.router)
app.include_router(index.router)
app.include_router(warhammer_40k.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
