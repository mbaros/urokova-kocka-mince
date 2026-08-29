#!/usr/bin/env python3
"""Host-side answerer for „Zeptej se Mince“.

Runs OUTSIDE the container (as bobek on martin1), watches data/ask/ for
req-*.json written by server/main.py, asks Claude Code in print mode and writes
res-*.json. Claude Code uses the Max subscription: put a long-lived token from
`claude setup-token` into <project>/.env as CLAUDE_CODE_OAUTH_TOKEN (gitignored),
or just be logged in (`claude` → /login) as the user running this worker.

    python3 scripts/ask-worker.py            # loop forever
    python3 scripts/ask-worker.py --once     # handle pending requests and exit

Install as a user service: see deploy/kocka-ask-worker.service.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASK_DIR = Path(os.environ.get("ASK_DIR", ROOT / "data" / "ask"))
# Remote mode: the ask dir lives on another machine (e.g. run this on a laptop where Claude Code
# is logged in, against martin1): ASK_REMOTE="martin1:/home/bobek/projects/urokova-kocka-mince/data/ask"
ASK_REMOTE = os.environ.get("ASK_REMOTE", "")
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]
MODEL = os.environ.get("ASK_MODEL", "sonnet")
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")
TIMEOUT_S = int(os.environ.get("ASK_CLAUDE_TIMEOUT_S", "75"))
WORKDIR = os.environ.get("ASK_WORKDIR", tempfile.mkdtemp(prefix="kocka-ask-"))   # empty cwd: no project CLAUDE.md in context

SYSTEM = """Jsi Mince — kočka z aplikace „Úroková kočka“, která učí patnáctiletou dívku finanční gramotnost.
Mluvíš česky, v první osobě jako kočka (hravě, vřele, bez poučování), tykáš, oslovuješ ji jménem {kid}.
Držíš se faktů o penězích, spoření, úrocích, rozpočtu, dluzích, investování a podvodech. Čísla uváděj v Kč, na příkladech.
Odpověď: nejvýš ~110 slov, srozumitelně pro patnáctiletou, jedna hlavní myšlenka, klidně jedna kočičí věta.
Nedoporučuj konkrétní produkty, firmy ani „kup tohle“; obecné principy ano. U rizikových věcí (krypto, půjčky) řekni riziko na rovinu.
Nikdy neříkej, že jsi AI nebo model — jsi kočka Mince. Když otázka nesouvisí s penězi, odpověz krátce a laskavě a vrať se k penězům.
O jejím otci mluv jako o „taťkovi“ (ne „táta“). Kontext výzvy: každý den dokoukané priming video = vklad 16 Kč a 3 % denní úrok ke všemu; po 100 dnech ≈ 10 008 Kč (1 600 Kč vklady, zbytek úroky); nabídky výběru na dnech 33 a 66.
VRAŤ POUZE JSON bez komentáře a bez ``` ve tvaru: {{"answer": "...", "followups": ["otázka 1", "otázka 2", "otázka 3"]}}
Uvnitř textu nikdy nepoužívej rovné uvozovky " (rozbily by JSON) — piš „takhle“ nebo bez uvozovek.
followups = tři krátké navazující otázky (max 8 slov), které by ji mohly zajímat a posouvají ji dál."""


def load_env() -> None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))


def build_prompt(req: dict) -> str:
    parts = []
    if req.get("lessonTitle"):
        parts.append(f"Dnešní myšlenka dne č. {req.get('lessonN')}: „{req['lessonTitle']}“ — {req.get('lessonText') or ''}")
    for turn in req.get("history") or []:
        parts.append(f"{req.get('kid', 'Terez')}: {turn['q']}\nMince: {turn['a']}")
    parts.append(f"{req.get('kid', 'Terez')} se ptá: {req['question']}")
    return "\n\n".join(parts)


def extract_json(text: str) -> dict | None:
    """The model is asked for JSON, but Czech quotes inside strings break it now and then — be forgiving."""
    text = text.strip().strip("`")
    text = re.sub(r"^json\s*", "", text)
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    ans = re.search(r'"answer"\s*:\s*"(.*?)"\s*(?:,\s*"followups"|\})', text, re.S)
    if not ans:
        return None
    fol = re.search(r'"followups"\s*:\s*\[(.*?)\]', text, re.S)
    followups = re.findall(r'"([^"\n]{3,120})"', fol.group(1)) if fol else []
    return {"answer": ans.group(1).replace('\\"', '"').replace("\\n", "\n"), "followups": followups}


def house_style(text: str) -> str:
    """Word-level fixes the family asked for: „taťka“, never „táta“."""
    for a, b in (("táta", "taťka"), ("táty", "taťky"), ("tátovi", "taťkovi"), ("tátu", "taťku"), ("tátou", "taťkou"), ("Táta", "Taťka"), ("Táty", "Taťky")):
        text = re.sub(rf"\b{a}\b", b, text)
    return text


def answer(req: dict) -> dict:
    system = SYSTEM.format(kid=req.get("kid", "Terez"))
    cmd = [CLAUDE_BIN, "-p", build_prompt(req), "--model", MODEL, "--output-format", "json",
           "--max-turns", "1", "--append-system-prompt", system]
    try:
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_S, stdin=subprocess.DEVNULL, cwd=WORKDIR)
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    if run.returncode != 0 and not run.stdout.strip():
        return {"error": (run.stderr or "claude failed").strip()[:300]}
    try:
        outer = json.loads(run.stdout)
    except json.JSONDecodeError:
        outer = {"result": run.stdout}
    if outer.get("is_error"):
        return {"error": str(outer.get("result", "error"))[:300]}
    text = str(outer.get("result", ""))
    data = extract_json(text)
    if not data or not data.get("answer"):
        return {"answer": house_style(text.strip()[:2000]), "followups": []}
    return {"answer": house_style(str(data["answer"])), "followups": [house_style(str(f)) for f in (data.get("followups") or [])][:3]}


def _remote() -> tuple[str, str]:
    host, _, path = ASK_REMOTE.partition(":")
    return host, path


def remote_heartbeat() -> None:
    host, path = _remote()
    subprocess.run(SSH + [host, f"touch '{path}/worker.heartbeat'"], capture_output=True, timeout=20)


def remote_pending() -> list[str]:
    """Names of req-*.json on the remote without a matching res-*.json."""
    host, path = _remote()
    run = subprocess.run(SSH + [host, f"cd '{path}' 2>/dev/null && ls req-*.json res-*.json 2>/dev/null"], capture_output=True, text=True, timeout=20)
    names = set(run.stdout.split())
    return sorted(n for n in names if n.startswith("req-") and n.replace("req-", "res-", 1) not in names)


def handle_remote() -> int:
    host, path = _remote()
    n = 0
    for name in remote_pending():
        run = subprocess.run(SSH + [host, f"cat '{path}/{name}'"], capture_output=True, text=True, timeout=20)
        try:
            req = json.loads(run.stdout)
        except json.JSONDecodeError:
            continue
        result = answer(req)
        res_name = name.replace("req-", "res-", 1)
        payload = json.dumps(result, ensure_ascii=False)
        subprocess.run(SSH + [host, f"cat > '{path}/{res_name}.tmp' && mv '{path}/{res_name}.tmp' '{path}/{res_name}'"],
                       input=payload, capture_output=True, text=True, timeout=20)
        n += 1
        print(f"[ask-worker] {req.get('id', name)}: {'error ' + result['error'] if result.get('error') else 'ok'} (remote)", flush=True)
    return n


def handle_pending() -> int:
    if ASK_REMOTE:
        return handle_remote()
    n = 0
    for req_path in sorted(ASK_DIR.glob("req-*.json")):
        res_path = ASK_DIR / req_path.name.replace("req-", "res-", 1)
        if res_path.exists():
            continue
        try:
            req = json.loads(req_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not req.get("queued") and time.time() - req_path.stat().st_mtime > 300:  # stale live request — the server gave up
            req_path.unlink(missing_ok=True)
            continue
        result = answer(req)
        tmp = res_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, res_path)
        n += 1
        print(f"[ask-worker] {req['id']}: {'error ' + result['error'] if result.get('error') else 'ok'}", flush=True)
    return n


_probe_ok = False
_probe_at = 0.0


def probe() -> bool:
    """Is Claude Code actually able to answer (token valid)? Cached for 10 minutes.
    The heartbeat is only written while this is true, so the app shows „Mince spí“
    instead of failing on every question when the login expired."""
    global _probe_ok, _probe_at
    if time.time() - _probe_at < 600:
        return _probe_ok
    _probe_at = time.time()
    try:
        run = subprocess.run([CLAUDE_BIN, "-p", "Odpověz jedním slovem: ok", "--model", MODEL, "--output-format", "json", "--max-turns", "1"],
                             capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL, cwd=WORKDIR)
        data = json.loads(run.stdout) if run.stdout.strip() else {}
        _probe_ok = bool(run.stdout.strip()) and not data.get("is_error")
        if not _probe_ok:
            print(f"[ask-worker] probe failed: {str(data.get('result') or run.stderr)[:200]} — run `claude setup-token` and put CLAUDE_CODE_OAUTH_TOKEN into .env", flush=True)
    except Exception as exc:  # noqa: BLE001
        _probe_ok = False
        print(f"[ask-worker] probe error: {exc}", flush=True)
    return _probe_ok


def main() -> None:
    load_env()
    once = "--once" in sys.argv
    if ASK_REMOTE:
        print(f"[ask-worker] remote mode → {ASK_REMOTE} (model {MODEL})", flush=True)
    else:
        ASK_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[ask-worker] watching {ASK_DIR} (model {MODEL})", flush=True)
    while True:
        try:
            if probe():
                if ASK_REMOTE:
                    remote_heartbeat()
                else:
                    (ASK_DIR / "worker.heartbeat").touch()
                handle_pending()
        except Exception as exc:  # noqa: BLE001 — keep the loop alive (ssh hiccups etc.)
            print(f"[ask-worker] loop error: {exc}", flush=True)
        if once:
            return
        time.sleep(15.0 if ASK_REMOTE else 1.0)


if __name__ == "__main__":
    main()
