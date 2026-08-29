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
ASK_ANSWERS = ASK_DIR / "answers.jsonl"      # answers to questions asked while the worker slept
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


_mock_asleep = False


class MockBody(BaseModel):
    asleep: bool = False


@app.put("/api/ask/mock")
def ask_mock(body: MockBody) -> dict[str, Any]:
    """Test-only (ASK_MOCK=1): pretend the worker is asleep."""
    global _mock_asleep
    if not ASK_MOCK:
        raise HTTPException(status_code=404)
    _mock_asleep = body.asleep
    if not _mock_asleep:
        for req_path in sorted(ASK_DIR.glob("req-*.json")):
            try:
                req = json.loads(req_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            _write_atomic(ASK_DIR / req_path.name.replace("req-", "res-", 1), json.dumps(_mock_answer(req["question"]), ensure_ascii=False))
        _collect_queued()
    return {"asleep": _mock_asleep}


def _alive() -> bool:
    return (ASK_MOCK and not _mock_asleep) or (not ASK_MOCK and _worker_alive())


@app.get("/api/ask/status")
def ask_status() -> dict[str, Any]:
    return {"alive": _alive(), "askedToday": _asks_today(), "limit": ASK_DAILY_LIMIT, "mock": ASK_MOCK}


def _mock_answer(question: str) -> dict[str, Any]:
    return {
        "answer": f"(zkušební odpověď) Ptáš se: „{question}“. Krátká verze: čas násobí víc než částka.",
        "followups": ["A co inflace?", "Kde seženu vyšší úrok?", "Jak to spočítám?"],
    }


def _log_ask(started: str, req_id: str, lesson_n: int | None, q: str, answer: str, followups: list[str]) -> None:
    try:
        with ASK_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"at": started, "id": req_id, "lessonN": lesson_n, "q": q, "a": answer, "followups": followups}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _collect_queued() -> None:
    """Move answered *queued* requests (asked while asleep) into answers.jsonl."""
    for res_path in sorted(ASK_DIR.glob("res-*.json")):
        req_path = ASK_DIR / res_path.name.replace("res-", "req-", 1)
        try:
            req = json.loads(req_path.read_text(encoding="utf-8")) if req_path.exists() else None
            if not req or not req.get("queued"):
                continue
            res = json.loads(res_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        answer = str(res.get("answer", "")).strip()[:2000]
        followups = [str(f).strip()[:120] for f in (res.get("followups") or []) if str(f).strip()][:3]
        if answer and not res.get("error"):
            entry = {"id": req["id"], "askedAt": req["at"], "answeredAt": _now(), "lessonN": req.get("lessonN"), "q": req["question"], "a": answer, "followups": followups}
            with ASK_ANSWERS.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        for p in (req_path, res_path):
            try:
                p.unlink()
            except OSError:
                pass


@app.get("/api/ask/inbox")
def ask_inbox(limit: int = 30) -> dict[str, Any]:
    """Answers to questions asked while Mince slept, oldest first; plus how many still wait."""
    ASK_DIR.mkdir(parents=True, exist_ok=True)
    _collect_queued()
    answers = []
    if ASK_ANSWERS.exists():
        for line in ASK_ANSWERS.read_text(encoding="utf-8").splitlines()[-limit:]:
            try:
                answers.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    waiting = sum(1 for p in ASK_DIR.glob("req-*.json") if not (ASK_DIR / p.name.replace("req-", "res-", 1)).exists())
    return {"answers": answers, "waiting": waiting}


@app.post("/api/ask")
async def ask(body: AskBody) -> dict[str, Any]:
    ASK_DIR.mkdir(parents=True, exist_ok=True)
    used = _asks_today()
    if used >= ASK_DAILY_LIMIT:
        raise HTTPException(status_code=429, detail=f"Dnes už jsi se zeptala {used}×. Zítra zase.")
    req_id = f"{int(time.time())}-{secrets.token_hex(4)}"
    started = _now()
    if not _alive():
        # Mince sleeps: keep the question, the worker answers later, the app picks it up from /api/ask/inbox.
        req = {"id": req_id, "at": started, "queued": True, **body.model_dump()}
        _write_atomic(ASK_DIR / f"req-{req_id}.json", json.dumps(req, ensure_ascii=False))
        _log_ask(started, req_id, body.lessonN, body.question, "", [])
        return JSONResponse({"queued": True, "id": req_id, "askedToday": used + 1, "limit": ASK_DAILY_LIMIT}, status_code=202)
    if ASK_MOCK:
        result = _mock_answer(body.question)
    else:
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
    _log_ask(started, req_id, body.lessonN, body.question, answer, followups)
    return {"answer": answer, "followups": followups, "askedToday": used + 1, "limit": ASK_DAILY_LIMIT}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(APP_DIR / "index.html", headers={"Cache-Control": "no-cache"})


VIDEO_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=VIDEO_DIR), name="media")   # Range requests → seeking works
app.mount("/", StaticFiles(directory=APP_DIR, html=True), name="static")
