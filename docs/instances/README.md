# Provozované instance

Jedna image (`urokova-kocka:latest`), **jeden container + jeden datový adresář + jedna Caddy route na instanci**. Všechny běží na martin1 v `/home/bobek/projects/urokova-kocka-mince`.

| Instance | Pro koho | Container | Data na hostu | Caddy route → | Soubor |
|---|---|---|---|---|---|
| `terezka` | Terezka (dcera) | `kocka` | `data/` | `kocka:8000` | [terezka.md](terezka.md) |
| `martas` | Marťas (taťka) | `kocka-martas` | `data-martas/` | `kocka-martas:8000` | [martas.md](martas.md) |

**Tajné hodnoty (secret path, token) nejsou v gitu.** Každá instance má svůj `URL.txt` v datovém adresáři na serveru (`cat ~/projects/urokova-kocka-mince/data-<inst>/URL.txt`, u terezky `data/URL.txt`) a route v `/home/bobek/jarabot-metrics/Caddyfile` (blok `handle /k/<SECRET>/*` s komentářem `# kocka: <instance>`).

## Společné věci

- Video `data/video/priming.mp4` sdílí obě instance (mount `:ro` v compose).
- `deploy/deploy.sh` nasadí obě naráz (pull → build → `up -d` → health obou containerů). Data přežijí (bind mounty).
- Odpovídač („Zeptej se Mince“) obsluhuje fronty všech instancí: na martin1 `ASK_DIRS=data/ask,data-martas/ask` (systemd unit), na Macu `ASK_REMOTE=martin1:…/data/ask,martin1:…/data-martas/ask` (launchd plist). Heartbeat se píše do každé fronty.

## Jak přidat další instanci `<inst>`

1. `deploy/docker-compose.yml`: zkopíruj službu `kocka-martas` → `kocka-<inst>` (`container_name`, volume `../data-<inst>:/data`).
2. `deploy/deploy.sh`: přidej container do `mkdir -p` a do health smyčky.
3. Worker: přidej `data-<inst>/ask` do `ASK_DIRS` (service) a `ASK_REMOTE` (plist); restartuj oba.
4. Na serveru: `mkdir -p data-<inst>`, nasaď (`deploy.sh`), vygeneruj `openssl rand -hex 20` (path) a `openssl rand -hex 24` (token), vlož blok z `deploy/Caddyfile.snippet` s `reverse_proxy kocka-<inst>:8000`, `caddy reload`, zapiš `data-<inst>/URL.txt`.
5. Nastav stav: buď projdi tutoriál v aplikaci, nebo zapiš `data-<inst>/state.json` (viz `docs/ARCHITECTURE.md` → Stav) a restartuj container (server čte soubor při každém GET, restart není nutný).
6. Založ `docs/instances/<inst>.md` a přidej řádek do tabulky výše.

## Běžné opravy

| Co | Jak |
|---|---|
| Stav instance | `curl -s "https://martin1.box.yarabot.io/k/<SECRET>/api/state?k=<TOKEN>"` nebo `cat data-<inst>/state.json` |
| Logy aplikace | `docker logs --tail 100 kocka-<inst>` |
| Eventy | `tail data-<inst>/events.jsonl` |
| Reset (od začátku) | zálohuj `state.json`+`events.jsonl` do `data-<inst>/archive-<datum>/`, smaž je; app při dalším načtení založí čistý stav (tutoriál znovu) |
| Fronta otázek | `ls data-<inst>/ask/` (`req-*.json`, `answers.jsonl`, `heartbeat`) |
| Nová URL/token | uprav blok v Caddyfile, `docker exec qa-tracker-caddy caddy reload --config /etc/caddy/Caddyfile`, přepiš `URL.txt` |
