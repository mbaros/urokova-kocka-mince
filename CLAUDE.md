# urokova-kocka-mince

Úroková kočka — 100denní výzva pro dceru: každý den dokoukané priming video = vklad 16 Kč + 3 % denní úrok, rostoucí kočka, graf, nabídky na výběr na dni 33 a 66. Cílem je *zažít* složené úročení, ne o něm číst.

> **Best practices**: viz `.agentic/CLAUDE.md`. Tady jsou jen projekt-specifické věci.

---

## Project context

- **Stack**: single-file frontend (`app/index.html`, vanilla JS, žádný build) + FastAPI backend (`server/main.py`) na Python 3.12; Docker (`deploy/`)
- **Server**: martin1 (`martin1.box.yarabot.io`), vhost sdílený s ostatními projekty přes Caddy v containeru `qa-tracker-caddy`
- **Project dir**: `/home/bobek/projects/urokova-kocka-mince`
- **App port**: 8000 uvnitř containeru `kocka` (síť `jarabot-metrics_default`); zvenku jen přes Caddy
- **Test command**: `bin/e2e-smoke` (musí být zelené před každým commitem) — API contract + `node --check` + Playwright (mobile Chromium)
- **Data**: `data/state.json` + `data/events.jsonl` (bind mount `./data:/data`, v gitu ignorováno)

## Klíčové soubory

| Soubor | Účel |
|---|---|
| `app/eggs.js` | 100 easter eggů + pohybová primitiva |
| `app/index.html` | celá aplikace: styly, UI, logika úročení, kočka (SVG + easter eggy), YouTube embed, sync se serverem |
| `server/main.py` | `GET/PUT /api/state`, `GET /api/events`, `GET /api/health`, statika |
| `deploy/docker-compose.yml`, `deploy/Dockerfile` | container `kocka` |
| `deploy/Caddyfile.snippet` | route s tajnou cestou + tokenem (hodnoty jen na serveru) |
| `deploy/deploy.sh` | `git pull` + rebuild + healthcheck |
| `bin/e2e-smoke` | povinný e2e runner |
| `tests/e2e/smoke.spec.js` | Playwright scénáře (seedují server přes `PUT /api/state`) |
| `docs/ARCHITECTURE.md` | aktuální architektura |
| `docs/DECISIONS.md` | log rozhodnutí (matematika, token v URL, …) |
| `docs/PROMPTS.md` | log promptů |
| `docs/CHANGELOG.md` | změny per session |

## Setup (lokálně)

```bash
python3 -m venv .venv && .venv/bin/pip install -r server/requirements.txt   # bin/e2e-smoke použije .venv, když existuje
cd tests && npm install && npx playwright install chromium && cd ..
git config core.hooksPath .githooks     # pre-push spustí bin/e2e-smoke; červené testy = push se nepustí
```

## Spuštění

```bash
DATA_DIR=./data uvicorn server.main:app --reload --port 8765   # http://127.0.0.1:8765
bin/e2e-smoke                                                  # spustí si vlastní server na 8765
```

## „Zeptej se Mince“ (ask worker na hostu)

Odpovědi generuje Claude Code přes Max předplatné, mimo container:

```bash
# jednorázově na martin1 jako bobek:
claude setup-token                      # vytvoří dlouhodobý token (sk-ant-oat-…) — přihlášení v prohlížeči
echo 'CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat-…' >> ~/projects/urokova-kocka-mince/.env   # gitignored
mkdir -p ~/.config/systemd/user && cp deploy/kocka-ask-worker.service ~/.config/systemd/user/
systemctl --user daemon-reload && systemctl --user enable --now kocka-ask-worker
sudo loginctl enable-linger bobek
journalctl --user -u kocka-ask-worker -f
```

Bez běžícího workeru UI hlásí „Mince spí“ (heartbeat starší než 2 min); otázky se zařadí do fronty a zodpoví později (inbox). Lekce, kvízy i FAQ fungují dál.

**Druhý odpovídač na Macu (kde je Claude Code přihlášený):** `scripts/ask-worker.py` v režimu `ASK_REMOTE=martin1:/home/bobek/projects/urokova-kocka-mince/data/ask` pracuje s frontou přes ssh. Launchd agent `deploy/com.jarabot.kocka-ask-worker.plist` (`launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/…`), log `~/Library/Logs/kocka-ask-worker.log`. Oba workery mohou běžet zároveň; heartbeat píše jen ten, kterému Claude Code odpovídá.

## Video

Nejspolehlivější je vlastní kopie: `ssh martin1 ~/projects/urokova-kocka-mince/deploy/fetch-video.sh <youtube-url>` → `data/video/priming.mp4`. Aplikace ji použije automaticky (health `video`), YouTube je jen záloha. YouTube embed vyžaduje Referer — route v Caddy proto přepisuje `Referrer-Policy`.

## Deploy

```bash
ssh martin1 ~/projects/urokova-kocka-mince/deploy/deploy.sh
```

## Project-specific gotchas

- **Tajná URL + token nikdy do gitu.** Caddy vrací 404 na cokoli bez správného `?k=`; hodnoty jsou jen v `/home/bobek/jarabot-metrics/Caddyfile` a v poznámce u Martina.
- **Klient volá API relativně** (`api/state` + `location.search`), aby prošel prefix `/k/<secret>/` i token. Nikdy nepiš absolutní `/api/...`.
- **Server je zdroj pravdy.** Při startu se stav načte z `GET /api/state` a přepíše localStorage. Testy proto seedují server, ne localStorage.
- **Vklad se zaokrouhluje nahoru** na celé Kč (`Math.ceil`), takže cíl je ≈ 10 008 Kč, nikdy méně než 10 000.
- **Úrok se připisuje jen ve dnech s check-inem.** Vynechaný den výzvu prodlužuje, rozpočet nikdy nepřekročí.
- **`data-testid` jsou kontrakt s testy**: `checkin-done`, `sheet-next`, `offer-take`, `offer-keep`, `offer-take-confirm`, `parent-gear`, `pinbox`, `settings-save`, `settings-sim-day`, `tab-*`, `balance`, `cat`, `whatif-range`.
- Kočka má idle animaci → Playwright klik `{ force: true }`.
- Google Fonts a YouTube jsou externí; testy je blokují (`page.route`), e2e nesmí na síti záviset.
- Playwright bez staženého Chromia: `PW_CHROMIUM_PATH=/cesta/k/chrome bin/e2e-smoke`.
- Výchozí PIN rodiče je `1234` — změnit v nastavení hned po nasazení.
- `bin/e2e-smoke` startuje server s `ASK_MOCK=1`; chat v testech dostává zkušební odpověď, worker není potřeba. `PUT /api/ask/mock {asleep:true}` (jen v mock režimu) simuluje spícího odpovídače.
- **Před každým nasazením**: `bin/e2e-smoke` zelené (hlídá i pre-push hook) + ruční proklik změněné obrazovky v prohlížeči (Playwright na Macu proti produkční URL, `tests/prod-check.cjs` vzor v historii).
- **Copy pro Terezku**: o otci vždy „taťka“, nikdy „táta“ (i v persona promptu odpovídače).
- Lekce v `app/lessons.js` jsou číslované 1–100 a testy počítají s konkrétními tituly (1 „Co jsou vlastně peníze“, 7 „Kam mizí drobné“, kvíz 5 odpověď C).

## Interní cesty / endpointy

| | |
|---|---|
| Produkce | `https://martin1.box.yarabot.io/k/<SECRET_PATH>/?k=<TOKEN>` (viz poznámka Martina) |
| Health | `…/k/<SECRET_PATH>/api/health?k=<TOKEN>` |
| Data na serveru | `/home/bobek/projects/urokova-kocka-mince/data/` |
| Caddy reload | `docker exec qa-tracker-caddy caddy reload --config /etc/caddy/Caddyfile` |

<!-- BEGIN .agentic managed block — do not edit -->
## Best practices

Read **`.agentic/CLAUDE.md`** before starting any task. It defines:
- Documentation discipline (`docs/ARCHITECTURE.md`, `DECISIONS.md`, `PROMPTS.md`, `CHANGELOG.md`)
- TDD + e2e workflow (mandatory before declaring done)
- HTML literal escape traps + JS regression detection
- Secret management, runtime isolation, event sourcing
- Git discipline + auto-commit policy

Project-specific notes are above this line. The `.agentic/` rules apply to ALL tasks.
<!-- END .agentic managed block -->
