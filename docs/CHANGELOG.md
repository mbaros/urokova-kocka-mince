# Changelog

## [2026-08-29] Prompt #4

### Added
- Dva levely check-inu: **Základní** (video od 2:30 do konce) a **Pokročilý** (celé video). Přepínač na kartě check-inu, volba se pamatuje na serveru (`state.level`), level se zapisuje do eventu `checkin`. Začátek základního levelu je v rodičovském nastavení (`basicStart`, m:ss).

### Tests
- Playwright: přepínač levelu + persist na server + zamčené nouzové tlačítko (10 scénářů, 12/12 zelené)

---

## [2026-08-29] Prompt #2 + #3

### Added
- Repo struktura podle `.agentic` (app/, server/, deploy/, tests/, docs/, bin/e2e-smoke)
- FastAPI backend: `GET/PUT /api/state`, `GET /api/events`, `GET /api/health`; stav v `data/state.json`, eventy v `data/events.jsonl`
- YouTube embed s detekcí konce videa → automatický check-in; nouzové tlačítko po `minMinutes`
- Oslava check-inu: konfety + „Tohle je tvůj N. den“ → „Dnes jsi kočičku vylepšila o …“ → nová odměna
- 30 odměn každé 2–5 dní (výbava, hračky, kulisy, tituly)
- Kočka v 6 stupních (kotě → kočka → velká kočka → mini puma → malá lvice → lvice)
- 20 easter eggů po kliknutí na kočku, jeden na den, odemykané podle stupně; každý 5. klik tajný
- Odpočet do startu 31. 8. 2026; před startem nejde check-in, ostatní ano
- Docker (`kocka`, non-root, read-only), Caddy route s tajnou cestou + `?k=` tokenem, `deploy/deploy.sh`

### Changed
- Vklad se zaokrouhluje nahoru (`ceil`), nabídky na `round(N/3)` a `2·round(N/3)`
- Y osa grafu na „hezkých“ krocích

### Tests
- `bin/e2e-smoke`: 12 kontrol (server, API contract, JS syntax, Playwright 9 scénářů) — zelené

---
