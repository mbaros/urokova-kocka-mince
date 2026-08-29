// @ts-check
const { test, expect } = require('@playwright/test');

const STORAGE_KEY = 'urokova-kocka-v1';

const STARTED = { startDate: '2020-01-01' }; // a challenge that is already running

/** State with `n` consecutive daily check-ins ending today. */
function stateWith(n, settings = {}, extra = {}, endDaysAgo = 0) {
  const checkins = [];
  const z = (k) => String(k).padStart(2, '0');
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i - endDaysAgo);
    checkins.push({ date: `${d.getFullYear()}-${z(d.getMonth() + 1)}-${z(d.getDate())}` });
  }
  return { checkins, settings: { ...STARTED, ...settings }, tutorialDone: true, ...extra };
}

/** The page loads whatever the server holds, so tests seed the server, not localStorage. */
async function seed(page, state) {
  const r = await page.request.put('/api/state', { data: { state, events: [] } });
  if (!r.ok()) throw new Error('seed failed: ' + r.status());
  await page.evaluate((k) => localStorage.removeItem(k), STORAGE_KEY);
}

function collectErrors(page) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  page.on('console', (m) => {
    const t = m.text();
    // Google Fonts may be unreachable in CI; that is not an app error.
    if (m.type() === 'error' && !t.includes('favicon') && !t.includes('fonts.g') && !t.includes('ERR_')) errors.push(t);
  });
  return errors;
}

test.describe('Úroková kočka smoke', () => {
  test.beforeEach(async ({ page }) => {
    // Fonts come from Google; the suite must not depend on that network being reachable.
    await page.route(/fonts\.(googleapis|gstatic)\.com|youtube\.com|ytimg\.com/, (r) => r.abort());
    await page.goto('/');
    await seed(page, stateWith(0));
  });

  test('page loads with no JS errors and shows day 0', async ({ page }) => {
    const errors = collectErrors(page);
    await page.goto('/');
    await expect(page).toHaveTitle(/Úroková kočka/);
    await expect(page.getByTestId('balance')).toHaveText('0');
    await expect(page.getByText('Den 0 ze 100')).toBeVisible();
    await expect(page.locator('#sync')).toHaveText(/načteno ze serveru/);
    expect(errors, `JS errors: ${errors.join(' | ')}`).toEqual([]);
  });

  test('before the start date a countdown is shown and no check-in is possible', async ({ page }) => {
    await seed(page, { settings: { startDate: '2099-01-01' }, tutorialDone: true });
    await page.goto('/');
    await expect(page.getByText('Výzva začíná')).toBeVisible();
    await expect(page.locator('#cd')).toContainText('hodin');
    await expect(page.getByTestId('checkin-done')).toHaveCount(0);
  });

  test('first visit shows the tutorial; finishing it is remembered on the server', async ({ page }) => {
    await seed(page, { settings: STARTED });
    await page.goto('/');
    await expect(page.getByTestId('tutorial')).toContainText('Ahoj Terez, já jsem Mince');
    for (let i = 0; i < 5; i++) await page.getByTestId('tutorial-next').click();
    await expect(page.getByTestId('tutorial')).toContainText('Začínáme');await expect(page.getByTestId('tutorial-cat').locator('svg')).toBeVisible();
    await page.getByTestId('tutorial-next').click();
    await expect(page.getByTestId('tutorial')).toHaveCount(0);
    await expect(page.locator('#sync')).toHaveText(/uloženo na serveru/);
    await page.reload();
    await page.waitForTimeout(800);
    await expect(page.getByTestId('tutorial')).toHaveCount(0);
    const saved = await (await page.request.get('/api/state')).json();
    expect(saved.state.tutorialDone).toBe(true);
  });

  test('tapping the cat plays the daily easter egg (speech bubble appears)', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('cat').locator('svg').click({ force: true }); // the idle wobble never settles
    await expect(page.locator('#bubbleToday')).toHaveClass(/on/);
  });

  test('first check-in credits 16 Kč deposit + 3 % interest and persists', async ({ page }) => {
    await page.goto('/');
    // No video URL configured → button is enabled immediately.
    await page.getByTestId('checkin-done').click();
    // 1) congratulations  2) what the cat gained  3) day-1 reward
    await expect(page.locator('#sheet')).toContainText('Tohle je tvůj 1. den');
    await page.getByTestId('sheet-next').click();
    await expect(page.locator('#sheet')).toContainText('Dnes jsi kočičku vylepšila o');
    await expect(page.locator('#sheet')).toContainText('+16 Kč');
    await page.getByTestId('sheet-next').click();
    await expect(page.locator('#sheet')).toContainText('První mince');
    await page.getByTestId('sheet-next').click();
    // 4) Mincina myšlenka č. 1
    await expect(page.getByTestId('lesson')).toContainText('Co jsou vlastně peníze');
    await page.getByTestId('sheet-next').click();
    await expect(page.getByTestId('balance')).toHaveText('16'); // 16.48 rounded
    await expect(page.getByText('Dnes hotovo')).toBeVisible();
    // Second click the same day is impossible: the button is gone.
    await expect(page.getByTestId('checkin-done')).toHaveCount(0);
    // Persisted on the server, not only in this browser.
    await expect(page.locator('#sync')).toHaveText(/uloženo na serveru/);
    await expect.poll(async () => (await (await page.request.get('/api/state')).json()).state.school.read).toEqual([1]);
    await page.evaluate((k) => localStorage.removeItem(k), STORAGE_KEY);
    await page.reload();
    await expect(page.getByTestId('balance')).toHaveText('16');
    const saved = await (await page.request.get('/api/state')).json();
    expect(saved.state.checkins).toHaveLength(1);
  });

  test('day 5 brings a quiz; a correct answer earns 2 stars and is remembered', async ({ page }) => {
    await seed(page, stateWith(4, {}, { school: { read: [1, 2, 3, 4], quiz: {}, asked: 0 } }, 1)); // last check-in yesterday
    await page.goto('/');
    await page.getByTestId('checkin-done').click();
    await page.getByTestId('sheet-next').click(); // gratulace
    await page.getByTestId('sheet-next').click(); // vylepšení
    await page.getByTestId('sheet-next').click(); // odměna (den 5 = klubíčko)
    await expect(page.getByTestId('quiz')).toBeVisible();
    await page.getByTestId('quiz').locator('[data-pick="2"]').click();
    await expect(page.locator('.why')).toContainText('Přesně!');
    await expect(page.locator('.stars .small')).toContainText('celkem 6'); // 4 read + 2 for the quiz (lesson 5 counts once closed)
    await page.getByTestId('sheet-next').click();
    await page.getByTestId('tab-school').click();
    await expect(page.locator('#schoolTiles')).toContainText('1/1');
    await expect(page.locator('#schoolHead')).toContainText('7 ⭐');
    await expect.poll(async () => (await (await page.request.get('/api/state')).json()).state.school.quiz['5']).toEqual({ pick: 2, ok: true });
  });

  test('Škola tab lists chapters, opens an earlier lesson, and the chat answers (mock)', async ({ page }) => {
    await seed(page, stateWith(12, {}, { school: { read: [1, 2, 3], quiz: {}, asked: 0 } }));
    await page.goto('/');
    await page.getByTestId('tab-school').click();
    await expect(page.getByTestId('chapter-1')).toHaveClass(/done/);
    await expect(page.getByTestId('chapter-2')).toHaveClass(/now/);
    await expect(page.getByTestId('chapter-3')).toHaveClass(/lock/);
    await page.getByTestId('chapter-1').click();
    await page.locator('[data-open="7"]').click();
    await expect(page.getByTestId('lesson')).toContainText('Kam mizí drobné');
    await page.getByTestId('lesson-ask').click();
    await expect(page.getByTestId('chat')).toBeVisible();
    await page.getByTestId('ask-input').fill('Co je inflace?');
    await page.getByTestId('ask-send').click();
    await expect(page.locator('#chatLog .msg.cat')).toContainText('zkušební odpověď');
    await expect(page.locator('#chips button')).toHaveCount(3);
    await page.locator('#chips button').first().click();
    await expect(page.locator('#chatLog .msg.me')).toHaveCount(2);
    await expect.poll(async () => (await (await page.request.get('/api/state')).json()).state.school.asked).toBe(2);
  });

  test('when the answerer sleeps, a question is kept and answered into the inbox once she wakes', async ({ page }) => {
    await page.request.put('/api/ask/mock', { data: { asleep: true } });
    try {
      await seed(page, stateWith(3));
      await page.goto('/');
      await page.getByTestId('tab-school').click();
      await page.getByTestId('ask-open').click();
      await expect(page.getByTestId('chat-asleep')).toBeVisible();
      await expect(page.getByTestId('ask-input')).toBeEnabled();
      // the lesson title in the header opens the lesson
      await expect(page.getByTestId('chat-lesson')).toContainText('Zaplať nejdřív sobě');
      await page.getByTestId('ask-input').fill('Proč mají peníze hodnotu?');
      await page.getByTestId('ask-send').click();
      await expect(page.getByTestId('queued')).toBeVisible();
      expect((await page.request.post('/api/ask', { data: { question: 'Ahoj?' } })).status()).toBe(202);
      await expect.poll(async () => (await (await page.request.get('/api/state')).json()).state.school?.asked).toBe(1);
    } finally {
      await page.request.put('/api/ask/mock', { data: { asleep: false } }); // wakes up and answers the queue
    }
    await page.locator('#sheet').getByRole('button', { name: 'Zavřít' }).click();
    await page.reload();
    await page.getByTestId('tab-school').click();
    await expect(page.getByTestId('inbox-badge')).toContainText('2 nové odpovědi');
    await page.getByTestId('ask-open').click();
    await expect(page.getByTestId('inbox-answer')).toHaveCount(2);
    await expect(page.locator('#chatLog')).toContainText('Proč mají peníze hodnotu?');
    await expect(page.locator('#chips button')).toHaveCount(3); // follow-ups of the last answer
    // seen → badge gone
    await page.locator('#sheet').getByRole('button', { name: 'Zavřít' }).click();
    await expect(page.getByTestId('inbox-badge')).toHaveCount(0);
  });

  test('the withdrawal offer explains both choices in a FAQ', async ({ page }) => {
    await seed(page, stateWith(33));
    await page.goto('/');
    const faq = page.getByTestId('offer-faq');
    await expect(faq.locator('details')).toHaveCount(5);
    await faq.locator('summary', { hasText: 'Co se stane, když nevyberu?' }).click();
    await expect(faq).toContainText(/za 67 dní z nich samotných bude/);
  });

  test('with a video set, the level toggle (základní od 2:30 / pokročilý celé) is remembered on the server', async ({ page }) => {
    await seed(page, stateWith(0, { videoUrl: 'https://youtu.be/dQw4w9WgXcQ' }));
    await page.goto('/');
    await expect(page.getByTestId('level-basic')).toHaveClass(/on/);
    await expect(page.getByTestId('level-basic')).toContainText('od 2:30 do konce');
    await page.getByTestId('level-advanced').click();
    await expect(page.getByTestId('level-advanced')).toHaveClass(/on/);
    await expect(page.locator('#sync')).toHaveText(/uloženo na serveru/);
    const saved = await (await page.request.get('/api/state')).json();
    expect(saved.state.level).toBe('advanced');
    // The emergency button is locked until the video has been playing for minMinutes.
    await expect(page.getByTestId('checkin-done')).toBeDisabled();
  });

  test('a self-hosted video (data/video/priming.mp4) is preferred over YouTube', async ({ page }) => {
    const h = await (await page.request.get('/api/health')).json();
    expect(h.video).toBe('media/priming.mp4'); // bin/e2e-smoke drops a tiny file there
    await seed(page, stateWith(0, { videoUrl: 'https://youtu.be/dQw4w9WgXcQ' }));
    await page.goto('/');
    await expect(page.getByTestId('local-video')).toHaveAttribute('src', /media\/priming\.mp4/);
    await expect(page.locator('#ytPlayer')).toHaveCount(0);
  });

  test('after 100 check-ins the balance is ≈ 10 008 Kč', async ({ page }) => {
    await seed(page, stateWith(100));
    await page.goto('/');
    await expect(page.getByTestId('balance')).toHaveText(/10\s008/);
    await expect(page.getByText('Hotovo. 100 dní.')).toBeVisible();
  });

  test('withdrawal offer appears after day 33 and keeping it logs a badge', async ({ page }) => {
    await seed(page, stateWith(33));
    await page.goto('/');
    await expect(page.getByText(/Chceš 908 Kč hned\?/)).toBeVisible();
    await page.getByTestId('offer-keep').click();
    await expect(page.locator('#sheet')).toContainText('Odolala jsi');
    await page.locator('#sheet').getByRole('button', { name: 'Jedeme dál' }).click();
    await expect(page.getByTestId('offer-keep')).toHaveCount(0);
    await page.getByTestId('tab-mile').click();
    await expect(page.getByText('Odolala nabídce')).toBeVisible();
  });

  test('taking the offer resets the balance to 0 and keeps the history', async ({ page }) => {
    await seed(page, stateWith(33));
    await page.goto('/');
    await page.getByTestId('offer-take').click();
    await page.getByTestId('offer-take-confirm').click();
    await expect(page.getByTestId('balance')).toHaveText('0');
    await expect(page.getByText('Den 33 ze 100')).toBeVisible();
  });

  test('tabs switch screens and the chart renders without errors', async ({ page }) => {
    const errors = collectErrors(page);
    await seed(page, stateWith(12));
    await page.goto('/');
    await page.getByTestId('tab-chart').click();
    await expect(page.locator('#s-chart')).toBeVisible();
    await expect(page.getByText('Jak rostou tvoje peníze')).toBeVisible();
    await page.getByTestId('whatif-range').fill('0');
    await expect(page.locator('#wiFinal')).toHaveText(/1\s600 Kč/);
    await page.getByTestId('tab-cat').click();
    await expect(page.locator('#s-cat svg')).toBeVisible();
    await page.getByTestId('tab-mile').click();
    await expect(page.locator('#mileList .mi:not(.locked)')).toHaveCount(5); // days 1,3,5,8,10
    expect(errors).toEqual([]);
  });

  test('parent settings require the PIN and recalculate the deposit', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('parent-gear').click();
    const digits = page.getByTestId('pinbox').locator('input');
    for (const [i, d] of ['1', '2', '3', '4'].entries()) await digits.nth(i).fill(d);
    await expect(page.locator('#sheet')).toContainText('Nastavení výzvy');
    await expect(page.locator('#calc')).toContainText('denní vklad 16 Kč');
    await page.locator('#fRate').fill('2');
    await expect(page.locator('#calc')).toContainText('denní vklad 32 Kč');
  });

  test('tutorial can be skipped, replayed from parent settings, and greets by the configured name', async ({ page }) => {
    await seed(page, { settings: { ...STARTED, kidName: 'Terezko', catName: 'Micka' } });
    await page.goto('/');
    await expect(page.getByTestId('tutorial')).toContainText('Ahoj Terezko, já jsem Micka');
    await page.getByTestId('tutorial-next').click();
    await page.locator('#tutBack').click();
    await expect(page.getByTestId('tutorial')).toContainText('Ahoj Terezko');
    await page.getByTestId('tutorial-skip').click();
    await expect(page.getByTestId('tutorial')).toHaveCount(0);
    await expect.poll(async () => (await (await page.request.get('/api/state')).json()).state.tutorialDone).toBe(true);
    await page.getByTestId('parent-gear').click();
    const digits = page.getByTestId('pinbox').locator('input');
    for (const [i, d] of ['1', '2', '3', '4'].entries()) await digits.nth(i).fill(d);
    await page.getByTestId('settings-tutorial').click();
    await expect(page.getByTestId('tutorial')).toContainText('Ahoj Terezko');
  });

  test('a wrong PIN is rejected; the right one opens settings', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('parent-gear').click();
    const digits = page.getByTestId('pinbox').locator('input');
    for (const [i, d] of ['9', '9', '9', '9'].entries()) await digits.nth(i).fill(d);
    await expect(page.locator('#pinErr')).toHaveText('Špatný PIN');
    await expect(page.locator('#sheet')).not.toContainText('Nastavení výzvy');
    for (const [i, d] of ['1', '2', '3', '4'].entries()) await digits.nth(i).fill(d);
    await expect(page.locator('#sheet')).toContainText('Nastavení výzvy');
  });

  test('parent settings: test day, undo, changed name/PIN persist; reset keeps settings', async ({ page }) => {
    await page.goto('/');
    const openSettings = async (pin) => {
      await page.getByTestId('parent-gear').click();
      const digits = page.getByTestId('pinbox').locator('input');
      for (const [i, d] of pin.split('').entries()) await digits.nth(i).fill(d);
      await expect(page.locator('#sheet')).toContainText('Nastavení výzvy');
    };
    await openSettings('1234');
    await page.getByTestId('settings-sim-day').click();
    await page.getByTestId('settings-sim-day').click();
    await expect(page.locator('#dayLabel')).toHaveText('Den 2 ze 100');
    await page.locator('#undoBtn').click();
    await expect(page.locator('#dayLabel')).toHaveText('Den 1 ze 100');
    await page.locator('#fCat').fill('Micka');
    await page.locator('#fPin').fill('6666');
    await page.getByTestId('settings-save').click();
    await expect(page.locator('#catName')).toHaveText('Micka');
    await expect.poll(async () => (await (await page.request.get('/api/state')).json()).state.settings.pin).toBe('6666');
    page.once('dialog', (d) => d.accept());
    await openSettings('6666');
    await page.locator('#resetBtn').click();
    await expect(page.locator('#dayLabel')).toHaveText('Den 0 ze 100');
    await expect(page.locator('#catName')).toHaveText('Micka'); // settings survive a reset
  });

  test('declining the withdrawal confirmation keeps the offer open', async ({ page }) => {
    await seed(page, stateWith(33));
    await page.goto('/');
    await page.getByTestId('offer-take').click();
    await page.locator('#sheet').getByRole('button', { name: 'Ještě ne' }).click();
    await expect(page.getByTestId('offer-take')).toBeVisible();
    await expect(page.getByTestId('balance')).toHaveText(/908/);
  });

  test('rewards unlock the cat gear and show up on the Odměny tab', async ({ page }) => {
    await seed(page, stateWith(10));
    await page.goto('/');
    await expect(page.locator('#catToday svg')).toBeVisible();
    await expect(page.locator('#catLvl')).toContainText('kočka');
    await expect(page.locator('#catTitle')).toHaveText('Nováček');
    await page.getByTestId('tab-mile').click();
    await expect(page.locator('#mileList .mi:not(.locked)')).toHaveCount(5);
    await expect(page.locator('#mileList')).toContainText('Korunka');
  });

  test('the daily easter egg follows the challenge day', async ({ page }) => {
    await seed(page, stateWith(31));
    await page.goto('/');
    await page.getByTestId('cat').locator('svg').click({ force: true });
    await expect(page.locator('#bubbleToday')).toHaveText('tadá!'); // egg 31 = flip
    await seed(page, stateWith(9));
    await page.goto('/');
    await page.getByTestId('cat').locator('svg').click({ force: true });
    await expect(page.locator('#bubbleToday')).toHaveText('Fuj! Mokro!'); // egg 9 = drop
  });

  test('a lesson reopened from Škola counts as read and its chat carries the lesson context', async ({ page }) => {
    await seed(page, stateWith(3));
    await page.goto('/');
    await page.getByTestId('tab-school').click();
    await page.getByTestId('chapter-1').click();
    await page.locator('[data-open="2"]').click();
    await expect(page.getByTestId('lesson')).toContainText('Příjem a výdaj');
    await page.locator('#lessonClose').click();
    await expect(page.locator('#schoolTiles')).toContainText('1');
    await expect.poll(async () => (await (await page.request.get('/api/state')).json()).state.school?.read).toEqual([2]);
  });
});
