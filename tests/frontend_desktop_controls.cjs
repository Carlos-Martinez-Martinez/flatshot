// Serve the frontend and run with Playwright available, as for frontend_workspace_layout.cjs.
const assert = require('node:assert/strict');
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.FLATSHOT_TEST_BROWSER
      ? { executablePath: process.env.FLATSHOT_TEST_BROWSER } : {}),
  });
  const failures = [];
  const check = async (name, run) => {
    try { await run(); console.log(`PASS: ${name}`); }
    catch (error) { failures.push(name); console.error(`FAIL: ${name}\n${error.message}`); }
  };
  try {
    const page = await browser.newPage();
    await page.addInitScript(() => {
      window.uiTestErrors = [];
      window.addEventListener('error', event => window.uiTestErrors.push(event.message));
      window.addEventListener('unhandledrejection', event => window.uiTestErrors.push(String(event.reason)));
    });
    const settleResize = () => page.evaluate(() => new Promise(resolve => {
      requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    }));
    const url = new URL(process.env.FLATSHOT_TEST_URL || 'http://127.0.0.1:4180');
    url.searchParams.set('dev', '1');
    await page.goto(url.href);
    await page.getByRole('button', { name: 'QA Lab', exact: true }).waitFor();
    await page.getByRole('button', { name: 'QA Lab', exact: true }).click();
    await page.getByRole('button', { name: 'Lote listo', exact: true }).click();
    await page.getByRole('button', { name: 'Cerrar QA Lab', exact: true }).click();
    await page.getByRole('dialog', { name: 'QA Lab', exact: true }).waitFor({ state: 'hidden' });

    await check('toolbar controls remain inside the header and receive clicks', async () => {
      for (const width of [1100, 1119, 1120, 1240, 1344, 1599, 1600, 1920]) {
        await page.setViewportSize({ width, height: 688 });
        await settleResize();
        const invalid = await page.locator('.preview-header').evaluate(header => {
          const bounds = header.getBoundingClientRect();
          return [...header.querySelectorAll('button, summary')].flatMap(el => {
            const rect = el.getBoundingClientRect();
            if (!el.checkVisibility() || !rect.width || !rect.height) return [];
            const hit = document.elementFromPoint(rect.x + rect.width / 2, rect.y + rect.height / 2);
            const inside = rect.left >= bounds.left && rect.right <= bounds.right + 1
              && rect.top >= bounds.top && rect.bottom <= bounds.bottom + 1;
            return inside && el.contains(hit) ? [] : [el.getAttribute('aria-label') || el.textContent.trim()];
          });
        });
        assert.deepEqual(invalid, [], `${width}px: obscured or clipped controls`);
      }
      await page.setViewportSize({ width: 1120, height: 688 });
      await page.getByRole('button', { name: 'Imagen siguiente', exact: true }).click();
      assert.match(await page.locator('.viewer-nav').innerText(), /2\s*\/\s*5/);
      await page.getByRole('button', { name: 'Imagen anterior', exact: true }).click();
      assert.match(await page.locator('.viewer-nav').innerText(), /1\s*\/\s*5/);
    });

    await check('an active inspector does not shrink at the wide breakpoint', async () => {
      await page.evaluate(() => showReviewScenario('batch-ready'));
      await page.setViewportSize({ width: 1599, height: 900 });
      await page.locator('.settings-panel').waitFor({ state: 'visible' });
      const before = await page.locator('.settings-panel').boundingBox();
      for (const width of [1600, 1920]) {
        await page.setViewportSize({ width, height: 900 });
        await settleResize();
        const after = await page.locator('.settings-panel').boundingBox();
        assert.ok(after.width >= before.width, `${width}px: inspector shrank from ${before.width} to ${after.width}`);
      }
    });

    await check('empty-folder inspector opens and closes without reserving a hidden column', async () => {
      await page.setViewportSize({ width: 1100, height: 688 });
      await page.evaluate(() => showReviewScenario('empty-folder'));
      assert.equal(await page.locator('.settings-panel').isVisible(), false, 'inspector initially hidden');
      await page.getByRole('button', { name: 'Ajustes', exact: true }).click();
      assert.equal(await page.locator('.settings-panel').isVisible(), true);
      await page.getByRole('button', { name: 'Cerrar ajustes', exact: true }).click();
      assert.equal(await page.locator('.settings-panel').isVisible(), false, 'inspector hidden after close');
      const widths = await page.evaluate(() => ['.workspace', '.preview-panel'].map(
        selector => document.querySelector(selector).getBoundingClientRect().width));
      assert.equal(widths[0], widths[1], 'empty preview uses full workspace width');
      await page.setViewportSize({ width: 1344, height: 860 });
      assert.equal(await page.locator('.settings-panel').isVisible(), true, 'desktop inspector preserved');
    });
    await check('gallery status remains readable beside its view selector', async () => {
      await page.evaluate(() => showReviewScenario('batch-ready'));
      for (const width of [1100, 1344, 1599, 1600, 1920]) {
        await page.setViewportSize({ width, height: 860 });
        await settleResize();
        const clipped = await page.locator('.gallery-heading').evaluate(el =>
          [...el.querySelectorAll('strong, small')].filter(x => x.scrollWidth > x.clientWidth + 1)
            .map(x => x.textContent));
        assert.deepEqual(clipped, [], `${width}px: gallery status clipped`);
      }
    });
    await check('drawer close remains clickable below a wrapped header', async () => {
      await page.setViewportSize({ width: 900, height: 688 });
      await page.getByRole('button', { name: 'Ajustes', exact: true }).click();
      for (const width of [600, 760, 900]) {
        await page.setViewportSize({ width, height: 688 });
        await settleResize();
        const reachable = await page.getByRole('button', { name: 'Cerrar ajustes', exact: true }).evaluate(el => {
          const r = el.getBoundingClientRect();
          return el.contains(document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2));
        });
        assert.ok(reachable, `${width}px: drawer covers its close button`);
      }
      await page.setViewportSize({ width: 600, height: 688 });
      await page.getByRole('button', { name: 'Cerrar ajustes', exact: true }).click();
      assert.equal(await page.locator('.settings-panel').isVisible(), false);
    });
    await check('output manager reflows without horizontal clipping or overlapping sections', async () => {
      await page.setViewportSize({ width: 1344, height: 860 });
      await page.evaluate(() => showReviewScenario('batch-ready'));
      await page.locator('.settings-panel').getByRole('button', { name: 'Exportación', exact: true }).click();
      await page.getByRole('button', { name: 'Gestionar salidas', exact: true }).click();
      for (const width of [1100, 900, 760, 600]) {
        await page.setViewportSize({ width, height: 688 });
        await settleResize();
        const invalid = await page.locator('#app-settings-modal').evaluate(modal => {
          const selectors = ['.app-settings-content', '.output-format-form', '.format-editor-panel',
            '.format-section-file', '.format-section-image', '.app-settings-footer'];
          return selectors.filter(s => {
            const el = modal.querySelector(s);
            return el.scrollWidth > el.clientWidth + 1;
          });
        });
        assert.deepEqual(invalid, [], `${width}px: output form overflows`);
        const file = await page.locator('.format-section-file').boundingBox();
        const image = await page.locator('.format-section-image').boundingBox();
        assert.ok(file.x + file.width <= image.x + 1 || file.y + file.height <= image.y + 1,
          `${width}px: file and image sections overlap`);
      }
      await page.getByRole('button', { name: 'Cerrar Salidas', exact: true }).click();
      await page.locator('#app-settings-modal').waitFor({ state: 'hidden' });
    });
    await check('resizing does not trigger the global error screen', async () => {
      await settleResize();
      assert.deepEqual(await page.evaluate(() => window.uiTestErrors), []);
      assert.equal(await page.locator('#flatshot-error-boundary').count(), 0);
    });
    assert.deepEqual(failures, [], 'desktop UI regressions');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
