"""Úroková kočka — tiny backend.

Serves the single-page app from ../app and keeps the challenge progress on the
server in DATA_DIR (default ./data):

  data/state.json    current state (atomic write: tmp + rename)
  data/events.jsonl  append-only log of every check-in / offer / withdrawal / settings change

Access control is NOT done here: Caddy in front of the container only forwards
requests that carry the secret path + ?k=<token> (see deploy/Caddyfile.snippet).
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = Path(os.environ.get("APP_DIR", BASE_DIR / "app"))
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))
STATE_FILE = DATA_DIR / "state.json"
EVENTS_FILE = DATA_DIR / "events.jsonl"
MAX_STATE_BYTES = 512 * 1024

app = FastAPI(title="Úroková kočka", docs_url=None, redoc_url=None)


class Event(BaseModel):
    type: str = Field(min_length=1, max_length=64)
    payload: dict[str, Any] = Field(default_factory=dict)


class StatePut(BaseModel):
    state: dict[str, Any]
    events: list[Event] = Field(default_factory=list)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=path.suffix)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        finally:
            raise


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True, "hasState": STATE_FILE.exists(), "time": _now()}


@app.get("/api/state")
def get_state() -> JSONResponse:
    if not STATE_FILE.exists():
        raise HTTPException(status_code=404, detail="Zatím žádný uložený stav.")
    try:
        doc = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail=f"Stav nejde přečíst: {exc}") from exc
    return JSONResponse(doc, headers={"Cache-Control": "no-store"})


@app.put("/api/state")
def put_state(body: StatePut) -> dict[str, Any]:
    doc = {"state": body.state, "updatedAt": _now()}
    text = json.dumps(doc, ensure_ascii=False)
    if len(text.encode("utf-8")) > MAX_STATE_BYTES:
        raise HTTPException(status_code=413, detail="Stav je příliš velký.")
    try:
        _write_atomic(STATE_FILE, text)
        if body.events:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with EVENTS_FILE.open("a", encoding="utf-8") as fh:
                for ev in body.events:
                    fh.write(json.dumps({"at": doc["updatedAt"], "type": ev.type, **ev.payload}, ensure_ascii=False) + "\n")
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Stav nejde uložit: {exc}") from exc
    return {"ok": True, "updatedAt": doc["updatedAt"]}


@app.get("/api/events")
def get_events(limit: int = 200) -> dict[str, Any]:
    if not EVENTS_FILE.exists():
        return {"events": []}
    lines = EVENTS_FILE.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines[-max(1, min(limit, 5000)):]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return {"events": out}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(APP_DIR / "index.html", headers={"Cache-Control": "no-cache"})


app.mount("/", StaticFiles(directory=APP_DIR, html=True), name="static")
