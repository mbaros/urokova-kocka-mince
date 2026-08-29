# Changelog

## [2026-08-29] Prompt #6 — úvodní návod

### Added
- Šestistránkový úvodní tutoriál při první návštěvě — mluví kočka v první osobě („Ahoj Terez, já jsem Mince“), s kočkou nakreslenou na každé stránce; oslovení dcery je v nastavení (`kidName`). Obsah: video + levely, úrok z úroku s čísly pro den 33/66/100, kočka a easter eggy, nabídky na dnech 33/66, start). Dokončení/přeskočení se ukládá (`state.tutorialDone`, event `tutorial`). V rodičovském nastavení tlačítko „Pustit úvodní návod znovu“.

### Changed
- `closeSheet()` maže obsah sheetu (dřív zůstával skrytý v DOM).

---

## [2026-08-29] Prompt #5 — proklikání a opravy

### Fixed
- Velké stupně kočky (lvice) měly uříznutou korunku: pravidlo `.cat *{transform-box:fill-box}` měnilo počátek transformace kořenové skupiny SVG → výjimka pro `.root`.
- Po kliknutí na „Otevři ho na YouTube“ zmizel nouzový blok (re-render schoval `#ytFallback` a časovač se znovu nenastavil) → `ytFailed` flag + re-arm timeoutu při každém načtení.
- Prázdný odznak titulu se zobrazoval jako pomlčka (`display:inline-block` přebíjel `hidden`) → globální `[hidden]{display:none!important}`.
- Osa Y grafu skákala na 20k při maximu 10k → jemnější „hezké“ kroky.
- Odkazy měly výchozí modrou → zlatá dle palety; kratší popisky polí v nastavení; mrknutí/spánek s brýlemi nemačká brýle do čáry.

---

## [2026-08-29] Prompt #4

### Added
- Dva levely check-inu: **Základní** (video od 2:30 do konce) a **Pokročilý** (celé video). Přepínač na kartě check-inu, volba se pamatuje na serveru (`state.level`), level se zapisuje do eventu `checkin`. Začátek základního levelu je v rodičovském nastavení (`basicStart`, m:ss).
- Video a přepínač levelu jsou vidět i během odpočtu před startem (jen náhled, vklad se nepočítá).

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
