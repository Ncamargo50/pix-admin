import puppeteer from 'puppeteer-core';
const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const b = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ['--no-sandbox','--disable-gpu','--hide-scrollbars'] });
const ctx = await b.createBrowserContext();
const p = await ctx.newPage();
await p.setViewport({ width: 390, height: 860, deviceScaleFactor: 2 });
const errs = [];
p.on('pageerror', e => errs.push(String(e)));
p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
await p.goto('http://localhost:9301/index.html?load=santo_antonio', { waitUntil: 'networkidle0', timeout: 20000 });
await p.waitForSelector('#scoutcanvas', { timeout: 12000 });
await new Promise(r => setTimeout(r, 1600));
// datos cargados
const info = await p.evaluate(() => {
  const fc = document.querySelector('.fcount')?.textContent;
  return { fcount: fc };
});
await p.screenshot({ path: 'shots/12_santoantonio_mapa.png' });
// también la lista
await p.evaluate(() => document.querySelector('.fmode[data-m="lista"]')?.click());
await new Promise(r => setTimeout(r, 400));
await p.screenshot({ path: 'shots/13_santoantonio_lista.png' });
console.log('errores JS:', errs.length ? errs.slice(0,6) : 'ninguno');
console.log('info:', JSON.stringify(info));
await b.close();
