// Verificación post-fix: flujo REAL de login (sin bypass) + mapa con perímetro (archivo único).
import puppeteer from 'puppeteer-core';
const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const b = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ['--no-sandbox','--disable-gpu','--hide-scrollbars'] });
const ctx = await b.createBrowserContext();
const p = await ctx.newPage();
await p.setViewport({ width: 390, height: 860, deviceScaleFactor: 2 });
const errs = [];
p.on('pageerror', e => errs.push(String(e)));
p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });

// 1) ?load carga el GeoJSON pero NO saltea el login → debe aparecer "Crear administrador"
await p.goto('http://localhost:9301/index.html?load=santo_antonio', { waitUntil: 'networkidle0', timeout: 20000 });
await p.waitForSelector('#ago', { timeout: 12000 });   // gate de crear-admin (prueba: no hubo bypass)
await p.screenshot({ path: 'shots/14_login_real.png' });

// 2) crear admin y entrar
await p.evaluate(() => {
  const g = document.getElementById('gate');
  g.querySelector('#au').value = 'nilton';
  g.querySelector('#an').value = 'Nilton Camargo';
  g.querySelector('#ap').value = 'campo2026';
  g.querySelector('#ap2').value = 'campo2026';
  g.querySelector('#ago').click();
});
await p.waitForSelector('#scoutcanvas', { timeout: 15000 });  // entró a la app y renderizó el mapa
await new Promise(r => setTimeout(r, 1600));
const info = await p.evaluate(() => ({
  fcount: document.querySelector('.fcount')?.textContent,
  gateHidden: document.getElementById('gate').hidden
}));
await p.screenshot({ path: 'shots/15_mapa_perimetro.png' });

console.log('errores JS:', errs.length ? errs.slice(0,6) : 'ninguno');
console.log('info:', JSON.stringify(info));
await b.close();
