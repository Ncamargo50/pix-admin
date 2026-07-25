/* PIX Scout — Service Worker (offline-first). SUBIR CACHE en cada cambio de assets. */
const CACHE = 'pixscout-v15';
// Cachés que NO se borran en activate: son datos de campo, no assets versionados.
// `pixscout-tiles` = tiles satelitales. `pixscout-focos` = ultimo GeoJSON descargado del
// pipeline; sin esta entrada, cada actualizacion de la app dejaba al tecnico sin los
// focos bajados y con la copia empaquetada, que puede ser de hace meses.
const KEEP = ['pixscout-tiles', 'pixscout-focos'];

/* VERSION DE ASSETS — subir junto con CACHE en cada despliegue.
   Subir solo CACHE NO alcanza: `addAll` pide los archivos por la MISMA URL, asi que el
   HTTP cache del navegador puede devolver la copia vieja y la cache nueva queda poblada
   con codigo viejo. Medido: con CACHE ya en v11, la app seguia ejecutando el data.js
   anterior. El parametro cambia la URL y obliga a bajar de red.
   DEBE coincidir con el ?v= de los <script> de index.html. */
const AV = '1.0.10';
const V = u => u.indexOf('./js/') === 0 || u === './css/app.css' ? u + '?v=' + AV : u;

const ASSETS = [
  './','./index.html','./manifest.webmanifest',
  './css/app.css',
  './js/config.js','./js/data.js','./js/geo.js','./js/store.js','./js/auth.js','./js/map.js','./js/geojson.js','./js/diagnosis.js','./js/umbral.js','./js/importar.js','./js/app.js',
  './data/santo_antonio.geojson',   // sin esto, el primer arranque OFFLINE se queda sin focos
  './icons/icon.svg','./icons/icon-maskable.svg','./icons/icon-192.png','./icons/icon-512.png'
].map(V);
self.addEventListener('install', e=>{
  e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()));
});
self.addEventListener('activate', e=>{
  e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE && KEEP.indexOf(k)<0).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));
});
self.addEventListener('fetch', e=>{
  const req = e.request;
  if(req.method!=='GET') return;
  const url = new URL(req.url);
  if(url.origin!==location.origin) return;   // backend (Supabase/API) siempre a la red

  // Datos dinámicos (GeoJSON de focos): network-first → siempre lo más nuevo, con respaldo offline.
  if(url.pathname.indexOf('/data/')>=0 || url.pathname.endsWith('.geojson')){
    e.respondWith(
      fetch(req).then(res=>{ const copy=res.clone(); caches.open(CACHE).then(c=>c.put(req,copy)).catch(()=>{}); return res; })
                .catch(()=> caches.match(req))
    );
    return;
  }

  // App shell: cache-first (funciona sin señal). Fallback a index.html SOLO para navegaciones.
  e.respondWith(
    caches.match(req).then(hit => hit || fetch(req).then(res=>{
      const copy=res.clone(); caches.open(CACHE).then(c=>c.put(req,copy)).catch(()=>{}); return res;
    }).catch(()=> req.mode==='navigate' ? caches.match('./index.html') : Response.error()))
  );
});
