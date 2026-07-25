import puppeteer from 'puppeteer-core';
const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const b = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ['--no-sandbox','--disable-gpu','--hide-scrollbars'] });
const ctx = await b.createBrowserContext();
const p = await ctx.newPage();
await p.setViewport({ width: 390, height: 860, deviceScaleFactor: 2 });
const errs = [];
p.on('pageerror', e => errs.push(String(e)));
p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
await p.goto('http://localhost:9301/index.html?load=santo_antonio', { waitUntil: 'domcontentloaded', timeout: 20000 });
await p.waitForSelector('#ago', { timeout: 12000 });
await p.evaluate(() => { const g=document.getElementById('gate');
  g.querySelector('#au').value='nilton'; g.querySelector('#an').value='N C';
  g.querySelector('#ap').value='campo2026'; g.querySelector('#ap2').value='campo2026'; g.querySelector('#ago').click(); });
await p.waitForSelector('#scoutcanvas', { timeout: 15000 });
await new Promise(r => setTimeout(r, 4500));   // dar tiempo a que carguen los tiles
const info = await p.evaluate(async () => {
  let tiles = 0;
  try { const c = await caches.open('pixscout-tiles'); tiles = (await c.keys()).length; } catch(e) {}
  return { tiles, sat: !!document.querySelector('#msat.act') };
});
await p.screenshot({ path: 'shots/16_satelital.png' });
console.log('errores JS:', errs.length ? errs.slice(0,6) : 'ninguno');
console.log('tiles cacheados:', info.tiles, '| satélite activo:', info.sat);
await b.close();
