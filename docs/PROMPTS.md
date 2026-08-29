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
