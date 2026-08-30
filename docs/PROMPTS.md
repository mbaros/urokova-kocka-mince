# Prompt Log

## Prompt #1 — 2026-08-29 07:30

**User prompt (hlasová diktace, zkráceno):**
> Chci web appku pro dceru (15), která jí ukáže sílu úroků. Rozpočet 10 000 Kč. Každý den si pustí priming video (URL dodám) a odklikne to; za každý den dostane vklad, jehož výši mám spočítat, plus denní úrok (třeba 20 %), který se nabaluje. Graf, jak to roste. 100 dní. Každých ~33 dní speciální obrazovka: může si peníze vzít hned (i s úroky), ale přijde o další úroky z vybrané částky — má být vidět, co ji to stojí. Fun věci, milníky, něco jako kočka, co sílí. Nejdřív živý artefakt, pak aplikace.

**Plan:** vyjasnit úrok/jazyk/úložiště/společníka → spočítat vklad → postavit artefakt (Dnes / Graf / Kočka / Milníky, nabídky, rodičovské nastavení s PINem).

**Summary of what was done:** Artefakt „Úroková kočka“ (3 %/den, 16 Kč/den, česky, localStorage, kočka s výbavou).

---

## Prompt #2 — 2026-08-29 08:00

**User prompt:**
> tady je repo pro tento projekt https://github.com/mbaros/urokova-kocka-mince.git — použij pravidla pro tvorbu aplikací i z tohoto repo https://github.com/xgroot-dev/best-practices-agentic-coding.git a ulož toto do repository a aplikaci nasaď na martin1 na speciální url, která je dlouhá a neuhodnutelná a zároveň se otevře jen s tokenem v url

**Plan:** přečíst `.agentic` pravidla → strukturovat repo (app/, server/, deploy/, tests/, docs/, bin/e2e-smoke) → `data-testid` + Playwright → Caddy route s tajnou cestou a tokenem → deploy na martin1 → ověřit.

---

## Prompt #3 — 2026-08-29 08:10

**User prompt:**
> ať se na konci každého úspěšného přehrání YT videa zobrazí obrazovka jako konfety a „toto je tvůj XY. den, gratuluji“ a pak případně další obrazovka „DNES JSI KOČIČKU VYLEPŠILA O XY“. Rozmysli odměny, ať je tam odměna každé 2–5 dní. Něco, co nebude vidět, ale když na kočku klikneš, tak se otočí nebo přitulí — skryté easter eggy, které se vyvíjejí v čase, jak kočka sílí a roste; každý den jeden. Kočka se může měnit na větší zvířátko: větší kočka, mini puma, malá lvice, velká lvice — může být jen easter egg. Jeden den na ni může kápnout a ona se otřepe. Veškerý progress ukládej přímo na serveru do speciálního adresáře, kde aplikace poběží. Výzva začne od pondělí 31. 8., do té doby odpočet „začíná za XY hodin a minut“, ale půjde klikat a koukat.

**Plan:** YouTube IFrame API + `ENDED` → 3 oslavné obrazovky → 30 odměn (2–5 dní) → 6 stupňů kočky → 20 easter eggů gated podle stupně + tajný 5. klik → FastAPI backend se `state.json` + `events.jsonl` → odpočet do 31. 8. → testy → docs → commit → deploy.

**Summary of what was done:**
Kompletní přepis `app/index.html` (server sync, YouTube embed, oslava, odměny, kočka 6 stupňů, 20 easter eggů, odpočet), nový `server/main.py`, Docker + Caddy snippet, `bin/e2e-smoke` (12 kontrol, 9 Playwright scénářů), dokumentace. Nasazeno na martin1 pod tajnou URL s tokenem.

**Files changed:**
- `app/index.html`, `server/main.py`, `server/requirements.txt`
- `deploy/Dockerfile`, `deploy/docker-compose.yml`, `deploy/Caddyfile.snippet`, `deploy/deploy.sh`
- `bin/e2e-smoke`, `tests/package.json`, `tests/playwright.config.js`, `tests/e2e/smoke.spec.js`
- `CLAUDE.md`, `README.md`, `.gitignore`, `docs/*`

**Tests added/modified:**
- API contract (health, 404 na prázdném store, PUT/GET shape, events.jsonl, 422)
- Playwright: načtení bez JS chyb + sync, odpočet před startem, easter egg kliknutím, první check-in (3 obrazovky + server persist), 100 dní ≈ 10 008 Kč, nabídka den 33 (kept/taken), taby + graf + odměny, rodičovský PIN + přepočet vkladu

---

## Prompt #4 — 2026-08-29 09:00

**User prompt:**
> to video je tohle [odkaz nedorazil] — ještě přidej level základní / pokročilý; pokročilý bude celé video, základní bude video od 2:30 do konce

**Plan:** přepínač levelu na kartě check-inu → YouTube `start` param / `&t=` u odkazu → uložit volbu do stavu a do eventu → nastavení začátku v rodičovské sekci → test → deploy.

**Summary of what was done:** Hotovo dle plánu; URL videa je třeba doplnit v rodičovském nastavení (v promptu nebyl odkaz).

**Files changed:** `app/index.html`, `tests/e2e/smoke.spec.js`, `docs/*`

**Tests added/modified:** level toggle scénář

---

## Prompt #7 — 2026-08-29 09:40

**User prompt:**
> Když budou ty milníky, kde můžu vybrat peníze, nadesignuj více info, např. FAQ „Co se stane, když teď vyberu / nevyberu“ — ať je to co nejlepší pro finanční gramotnost. Každý den dej 1 lekci z finanční gramotnosti, nenuceně jako myšlenku kočky po primingu. Ať na sebe navazují, občas kvíz a možnost se na něco zeptat; když se zeptá, použij lokální model (paušál Max), vygeneruj odpověď a navrhuj navazující dotazy dynamicky. Celé to nadesignuj jako hru, nakresli v Claude Design, pak implementuj.

**Plan:** design canvas (5 obrazovek) → 100 lekcí + 20 kvízů → Škola, hvězdičky, tituly → chat přes `/api/ask` + host worker (Claude Code, Max) → FAQ u nabídek → testy → docs → deploy.

**Summary of what was done:** Vše výše; worker vyžaduje jednorázové `claude setup-token` na martin1 (token OAuth expiroval).

**Files changed:** `app/index.html`, `app/lessons.js`, `server/main.py`, `scripts/ask-worker.py`, `deploy/kocka-ask-worker.service`, `bin/e2e-smoke`, `tests/e2e/smoke.spec.js`, `CLAUDE.md`, `docs/*`

**Tests added/modified:** API ask mock + 422; Playwright: lekce v oslavě, kvíz den 5, Škola + chat, FAQ nabídky

---

## 2026-08-29 — Prompt #16

**User prompt:**
> Udělej na serveru martin1 jednu obdobnou kopii, ta bude pro mě (Pro Marťase), na jiné adrese; začal jsem včera a mám 2 splněné. Budeme provozovat dvě instance, dvě různé URL a tokeny. Informace o instancích zapiš do repozitáře do speciálního adresáře, ať se můžu snadno vracet k opravám.

**Plan:** compose s kotvou → 2 containery, sdílené video `:ro` → worker s víc frontami → `docs/instances/` → e2e → deploy → na serveru `data-martas/state.json` (start 28. 8., 2 check-iny), nová route v Caddy, `URL.txt` → ověřit obě instance.

**Summary of what was done:** Vše výše (viz CHANGELOG #16).

**Files changed:** `deploy/docker-compose.yml`, `deploy/deploy.sh`, `deploy/Caddyfile.snippet`, `deploy/kocka-ask-worker.service`, `deploy/com.jarabot.kocka-ask-worker.plist`, `server/main.py`, `scripts/ask-worker.py`, `.gitignore`, `docs/instances/*`, `docs/ARCHITECTURE.md`, `docs/CHANGELOG.md`, `CLAUDE.md`

**Tests added/modified:** beze změny (infrastruktura); `bin/e2e-smoke` zelené

---

## 2026-08-30 — Prompt #17

**User prompt:**
> (screenshot oslavy s „Nový zůstatek 51 Kč“) Navrhni design a implementuj — ať je tady někde vidět i původní zůstatek, např. starý zůstatek → nový zůstatek.

**Plan:** řádek bylo → nový zůstatek + pilulka s rozdílem v Kč a % → totéž na kartě Dnes hotovo → test → deploy.

**Summary of what was done:** Vše výše (CHANGELOG #17).

**Files changed:** `app/index.html`, `tests/e2e/smoke.spec.js`, `docs/*`

**Tests added/modified:** +1 Playwright scénář, rozšířen test prvního check-inu

---

## 2026-08-30 — Prompt #18

**User prompt:**
> Ať jsou ty věty srozumitelnější — např. „Patří do rodiny“ → chtěl bych „Mince už patří do rodiny“ nebo tak něco hezkého. Zreviduj všechny texty, promysli to a oprav to.

**Plan:** projít REWARDS + SURPRISES + krátké nadpisy → celé věty se jménem kočky přes `rtext()` → ověřit čísla v textech proti matematice → test → deploy.

**Summary of what was done:** Viz CHANGELOG #18.

**Files changed:** `app/index.html`, `tests/e2e/smoke.spec.js`, `docs/*`

**Tests added/modified:** rozšířen scénář dne 3, upraven scénář 100 dní

---

## 2026-08-30 — Prompt #19

**User prompt:**
> Tenhle text (lekce 3) je taky nesrozumitelný — místo „většina lidí utratí a spoří, co zbyde“ má být: většina lidí spoří to, co během měsíce neutratí, to nefunguje; správně je na začátku měsíce rozdělit peníze na ty, co utratím za co chci, na nutné věci, a na spoření (investice nebo odložené třeba na dárek).

**Plan:** přepsat lekci 3 v hlasu kočky podle zadání → navázat lekci 9 → projít ostatní lekce a rozepsat telegrafické úvody kvízů → test → deploy.

**Summary of what was done:** Viz CHANGELOG #19.

**Files changed:** `app/lessons.js`, `tests/e2e/smoke.spec.js`, `docs/*`

---
