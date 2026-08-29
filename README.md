# Úroková kočka 🐾

100denní výzva pro dceru: každý den, kdy dokouká priming video, dostane vklad **16 Kč** a k celému zůstatku se připíše **3 % úrok**. Po 100 dnech je zůstatek ≈ **10 008 Kč** — z toho 1 600 Kč vklady a 8 400 Kč úroky. Na dni 33 a 66 přijde nabídka vzít si peníze hned (a přijít o budoucí úroky). Kočka mezitím roste z kotěte na lvici, sbírá odměny každých pár dní a každý den umí jiný trik, když se na ni klepne.

- `app/` — celá aplikace v jednom HTML souboru
- `server/` — malý FastAPI backend, který drží průběh na serveru
- `deploy/` — Docker + Caddy route s tajnou URL a tokenem
- `tests/` + `bin/e2e-smoke` — Playwright e2e a API testy
- `docs/` — architektura, rozhodnutí, prompty, changelog

Vývoj, spuštění a nasazení: viz [CLAUDE.md](CLAUDE.md).
