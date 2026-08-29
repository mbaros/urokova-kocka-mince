# Changelog

## [2026-08-29] Prompt #11 — video na iPhonu

### Fixed
- Stažené video bylo AV1 (yt-dlp formát 398) — iPhone ho neumí přehrát, `ended` nikdy nepřišlo. Překódováno na H.264 720p (133 MB); `fetch-video.sh` teď vybírá avc1 a jinak překóduje. Na iOS se posun na 2:30 dělá i při play.
- Dokoukání v nácviku (před startem) dá konfety a vysvětlující kartu místo ticha.

---

## [2026-08-29] Prompt #10 — písmo s českou diakritikou

### Fixed
- Easter egg se vybíral podle kalendářního dne od startu, ne podle dne výzvy — testovací dny ho neměnily. Teď: den N výzvy (N-tý check-in) = trik N.

### Changed
- Display písmo Fredoka nemá ě/č/ř (padalo do náhradního fontu, „Kotě-žák“ vypadalo slepeně) → **Baloo 2** (stejně hravé, kompletní latin-ext). Nunito zůstává pro text.

---

## [2026-08-29] Prompt #9 — 100 easter eggů

### Added
- `app/eggs.js`: 55 pohybových primitiv (`MOTIONS`) + dráhy propů a **100 pojmenovaných easter eggů**, jeden na každý den výzvy (den 1 mrknutí … den 100 „Sto dní. Děkuju, Terez.“), řazené podle vývoje kočky (lví triky až od dne 81). Interpret `runEgg` v `index.html` (pohyby, částice, letící emoji, návazné pohyby, otřes). Když dcera vynechá dny a kočka na trik ještě nemá stupeň, vybere se jiný z povolených.

---

## [2026-08-29] Prompt #8 — video bez YouTube

### Fixed
- YouTube embed končil chybou 153 (chybí Referer): vhost má `Referrer-Policy no-referrer`; route aplikace teď posílá `strict-origin-when-cross-origin` (jen origin, nikdy tajná cesta ani token).

### Added
- **Vlastní kopie videa**: `deploy/fetch-video.sh <url>` stáhne přes yt-dlp do `data/video/priming.mp4`; server ji servíruje jako `media/priming.mp4` (Range → posouvání funguje) a hlásí ji v `/api/health.video`. Aplikace ji upřednostní před YouTube: HTML5 `<video>`, `ended` = check-in, základní level skočí na 2:30.

---

## [2026-08-29] Prompt #7 — Mincina škola

### Added
- **100 navazujících myšlenek o penězích** (`app/lessons.js`), 10 kapitol po 10 dnech, hlas kočky; kvíz každý 5. den (3 možnosti + vysvětlení). Myšlenka n se odemkne n-tým check-inem a je 4. obrazovkou oslavy.
- **Záložka Škola**: titul podle hvězdiček (přečtení +1, správný kvíz +2, otázka +1), kapitoly jako mapa, znovuotevření starších myšlenek.
- **„Zeptej se Mince“**: chat s navrhovanými otázkami, odpověď + 3 dynamické navazující otázky. `POST /api/ask` → souborová IPC (`data/ask/req-*.json`) → host worker `scripts/ask-worker.py` (Claude Code v print módu, Max předplatné) → `res-*.json`. Denní limit 25, heartbeat (`/api/ask/status`), mock režim `ASK_MOCK=1` pro testy. Systemd user unit `deploy/kocka-ask-worker.service`.
- **FAQ u nabídek výběru** (den 33/66): „Co se stane, když teď vyberu / nevyberu“, proč je rozdíl tak velký, reálný svět, kdy je správné vybrat — s konkrétními čísly; tlačítko „Mám jinou otázku“ otevře chat s kontextem nabídky.
- Flush rozpracovaného uložení přes `sendBeacon` při zavření karty.

### Tests
- API: `/api/ask` mock tvar + 422; Playwright: 4. obrazovka oslavy, kvíz den 5, Škola + chat (mock), FAQ nabídky — 14/14 zelené

---

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
