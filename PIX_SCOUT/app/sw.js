/* PIX Scout — Service Worker (offline-first). SUBIR CACHE en cada cambio de assets. */
const CACHE = 'pixscout-v10';
const KEEP = ['pixscout-tiles'];   // caché de tiles satelitales: NO borrar en activate (offline)
const ASSETS = [
  './','./index.html','./manifest.webmanifest',
  './css/app.css',
  './js/config.js','./js/data.js','./js/geo.js','./js/store.js','./js/auth.js','./js/map.js','./js/geojson.js','./js/diagnosis.js','./js/app.js',
  './data/santo_antonio.geojson',   // sin esto, el primer arranque OFFLINE se queda sin focos
  './icons/icon.svg','./icons/icon-maskable.svg','./icons/icon-192.png','./icons/icon-512.png'
];
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
