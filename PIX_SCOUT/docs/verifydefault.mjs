import puppeteer from 'puppeteer-core';
const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const b = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ['--no-sandbox','--disable-gpu'] });
const ctx = await b.createBrowserContext();
const p = await ctx.newPage();
await p.setViewport({ width: 390, height: 860, deviceScaleFactor: 1 });
const errs = [];
p.on('pageerror', e => errs.push(String(e)));
await p.goto('http://localhost:9301/index.html', { waitUntil: 'networkidle0' });   // SIN ?load — prueba DEFAULT_FOCOS
await p.waitForSelector('#ago', { timeout: 12000 });
await p.evaluate(() => { const g = document.getElementById('gate');
  g.querySelector('#au').value='nilton'; g.querySelector('#an').value='N C';
  g.querySelector('#ap').value='campo2026'; g.querySelector('#ap2').value='campo2026';
  g.querySelector('#ago').click(); });
await p.waitForSelector('#scoutcanvas', { timeout: 15000 });
await new Promise(r => setTimeout(r, 900));
const fc = await p.evaluate(() => document.querySelector('.fcount')?.textContent);
console.log('DEFAULT_FOCOS cargó:', fc, '| errores:', errs.length ? errs.slice(0,3) : 'ninguno');
await b.close();
