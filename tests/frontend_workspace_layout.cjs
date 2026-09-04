// Run with Playwright available and the frontend served at FLATSHOT_TEST_URL.
const assert = require('node:assert/strict');
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.FLATSHOT_TEST_BROWSER
      ? { executablePath: process.env.FLATSHOT_TEST_BROWSER } : {}),
  });
  try {
    const page = await browser.newPage();
    await page.goto(process.env.FLATSHOT_TEST_URL || 'http://127.0.0.1:4180');
    await page.getByRole('button', { name: 'Seleccionar carpeta', exact: true }).waitFor();
    for (const width of [1920, 1600, 1599, 1344, 1120, 1119, 900, 760, 759, 390]) {
      await page.setViewportSize({ width, height: 860 });
      for (const uiState of ['no_folder', 'scanning']) {
        for (const editing of ['false', 'true']) {
          const geometry = await page.evaluate(({ uiState, editing }) => {
            const shell = document.querySelector('.app-shell');
            shell.dataset.uiState = uiState;
            shell.dataset.inspectorEditing = editing;
            shell.dataset.outputEditing = editing;
            const workspace = document.querySelector('.workspace');
            const preview = document.querySelector('.preview-panel');
            return {
              workspace: workspace.getBoundingClientRect().width,
              preview: preview.getBoundingClientRect().width,
              columns: getComputedStyle(workspace).gridTemplateColumns.split(' ').length,
              rows: getComputedStyle(workspace).gridTemplateRows.split(' ').length,
            };
          }, { uiState, editing });
          assert.equal(geometry.columns, 1, `${width}px ${uiState} editing=${editing}: columns`);
          assert.equal(geometry.rows, 1, `${width}px ${uiState}: rows`);
          assert.equal(geometry.preview, geometry.workspace, `${width}px ${uiState}: preview width`);
        }
      }
      const workbenchColumns = await page.evaluate(() => {
        const shell = document.querySelector('.app-shell');
        shell.dataset.uiState = 'ready';
        shell.dataset.batchContext = 'true';
        return getComputedStyle(document.querySelector('.workspace')).gridTemplateColumns.split(' ').length;
      });
      assert.equal(workbenchColumns, width <= 759 ? 1 : width <= 1119 ? 2 : 3,
        `${width}px: editing workbench column count`);
    }
    console.log('PASS: initial/scanning layout and editing workbench at 10 widths');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
