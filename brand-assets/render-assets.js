/**
 * AYA Brand Assets — headless render via Playwright
 * Generates: vesica-static.png, og-default.png
 * Run: node brand-assets/render-assets.js
 */
const { chromium } = require('/tmp/aya-render/node_modules/playwright');
const path = require('path');
const fs = require('fs');

const REPO_ROOT = path.join(__dirname, '..');
const ASSETS_DIR = __dirname;

async function renderSVGtoCanvas(page, svgPath, width, height) {
  const svgContent = fs.readFileSync(svgPath, 'utf8');
  const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { width: ${width}px; height: ${height}px; overflow: hidden; background: transparent; }
  .container { width: ${width}px; height: ${height}px; display: flex; align-items: center; justify-content: center; }
  svg { max-width: 100%; max-height: 100%; }
</style>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@600&display=swap" rel="stylesheet">
</head>
<body>
  <div class="container">${svgContent}</div>
</body>
</html>`;
  await page.setContent(html, { waitUntil: 'networkidle' });
  await page.waitForTimeout(500);
}

async function main() {
  const browser = await chromium.launch();
  const context = await browser.newContext({ deviceScaleFactor: 1 });

  // e) vesica-static.png 240x80 (Outlook fallback)
  {
    const page = await context.newPage();
    await page.setViewportSize({ width: 240, height: 80 });
    const svgPath = path.join(ASSETS_DIR, 'vesica-lockup-L1.svg');
    const svgContent = fs.readFileSync(svgPath, 'utf8');
    const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; }
  body { width: 240px; height: 80px; background: #060A09; display: flex; align-items: center; justify-content: center; overflow: hidden; }
  svg { width: 220px; height: 70px; }
</style>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@600&display=swap" rel="stylesheet">
</head>
<body>${svgContent}</body>
</html>`;
    await page.setContent(html, { waitUntil: 'networkidle' });
    await page.waitForTimeout(800);
    await page.screenshot({
      path: path.join(ASSETS_DIR, 'vesica-static.png'),
      clip: { x: 0, y: 0, width: 240, height: 80 }
    });
    await page.close();
    console.log('vesica-static.png OK (240x80)');
  }

  // c) og-default.png 1200x630
  {
    const page = await context.newPage();
    await page.setViewportSize({ width: 1200, height: 630 });
    const svgPath = path.join(ASSETS_DIR, 'vesica-lockup-L1.svg');
    const svgContent = fs.readFileSync(svgPath, 'utf8');
    const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; }
  body {
    width: 1200px; height: 630px;
    background: #060A09;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    gap: 20px;
    font-family: 'Space Grotesk', system-ui, sans-serif;
    overflow: hidden;
  }
  .lockup { width: 480px; }
  .lockup svg { width: 100%; }
  .tagline {
    color: #6B7370;
    font-size: 24px;
    font-family: 'Geist Mono', 'JetBrains Mono', monospace;
    letter-spacing: 0.02em;
  }
</style>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600&display=swap" rel="stylesheet">
</head>
<body>
  <div class="lockup">${svgContent}</div>
  <div class="tagline">curadoria de novidades sobre IA. todo dia.</div>
</body>
</html>`;
    await page.setContent(html, { waitUntil: 'networkidle' });
    await page.waitForTimeout(800);
    await page.screenshot({
      path: path.join(ASSETS_DIR, 'og-default.png'),
      clip: { x: 0, y: 0, width: 1200, height: 630 }
    });
    await page.close();
    console.log('og-default.png OK (1200x630)');
  }

  await browser.close();
}

main().catch(console.error);
