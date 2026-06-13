/**
 * AYA vesica-animated.gif generator (wall-clock approach)
 * Loads SVG with animations running, captures frame every 33ms
 * Run: node brand-assets/render-gif.js
 */
const { chromium } = require('/tmp/aya-render/node_modules/playwright');
const path = require('path');
const fs = require('fs');

const ASSETS_DIR = __dirname;
const FRAMES_DIR = path.join(ASSETS_DIR, 'gif-frames');
const SVG_PATH = path.join(ASSETS_DIR, 'vesica-animated.svg');

const WIDTH = 240;
const HEIGHT = 80;
const FPS = 15;           // 15fps for smaller file size
const DURATION_S = 9;
const TOTAL_FRAMES = FPS * DURATION_S;   // 135 frames
const FRAME_MS = 1000 / FPS;             // 66.67ms between frames

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  // Clean up old frames
  if (fs.existsSync(FRAMES_DIR)) {
    fs.readdirSync(FRAMES_DIR).forEach(f => fs.unlinkSync(path.join(FRAMES_DIR, f)));
  } else {
    fs.mkdirSync(FRAMES_DIR);
  }

  const svgContent = fs.readFileSync(SVG_PATH, 'utf8');

  const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; }
  body {
    width: ${WIDTH}px; height: ${HEIGHT}px;
    background: #060A09;
    display: flex; align-items: center; justify-content: center;
    overflow: hidden;
  }
  svg { width: 200px; height: 60px; }
</style>
</head>
<body>${svgContent}</body>
</html>`;

  const browser = await chromium.launch();
  const context = await browser.newContext({ deviceScaleFactor: 1 });
  const page = await context.newPage();
  await page.setViewportSize({ width: WIDTH, height: HEIGHT });

  await page.setContent(html);
  // Let animations initialize for one full cycle before capturing
  console.log('Waiting for animation warm-up (2s)...');
  await sleep(2000);

  console.log(`Capturing ${TOTAL_FRAMES} frames at ${FPS}fps (${DURATION_S}s)...`);

  for (let i = 0; i < TOTAL_FRAMES; i++) {
    const framePath = path.join(FRAMES_DIR, `frame-${String(i).padStart(3, '0')}.png`);
    await page.screenshot({ path: framePath, clip: { x: 0, y: 0, width: WIDTH, height: HEIGHT } });
    if (i % FPS === 0) process.stdout.write(`  frame ${i}/${TOTAL_FRAMES} (t=${i/FPS}s)\n`);
    if (i < TOTAL_FRAMES - 1) await sleep(FRAME_MS);
  }

  await browser.close();
  console.log(`\nAll ${TOTAL_FRAMES} frames saved to ${FRAMES_DIR}/`);
  console.log('Now run: python3 brand-assets/make-gif.py');
}

main().catch(err => { console.error(err); process.exit(1); });
