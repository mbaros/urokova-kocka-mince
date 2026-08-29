# Decision Log

## Decision #1: 3 % denně a vklad odvozený z cílové částky

**Date:** 2026-08-29

**Context:** Martin chtěl rozpočet 10 000 Kč na 100 dní a „nějaký úrok, třeba 20 %“. Při 20 % denně by vklad vyšel na 0,0001 Kč — dcera by neviděla vlastní vklady vůbec.

**Decision:** 3 % denně, vklad se dopočítá tak, aby 100 check-inů skončilo na cílové částce: 16 Kč/den → ≈ 10 008 Kč (1 600 vklady, 8 400 úroky). Vklad se zaokrouhluje nahoru na celé koruny, cíl se tedy nikdy nepodstřelí.

**Alternatives considered:** 2 % (32 Kč/den, mírnější křivka), 5 % (3,80 Kč/den, vklady působí jako drobné), 20 % (nesmysl).

**Rationale:** Při 3 % zůstatek mezi fází 1 a 3 zhruba zčtyřnásobí — nabídka výběru na dni 33 (908 Kč vs. ztráta 5 669 Kč) skutečně bolí, a přitom je 1 600 Kč vlastních vkladů dost na to, aby je dcera cítila jako své.

---

## Decision #2: Úrok jen ve dnech s check-inem

**Date:** 2026-08-29

**Context:** Kdyby úrok běžel kalendářně, vynechané dny by ho stejně přinesly a při delším trvání by rozpočet přetekl.

**Decision:** Řetězec `balance = (balance + vklad) × 1,03` se počítá jen za check-in. Vynechaný den výzvu prodlužuje.

**Rationale:** Deterministický konec (100 check-inů = 10 008 Kč), motivace chodit denně, rozpočet nikdy nepřekročí.

---

## Decision #3: Průběh na serveru, ne jen v prohlížeči

**Date:** 2026-08-29

**Context:** Původní artefakt ukládal do localStorage (jeden telefon). Martin chce průběh na serveru v adresáři aplikace a vidět ho taky.

**Decision:** Malý FastAPI backend, `state.json` (atomický zápis tmp+rename) + append-only `events.jsonl`. Server je zdroj pravdy; localStorage zůstává jako offline cache a záloha.

**Alternatives considered:** čistě statický hosting + zálohový kód (křehké při změně telefonu); Claude artifact s `artifact` capability (vyžaduje účet pro dceru).

**Rationale:** Bez účtů, jedna URL pro oba, event log umožňuje replay/audit (princip #6).

---

## Decision #4: Tajná cesta + token v URL (vědomá odchylka od principu #4)

**Date:** 2026-08-29

**Context:** `.agentic/principles/04-secrets-and-vault.md` říká „nikdy token přes URL query“. Martin ale výslovně chce, aby se aplikace otevřela jen s tokenem v URL, bez přihlašování (dcera si uloží záložku).

**Decision:** Caddy: `handle /k/<SECRET_PATH>/*` + matcher `query k=<TOKEN>`; cokoli jiného → 404. Hodnoty žijí jen v serverovém Caddyfile a v Martinově poznámce, repo má pouze placeholdery. Klient posílá token dál relativními URL, takže i API je za tokenem.

**Alternatives considered:** oauth2-proxy jako u mbtasks (dcera by potřebovala GitHub/Google účet); basic auth (nepříjemné na mobilu, prohlížeče ho různě cachují); token → cookie redirect (elegantnější, ale token stejně musí být v první URL).

**Rationale:** Chráněná data jsou 100 řádků check-inů jedné rodiny; hrozba je „někdo uhádne URL“, ne cílený útok. Dvě 192bitová tajemství to řeší. Tokeny se v Caddy nelogují (access log není zapnutý). Pokud by unikly, stačí vyměnit dva řetězce v Caddyfile.

---

## Decision #5: Konec videa detekuje YouTube IFrame API, nouzové tlačítko jako fallback

**Date:** 2026-08-29

**Context:** Původně (artefakt) šlo video otevřít jen v nové kartě a check-in odemknout časovačem. Martin chce oslavu „po úspěšném přehrání“.

**Decision:** Na vlastní doméně se video vloží přes IFrame API, `onStateChange === ENDED` spouští check-in. Když embed selže (video bez povoleného embedu, API se nenačte), zobrazí se odkaz na YouTube a časovač odemkne nouzové tlačítko po `minMinutes`.

**Rationale:** Skutečné „dokoukala“ je silnější rituál než „odklikla“, ale nesmí to být cesta, jak se zaseknout.

---

## Decision #6: Odměny každé 2–5 dní a easter eggy podle dne

**Date:** 2026-08-29

**Decision:** 30 odměn na dnech 1, 3, 5, 8, 10, 13, … 97, 100 (max. rozestup 5) ve čtyřech typech (výbava / hračka / kulisa / titul). Vývoj kotě→lvice není odměna, jen se děje (easter egg). Denní easter egg je deterministický z data, ne z náhody, aby se při refreshi neměnil; každý 5. klik má tajný efekt.

---

## Decision #7: „Zeptej se Mince“ přes Claude Code na hostu (souborová IPC), ne přes API klíč

**Date:** 2026-08-29

**Context:** Martin chce odpovědi generovat „lokálním modelem na paušál Max“ — tedy bez placení za API tokeny, přes Claude Code přihlášené jeho Max předplatným. Container aplikace nemá (a nemá mít) přístup k jeho přihlášení.

**Decision:** Container jen zapisuje požadavky do `data/ask/` a čeká na odpověď (max 90 s). Na hostu běží `scripts/ask-worker.py` jako systemd user service, volá `claude -p … --output-format json --max-turns 1 --append-system-prompt <persona Mince>` a odpověď (JSON `{answer, followups[3]}`) zapíše zpět. Heartbeat soubor říká UI, jestli je Mince „vzhůru“. Denní limit 25 dotazů.

**Alternatives considered:** Anthropic API klíč v containeru (platí se za tokeny, jiná fakturace než chtěl); Claude CLI uvnitř containeru s namountovaným `~/.claude` (token by musel být zapisovatelný pro refresh, porušuje izolaci); Agent SDK (stejný problém s auth).

**Rationale:** Přesně pattern z `.agentic/principles/05` a lucas-ai (brain/hands, IPC přes adresář, atomické zápisy). Token zůstává v `.env`/přihlášení hosta, nikdy v gitu ani v containeru. Vyžaduje jednorázově `claude setup-token` (Max) na martin1 — viz README/CLAUDE.md.

---

## Decision #8: Lekce jako statická data v repu, ne generované

**Date:** 2026-08-29

**Decision:** 100 myšlenek je ručně napsaný, navazující curriculum (`app/lessons.js`), ne generované za běhu. Model se používá jen na otázky navíc.

**Rationale:** Konzistence, návaznost kapitol na nabídky (den 31–33, 65–66), žádná náhoda v tom, co dcera uvidí, nulová cena a žádná závislost na tom, že worker běží.
