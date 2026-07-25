// Captura pantallas reales de PIX Scout (modo demo) con Chrome + puppeteer-core.
import puppeteer from 'puppeteer-core';
import fs from 'node:fs';

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const BASE = 'http://localhost:9301/index.html?demo=';
const OUT = 'D:\\PIXADVISOR_AGENT_WORKSPACE\\PIX_SCOUT\\docs\\shots\\';
fs.mkdirSync(OUT, { recursive: true });

// pantalla, selector a esperar, alto de viewport
const SPECS = [
  ['login',      '.gate .card',        820,  '01_login'],
  ['focos',      '.foco',              940,  '02_focos'],
  ['nav',        '.compass',           820,  '03_nav'],
  ['contexto',   '#ph .selchip',      1080,  '04_contexto'],
  ['signo',      '.opts .opt',         920,  '05_signo'],
  ['results',    '.cand',             1020,  '06_results'],
  ['ficha',      '.umbral',           1460,  '07_ficha'],
  ['validacion', '.ndverdict',        1240,  '08_validacion'],
  ['historial',  '.histrow',           940,  '09_historial'],
  ['users',      '.urow',             1320,  '10_users'],
];

const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: true,
  args: ['--no-sandbox', '--disable-gpu', '--hide-scrollbars']
});

for (const [screen, sel, h, name] of SPECS) {
  const ctx = await browser.createBrowserContext();          // storage aislado por captura
  const page = await ctx.newPage();
  await page.setViewport({ width: 390, height: h, deviceScaleFactor: 2 });
  try {
    await page.goto(BASE + screen, { waitUntil: 'networkidle0', timeout: 20000 });
    await page.waitForSelector(sel, { timeout: 12000 });
    await new Promise(r => setTimeout(r, 500));               // asentar animación/fuentes
    await page.screenshot({ path: OUT + name + '.png' });
    console.log('OK  ', name);
  } catch (e) {
    console.log('FAIL', name, '-', e.message.split('\n')[0]);
  }
  await ctx.close();
}
await browser.close();
console.log('done');
