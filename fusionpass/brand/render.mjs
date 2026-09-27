// Renders the Fusion Pass web app images from logo.svg + League Spartan into ./out.
//   node render.mjs  (needs playwright-core + a Chromium)
import { chromium } from 'playwright-core';
import fs from 'node:fs';
const here = new URL('.', import.meta.url).pathname;
const exe = process.env.CHROME || fs.readdirSync(`${process.env.HOME}/.cache/ms-playwright`).filter((d) => d.startsWith('chromium-')).map((d) => `${process.env.HOME}/.cache/ms-playwright/${d}/chrome-linux64/chrome`)[0];
const splash = fs.readdirSync(`${here}/../../assets/images/splash`).map((f) => f.match(/^apple-splash-(\d+)-(\d+)\.jpg$/)).filter(Boolean);
const jobs = [
  ['logo.png', 'wordmark', 670, 195],
  ['stremio_symbol.png', 'icon', 256, 256],
  ['icon.png', 'icon', 512, 512],
  ['icon_512x512.png', 'icon', 512, 512],
  ['icon_196x196.png', 'icon', 196, 196],
  ['maskable_icon.png', 'maskable', 512, 512],
  ['maskable_icon_512x512.png', 'maskable', 512, 512],
  ['maskable_icon_196x196.png', 'maskable', 196, 196],
  ['monochrome_icon_512x512.png', 'mono', 512, 512],
  ['favicon-256.png', 'icon', 256, 256],
  ...splash.map(([f, w, h]) => [`splash/${f}`, 'splash', +w, +h]),
];
const b = await chromium.launch({ executablePath: exe, args: ['--no-sandbox', '--allow-file-access-from-files'] });
fs.mkdirSync(`${here}/out/splash`, { recursive: true });
for (const [name, k, w, h] of jobs) {
  const p = await b.newPage({ viewport: { width: w, height: h } });
  await p.goto(`file://${here}/render.html?k=${k}&w=${w}&h=${h}`);
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(100);
  const jpg = name.endsWith('.jpg');
  await p.screenshot({ path: `${here}/out/${name}`, type: jpg ? 'jpeg' : 'png', quality: jpg ? 85 : undefined, omitBackground: !jpg, clip: { x: 0, y: 0, width: w, height: h } });
  await p.close();
}
await b.close();
console.log('rendered', jobs.length);
