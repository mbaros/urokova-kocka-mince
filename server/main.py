"""Úroková kočka — tiny backend.

Serves the single-page app from ../app and keeps the challenge progress on the
server in DATA_DIR (default ./data):

  data/state.json    current state (atomic write: tmp + rename)
  data/events.jsonl  append-only log of every check-in / offer / withdrawal / settings change

Access control is NOT done here: Caddy in front of the container only forwards
requests that carry the secret path + ?k=<token> (see deploy/Caddyfile.snippet).
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import secrets
import tempfile
import time
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

# "Zeptej se Mince" — file-based IPC with a host-side worker that runs Claude Code
# (Max subscription). The container never holds the token: it writes ask/req-*.json,
# the worker (scripts/ask-worker.py) answers into ask/res-*.json.
VIDEO_DIR = DATA_DIR / "video"          # self-hosted copy of the priming video (deploy/fetch-video.sh)
VIDEO_FILE = "priming.mp4"
ASK_DIR = DATA_DIR / "ask"
ASK_LOG = ASK_DIR / "log.jsonl"
ASK_HEARTBEAT = ASK_DIR / "worker.heartbeat"
ASK_MOCK = os.environ.get("ASK_MOCK", "") == "1"
ASK_DAILY_LIMIT = int(os.environ.get("ASK_DAILY_LIMIT", "25"))
ASK_TIMEOUT_S = int(os.environ.get("ASK_TIMEOUT_S", "90"))

app = FastAPI(title="Úroková kočka", docs_url=None, redoc_url=None)


class Event(BaseModel):
    type: str = Field(min_length=1, max_length=64)
    payload: dict[str, Any] = Field(default_factory=dict)


class StatePut(BaseModel):
    state: dict[str, Any]
    events: list[Event] = Field(default_factory=list)


class AskTurn(BaseModel):
    q: str = Field(max_length=400)
    a: str = Field(max_length=2000)


class AskBody(BaseModel):
    question: str = Field(min_length=1, max_length=400)
    lessonN: int | None = None
    lessonTitle: str | None = Field(default=None, max_length=120)
    lessonText: str | None = Field(default=None, max_length=1200)
    history: list[AskTurn] = Field(default_factory=list, max_length=6)
    kid: str = Field(default="Terez", max_length=40)
    cat: str = Field(default="Mince", max_length=40)


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
    video = (VIDEO_DIR / VIDEO_FILE)
    return {"ok": True, "hasState": STATE_FILE.exists(), "time": _now(),
            "video": f"media/{VIDEO_FILE}" if video.exists() and video.stat().st_size > 0 else None}


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


def _asks_today() -> int:
    if not ASK_LOG.exists():
        return 0
    today = datetime.now().strftime("%Y-%m-%d")
    n = 0
    for line in ASK_LOG.read_text(encoding="utf-8").splitlines():
        if line.startswith('{"at": "' + today):
            n += 1
    return n


def _worker_alive() -> bool:
    try:
        return time.time() - ASK_HEARTBEAT.stat().st_mtime < 120
    except OSError:
        return False


@app.get("/api/ask/status")
def ask_status() -> dict[str, Any]:
    return {"alive": ASK_MOCK or _worker_alive(), "askedToday": _asks_today(), "limit": ASK_DAILY_LIMIT, "mock": ASK_MOCK}


@app.post("/api/ask")
async def ask(body: AskBody) -> dict[str, Any]:
    ASK_DIR.mkdir(parents=True, exist_ok=True)
    used = _asks_today()
    if used >= ASK_DAILY_LIMIT:
        raise HTTPException(status_code=429, detail=f"Dnes už jsi se zeptala {used}×. Zítra zase.")
    req_id = f"{int(time.time())}-{secrets.token_hex(4)}"
    started = _now()
    if ASK_MOCK:
        result = {
            "answer": f"(zkušební odpověď) Ptáš se: „{body.question}“. Krátká verze: čas násobí víc než částka.",
            "followups": ["A co inflace?", "Kde seženu vyšší úrok?", "Jak to spočítám?"],
        }
    else:
        if not _worker_alive():
            raise HTTPException(status_code=503, detail="Mince zrovna spí (odpovídač neběží). Zkus to za chvíli.")
        req = {"id": req_id, "at": started, **body.model_dump()}
        _write_atomic(ASK_DIR / f"req-{req_id}.json", json.dumps(req, ensure_ascii=False))
        res_path = ASK_DIR / f"res-{req_id}.json"
        deadline = time.time() + ASK_TIMEOUT_S
        result = None
        while time.time() < deadline:
            if res_path.exists():
                try:
                    result = json.loads(res_path.read_text(encoding="utf-8"))
                    break
                except (OSError, json.JSONDecodeError):
                    await asyncio.sleep(0.3)
                    continue
            await asyncio.sleep(0.5)
        for p in (ASK_DIR / f"req-{req_id}.json", res_path):
            try:
                p.unlink()
            except OSError:
                pass
        if result is None:
            raise HTTPException(status_code=504, detail="Mince přemýšlí moc dlouho. Zkus to ještě jednou.")
        if result.get("error"):
            raise HTTPException(status_code=502, detail=f"Mince se zamotala: {result['error']}")
    answer = str(result.get("answer", "")).strip()[:2000]
    followups = [str(f).strip()[:120] for f in (result.get("followups") or []) if str(f).strip()][:3]
    if not answer:
        raise HTTPException(status_code=502, detail="Mince neodpověděla.")
    try:
        with ASK_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"at": started, "id": req_id, "lessonN": body.lessonN, "q": body.question, "a": answer, "followups": followups}, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return {"answer": answer, "followups": followups, "askedToday": used + 1, "limit": ASK_DAILY_LIMIT}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(APP_DIR / "index.html", headers={"Cache-Control": "no-cache"})


VIDEO_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=VIDEO_DIR), name="media")   # Range requests → seeking works
app.mount("/", StaticFiles(directory=APP_DIR, html=True), name="static")
