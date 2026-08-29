// @ts-check
const { test, expect } = require('@playwright/test');

const STORAGE_KEY = 'urokova-kocka-v1';

const STARTED = { startDate: '2020-01-01' }; // a challenge that is already running

/** State with `n` consecutive daily check-ins ending today. */
function stateWith(n, settings = {}, extra = {}) {
  const checkins = [];
  const z = (k) => String(k).padStart(2, '0');
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
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
    await expect(page.getByTestId('tutorial')).toContainText('Ahoj Terezko');
    for (let i = 0; i < 5; i++) await page.getByTestId('tutorial-next').click();
    await expect(page.getByTestId('tutorial')).toContainText('Start:');
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
    await expect(page.getByTestId('balance')).toHaveText('16'); // 16.48 rounded
    await expect(page.getByText('Dnes hotovo')).toBeVisible();
    // Second click the same day is impossible: the button is gone.
    await expect(page.getByTestId('checkin-done')).toHaveCount(0);
    // Persisted on the server, not only in this browser.
    await expect(page.locator('#sync')).toHaveText(/uloženo na serveru/);
    await page.evaluate((k) => localStorage.removeItem(k), STORAGE_KEY);
    await page.reload();
    await expect(page.getByTestId('balance')).toHaveText('16');
    const saved = await (await page.request.get('/api/state')).json();
    expect(saved.state.checkins).toHaveLength(1);
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
});
