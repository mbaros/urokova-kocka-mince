# Changelog

## [2026-08-30] Prompt #20 — listování mezi lekcemi

### Added
- V otevřené lekci jsou karty „Včera · 2“ / „Dnes · 3“ (obecně „Myšlenka · N“) tlačítka: klepnutí vymění lekci přímo v panelu (krátké posunutí do strany), funguje i přejetí prstem doleva/doprava. Zítřejší lekce zůstává zamčená „🔒 až po videu“, před první je „Začátek“, za stou „konec školy“. Každá takto navštívená lekce se počítá jako přečtená (+1 ⭐). Platí v oslavě po videu i ve Škole.

### Tests
- +1 scénář: den 3 → včera → myšlenka 1 (bez „předchozí“) → zpět; zamčené zítra; `school.read = [1,2,3]`. Celkem 25 Playwright + 8 API.

---

## [2026-08-30] Prompt #19 — lekce 3 a úvody kvízů

### Changed
- Lekce 3 „Zaplať nejdřív sobě“ přepsána podle taťky: spořit z toho, co zbyde, nefunguje; na začátku měsíce rozdělit peníze na tři hromádky (nutné · chci · odložit — spoření/investice nebo třeba dárek během roku); kočka je ta třetí hromádka. Lekce 9 „Tři sklenice“ na ni navazuje (přidává sklenici DÁT).
- 20 úvodů ke kvízům z telegrafických „Sedmdesát dní. Kvíz.“ na celé věty, které říkají, z čeho kvíz je a proč zrovna dnes.

### Tests
- Den 3 kontroluje i text lekce („rozdělíš na tři hromádky“).

---

## [2026-08-30] Prompt #18 — srozumitelnější texty odměn

### Changed
- Všech 30 popisů odměn přepsáno do celých vět s jménem kočky (`{cat}` → `settings.catName`), např. „Tři dny v kuse! Mince dostává obojek — už patří do rodiny.“ Věty u nabídek (33, 66) rovnou říkají, že dnes přijde nabídka na výběr.
- Opravená čísla: den 82 dělá úrok ~170 Kč (bylo „přes 200“), překvapení „posledních 25 dní přinese víc než prvních 75“ (20/80 neplatilo). Popisy už netvrdí vývoj kočky ve špatný den.
- Zpráva o vývoji kočky má správný tvar („Z kotěte je odteď kočka“, `STAGES[].gen`), „Zítra zase, ať kočka roste dál.“, „Hotovo — sto dní!“, „A je to — sto dní ze sta. Dokázala jsi to.“

### Tests
- Den 3 kontroluje text odměny se jménem kočky; test 100 dní upraven na nový nadpis.

---

## [2026-08-30] Prompt #17 — starý zůstatek → nový zůstatek

### Changed
- Oslava po videu: místo samotného „Nový zůstatek“ je řádek **bylo (přeškrtnuto) → nový zůstatek** (šipka jemně pulzuje, nový zůstatek dál nabíhá) a pod ním pilulka `+17,48 Kč · o 52 % víc než včera` (první den „první koruny na účtu“). Stejný řádek `33 Kč → 51 Kč` zůstává i na kartě „Dnes hotovo“.

### Tests
- +1 scénář (den 3: 33 → 51 Kč, +17,48 Kč, 52 %, řádek na kartě Dnes hotovo); den 1 kontroluje 0 Kč → 16 Kč. Celkem 24 Playwright + 8 API.

---

## [2026-08-29] Prompt #16 — druhá instance „martas“

### Added
- Více instancí z jedné image: `docker-compose.yml` s YAML kotvou, containery `kocka` (terezka, `data/`) a `kocka-martas` (martas, `data-martas/`), video sdílené `:ro` přes `VIDEO_DIR`. `deploy.sh` nasazuje a kontroluje obě.
- Odpovídač obsluhuje víc front: `ASK_DIRS` (lokálně) i `ASK_REMOTE` (ssh) berou čárkou oddělený seznam; service i plist aktualizované.
- `docs/instances/` — přehled instancí, kde jsou data, route, URL.txt, jak přidat další, běžné opravy. Tajné hodnoty zůstávají jen na serveru.
- Instance `martas` pro taťku: start 28. 8. 2026, dva hotové dny, vlastní tajná cesta + token.

---

## [2026-08-29] Prompt #15

### Added
- Terezka si může před startem sama posunout začátek výzvy („Chceš začít jindy?“ pod odpočtem, jen dnešek nebo pozdější den; event `start-changed`). Návod to na poslední straně říká.

---

## [2026-08-29] Prompt #14

### Changed
- Návod, strana 2: kočičí tip — večer nabít sluchátka a dát je k telefonu, ať jde video poslouchat kdekoli.

---

## [2026-08-29] Prompt #13 — otázky i když Mince spí

### Added
- Odpovídač: tolerantní čtení JSON z modelu (české uvozovky, kódové ploty), „taťka“ vynuceno i v odpovědích.
- Odpovídač umí běžet i na Macu (`ASK_REMOTE`, ssh na frontu na martin1) — tam je Claude Code přihlášený Max plánem; launchd agent `deploy/com.jarabot.kocka-ask-worker.plist`. Claude běží v prázdném adresáři, ať netahá cizí CLAUDE.md do kontextu.
- Když odpovídač neběží, otázka se přesto odešle (`202 queued`, `data/ask/req-*.json` s `queued:true`); worker ji zodpoví, až bude přihlášený, server ji sebere do `data/ask/answers.jsonl` a aplikace ji ukáže: odznak „Mince ti odpověděla · N nové odpovědi“ ve Škole, odpovědi nahoře v chatu s navazujícími otázkami (`GET /api/ask/inbox`, `state.school.seenAnswers`).
- Název dnešní myšlenky v hlavičce chatu je tlačítko — otevře lekci.

---

## [2026-08-29] Prompt #12

### Changed
- V textech pro Terezku „taťka“ místo „táta“ (aplikace, lekce, FAQ nabídky, persona odpovídače).

### Fixed
- Chat se spící Mincí: navrhované otázky šly klepnout, ale nic se nedělo → při spánku se schovají, vstup se zamkne, klepnutí řekne proč; 503 z API se ukáže jako spánek.

### Tests
- +8 scénářů: spící odpovídač (test-only `PUT /api/ask/mock`), tutoriál skip/zpět/znovu + oslovení, špatný PIN, nastavení (testovací den, undo, jméno, PIN, reset zachová nastavení), zrušení výběru, odměny + výbava na dni 10, easter egg podle dne (31 = otočka, 9 = kapka), znovuotevřená lekce ze Školy. Celkem 23 Playwright + 8 API kontrol. Pre-push hook `.githooks/pre-push` blokuje push při červených testech.
- Rychlé klepání na telefonu přibližovalo stránku (double-tap zoom) → `touch-action: manipulation` + `maximum-scale=1`.

---

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
