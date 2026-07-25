/* PIX Scout — aplicación (router + vistas). Usa Geo (GPS real), Store (offline), Dx (motor). */
(function(){
const D=window.PIXDATA, CFG=window.PIXCONFIG;
const IC={
 chevron:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="m9 18 6-6-6-6"/></svg>',
 back:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="m15 18-6-6 6-6"/></svg>',
 route:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="6" cy="19" r="3"/><circle cx="18" cy="5" r="3"/><path d="M9 19h6a4 4 0 0 0 0-8H9a4 4 0 0 1 0-8h6"/></svg>',
 target:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></svg>',
 fungus:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 11a7 7 0 0 1 14 0Z"/><path d="M11 11v7a1.5 1.5 0 0 0 3 0"/></svg>',
 bug:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M8 9a4 4 0 0 1 8 0v4a4 4 0 0 1-8 0Z"/><path d="M8 11H4M20 11h-4M8 15l-3 2M16 15l3 2M8 7 5 5M16 7l3-2M12 5V3"/></svg>',
 leaf:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M11 20A7 7 0 0 1 4 13c0-6 7-9 15-9 0 8-3 15-8 16Z"/><path d="M4 20c2-4 5-7 9-9"/></svg>',
 spray:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M9 11h6v9a1 1 0 0 1-1 1h-4a1 1 0 0 1-1-1Z"/><path d="M9 11V7h4V4M13 4l3 1M13 7l4 1M6 6h.01M6 9h.01M4 8h.01"/></svg>',
 drop:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3s6 6.3 6 10a6 6 0 0 1-12 0c0-3.7 6-10 6-10Z"/></svg>',
 wind:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 8h11a3 3 0 1 0-3-3M3 16h15a3 3 0 1 1-3 3M3 12h9"/></svg>',
 info:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/></svg>',
 gauge:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z"/><path d="M13.4 12.6 19 8M4 16a8 8 0 1 1 16 0Z"/></svg>',
 photo:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="11" r="2"/><path d="m4 18 5-4 4 3 3-2 4 3"/></svg>',
 check:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M20 6 9 17l-5-5"/></svg>',
 camera:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M4 8h3l1.5-2h7L17 8h3a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1Z"/><circle cx="12" cy="13" r="3"/></svg>',
 pin:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M12 21s-7-5.2-7-11a7 7 0 0 1 14 0c0 5.8-7 11-7 11Z"/><circle cx="12" cy="10" r="2.2"/></svg>',
 compass:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><circle cx="12" cy="12" r="9"/><path d="m15.5 8.5-2 5-5 2 2-5 5-2Z"/></svg>',
 arrow:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"><path d="M12 2 5 21l7-4 7 4Z" fill="currentColor"/></svg>',
 eye:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>',
 flask:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"><path d="M9 3h6M10 3v6l-5 8a2 2 0 0 0 1.7 3h10.6A2 2 0 0 0 19 17l-5-8V3"/><path d="M7.5 14h9"/></svg>',
 clock:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
 grid:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
 sat:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M12 3 2 8l10 5 10-5-10-5Z"/><path d="M2 13l10 5 10-5"/><path d="M2 18l10 5 10-5" opacity=".5"/></svg>',
 list:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg>',
 none:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/></svg>',
 up:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"><path d="M12 19V5M6 11l6-6 6 6"/></svg>',
 sync:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 12a9 9 0 0 1-15 6.7L3 16M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M21 3v5h-5M3 21v-5h5"/></svg>',
 alert:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 3 2 20h20L12 3Z"/><path d="M12 10v4M12 17h.01"/></svg>',
 download:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 3v12M7 10l5 5 5-5M4 21h16"/></svg>',
};
const SEVC={muy_alta:'crit',alta:'alta',media:'media',baja:'baja'};
const SEVL={muy_alta:'Muy alta',alta:'Alta',media:'Media',baja:'Baja'};
const CROP_EMOJI={soya:'🫘',trigo:'🌾',maiz:'🌽',sorgo:'🌾',girasol:'🌻',cana_de_azucar:'🎋',pastura:'🌱'};
const CAT_ICON={enfermedad:IC.fungus,plaga:IC.bug,carencia:IC.leaf,abiotico:IC.wind};
const CAT_COL={enfermedad:'var(--enf)',plaga:'var(--plg)',carencia:'var(--car)',abiotico:'var(--abio)'};
const CAT_LABEL={enfermedad:'enfermedad',plaga:'plaga',carencia:'carencia nutricional',abiotico:'causa abiótica'};

const $=s=>document.querySelector(s), main=()=>$('#main');
function esc(s){return (s==null?'':String(s)).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function sevC(s){return SEVC[s]||'media';}
function linkify(s){return esc(s).replace(/(https?:\/\/[^\s]+)/g,'<a href="$1" target="_blank" rel="noopener">$1</a>');}
function crumb(t){$('#crumb').textContent=t;}

let nav='focos', wiz=null, bancoSel=null, SESSION=null, focosMode='mapa', mapInst=null, mapSubs=[], LOADED_FOCI=null, LOADED_BOUNDARY=null;
// De donde salieron los focos que el tecnico esta viendo. Se muestra en pantalla:
// navegar con un mapa viejo creyendolo de hoy es peor que no tener mapa.
let FOCOS_ORIGEN=null, FOCOS_FECHA=null;
// P0: NO caer a los focos demo. `D.focos` son 6 puntos de 5 haciendas distintas a
// mas de 1.000 km entre si; sin GeoJSON el tecnico veia 'focos activos' y la brujula
// lo mandaba a navegar a otra finca. Sin datos reales, la lista va VACIA y se avisa.
let FOCOS_ERROR = null;
function activeFoci(){ return LOADED_FOCI || (CFG.DEMO_FOCOS ? D.focos : []); }
// MODO CIEGO: en campaña de validacion el tecnico NO puede ver el nivel de alerta
// antes de registrar. Sin esto el registro negativo no mide nada: el que sabe que va
// a un rojo encuentra algo. Ver ESPECIFICACION.md §3 y §4.
const CIEGO = !!CFG.MODO_CIEGO;
const sevTxt = f => CIEGO ? '—' : SEVL[f.sev];
const sevCls = f => CIEGO ? 'media' : sevC(f.sev);
const scoreTxt = f => CIEGO ? '·' : f.score;
/* Descarga el GeoJSON de focos del pipeline y lo deja cacheado para uso offline.
   CFG.FOCOS_ENDPOINT estaba declarado pero NINGUN modulo lo leia: cambiar de campo
   exigia recompilar el APK entera. Ahora: si hay endpoint se intenta la red primero,
   y lo que baja queda guardado; si no hay red se usa lo ultimo bajado, y recien
   despues el archivo empaquetado. El tecnico nunca se queda sin focos por estar
   sin señal, y nunca navega con un mapa viejo habiendo uno nuevo disponible. */
const FOCOS_CACHE='pixscout-focos';
async function fetchFocosRemoto(name){
 const base=(window.PIXCONFIG&&PIXCONFIG.FOCOS_ENDPOINT||'').trim();
 if(!base) return null;
 const url=base.replace('{campo}', encodeURIComponent(name))
   + (base.indexOf('{campo}')<0 ? (base.endsWith('/')?'':'/')+encodeURIComponent(name)+'.geojson' : '');
 const ctrl=new AbortController(); const to=setTimeout(()=>ctrl.abort(), 20000);
 try{
  const r=await fetch(url, {cache:'no-store', signal:ctrl.signal});
  clearTimeout(to);
  if(!r.ok) throw new Error('HTTP '+r.status);
  const txt=await r.text();
  const gj=JSON.parse(txt);                       // parsear ANTES de cachear: no guardar basura
  if(!gj || !gj.features) throw new Error('respuesta sin features');
  try{ const c=await caches.open(FOCOS_CACHE);
       await c.put('focos/'+name, new Response(txt, {headers:{'Content-Type':'application/json'}})); }catch(e){}
  return gj;
 }catch(e){
  clearTimeout(to);
  if(console&&console.warn) console.warn('focos remotos no disponibles ('+e.message+'): se usa la copia local');
  return null;
 }
}
async function fetchFocosCacheado(name){
 try{ const c=await caches.open(FOCOS_CACHE); const r=await c.match('focos/'+name);
      return r ? await r.json() : null; }catch(e){ return null; }
}
async function loadFocosGeojson(name){
 // PRIMERO el mapa que el tecnico importo a mano. El canal real es WhatsApp: si abrio
 // un archivo, ESE es su campo — pisarlo al reabrir la app lo mandaria al lote de otro.
 try{
  const imp = await Importar.activo();
  if(imp && imp.nombre){
   const gj = await Importar.leerGuardado(imp.nombre);
   if(gj){
    const meta=(gj.features||[]).map(f=>f.properties||{});
    const hac=(meta.find(p=>p.hacienda)||{}).hacienda;
    const cul=String(((meta.find(p=>p.cultivo)||{}).cultivo)||'').toLowerCase().replace(/[\s-]+/g,'_');
    FOCOS_ORIGEN='recibido por WhatsApp';
    FOCOS_FECHA=meta.reduce((a,p)=>(p.fecha_img&&(!a||p.fecha_img>a))?p.fecha_img:a,null);
    LOADED_FOCI=GeoLoad.fociFromGeoJSON(gj,{hacienda:hac||'Campo',
      cultivo:(cul&&D.cultivos&&D.cultivos[cul])?cul:'trigo',
      cultivoLabel:((meta.find(p=>p.cultivo)||{}).cultivo)||'Lote', idPrefix:'F'});
    LOADED_BOUNDARY=GeoLoad.boundaryFromGeoJSON(gj);
    return LOADED_FOCI;
   }
  }
 }catch(e){}

 let gj=await fetchFocosRemoto(name);
 let origen='remoto';
 if(!gj){ gj=await fetchFocosCacheado(name); origen='descarga previa'; }
 if(!gj){
  const r=await fetch('data/'+encodeURIComponent(name)+'.geojson', {cache:'no-store'});
  if(!r.ok) throw new Error('No se pudo cargar '+name+'.geojson ('+r.status+')');
  gj=await r.json(); origen='empaquetado en la app';
 }
 FOCOS_ORIGEN=origen;
 // Fecha de la escena que origino estos focos. Es lo que permite al tecnico saber si
 // esta mirando el mapa de esta semana o el de hace un mes.
 FOCOS_FECHA=null;
 try{
  for(const ft of (gj.features||[])){
   const d=(ft.properties||{}).fecha_img;
   if(d && (!FOCOS_FECHA || d>FOCOS_FECHA)) FOCOS_FECHA=d;
  }
 }catch(e){}
 // El cultivo y la hacienda salen del GeoJSON, NO de un default fijo. Estaban
 // hardcodeados a Santo Antonio/trigo: cargando los lotes de soya de otra hacienda,
 // la app mostraba "Trigo" y abría el banco de fichas de TRIGO para diagnosticar una
 // soya. El técnico habría buscado royas de trigo en un lote de soya.
 const meta = (gj.features||[]).map(f=>f.properties||{})
   .find(p => p.cultivo || p.hacienda) || {};
 const cultKey = String(meta.cultivo||'').toLowerCase().replace(/[\s-]+/g,'_') || null;
 const cultOk = cultKey && D.cultivos && D.cultivos[cultKey] ? cultKey : null;
 if(meta.cultivo && !cultOk && console && console.warn){
   // Se declara: mejor un aviso que diagnosticar con el banco equivocado en silencio.
   console.warn('cultivo "'+meta.cultivo+'" del GeoJSON no está en el banco; se usa el genérico');
 }
 LOADED_FOCI=GeoLoad.fociFromGeoJSON(gj, {
   hacienda: meta.hacienda || 'Campo',
   cultivo: cultOk || 'trigo',
   cultivoLabel: (cultOk && D.cultivos[cultOk].label) || meta.cultivo || 'Lote',
   estadio: meta.estadio || 'Vegetativo', idPrefix:'F'});
 if(!LOADED_FOCI.length) throw new Error('El GeoJSON no tiene polígonos válidos.');
 // Perímetro del lote: primero del MISMO geojson (features de perímetro); si no, de <name>_boundary.geojson.
 LOADED_BOUNDARY = GeoLoad.boundaryFromGeoJSON(gj);
 if(!LOADED_BOUNDARY.length){
   try{ const rb=await fetch('data/'+encodeURIComponent(name)+'_boundary.geojson',{cache:'no-store'});
     if(rb.ok) LOADED_BOUNDARY=GeoLoad.ringsFromGeoJSON(await rb.json()); }catch(e){}
 }
 return LOADED_FOCI;
}

/* ===== FOCOS (mapa navegable + lista) ===== */
function teardownMap(){
 mapSubs.forEach(u=>{try{u();}catch(e){}}); mapSubs=[];
 if(mapInst){ try{mapInst.destroy();}catch(e){} mapInst=null; }
 try{clearNav();}catch(e){}          // corta el loop de navegación si estaba activo
 try{Geo.stop();}catch(e){}          // apaga el GPS al salir de mapa/navegación (batería)
 const M=main(); M.style.display=''; M.style.flexDirection=''; M.style.padding=''; M.style.overflow='';
}
function renderFocos(){
 nav='focos'; teardownMap(); crumb('Focos activos'); setTab();
 const m = focosMode==='lista' ? 'lista' : 'mapa';
 const M=main(); M.style.display='flex'; M.style.flexDirection='column'; M.style.padding='0'; M.style.overflow='hidden';
 M.innerHTML=`<div class="fmodebar">
   <button class="fmode ${m==='mapa'?'on':''}" data-m="mapa">${IC.pin} Mapa</button>
   <button class="fmode ${m==='lista'?'on':''}" data-m="lista">${IC.list} Lista</button>
   <button class="fmode" data-m="importar" title="Abrir un mapa que te mandaron">${IC.route} Abrir mapa</button>
   <span class="fcount">${FOCOS_ERROR ? 'SIN DATOS DE FOCOS' : activeFoci().length+' focos activos'}${LOADED_FOCI&&FOCOS_FECHA?' · escena '+esc(FOCOS_FECHA):(LOADED_FOCI?' · GeoJSON':'')}${LOADED_FOCI&&FOCOS_ORIGEN&&FOCOS_ORIGEN!=='remoto'?' · '+esc(FOCOS_ORIGEN):''}</span></div>
  <input type="file" accept=".geojson,.json,application/geo+json,application/json" id="fImport" style="display:none">
  <div id="fbody" style="flex:1;min-height:0;position:relative;overflow:${m==='mapa'?'hidden':'auto'}"></div>`;
 M.querySelectorAll('.fmode').forEach(b=>b.onclick=()=>{
   if(b.dataset.m==='importar'){ $('#fImport').click(); return; }
   focosMode=b.dataset.m; renderFocos();
 });
 $('#fImport').onchange = e => {
   const file = e.target.files && e.target.files[0];
   e.target.value = '';                       // permite reabrir el MISMO archivo
   if(file) abrirMapaRecibido(file);
 };
 m==='mapa' ? buildMap($('#fbody')) : buildList($('#fbody'));
}
/* Abre un GeoJSON que llegó por WhatsApp. NO reemplaza el mapa activo en silencio:
   primero muestra qué trae el archivo. Un técnico que sale al campo con el mapa
   equivocado sin haberse enterado es peor que uno sin mapa. */
function abrirMapaRecibido(file){
 const rd = new FileReader();
 rd.onerror = () => toast('No se pudo leer el archivo.');
 rd.onload = () => {
  const r = Importar.inspeccionar(rd.result);
  const wrap = document.createElement('div'); wrap.className='scrim';
  if(!r.ok){
   wrap.innerHTML = `<div class="sheet"><div class="grab"></div>
     <div><div class="eyebrow" style="margin-bottom:6px">No se pudo abrir</div>
     <h2 class="vh" style="font-size:17px">${esc(file.name)}</h2></div>
     <p class="sub">${esc(r.motivo)}</p>
     <p class="sub" style="font-size:11px">Pedile a Pixadvisor el archivo <b>.geojson</b> de la última corrida. Si lo bajaste de WhatsApp, fijate que no sea la vista previa.</p>
     <button class="btn ghost block" id="i-c">Cerrar</button></div>`;
   $('#app').appendChild(wrap);
   wrap.querySelector('#i-c').onclick = () => wrap.remove();
   wrap.onclick = e => { if(e.target===wrap) wrap.remove(); };
   return;
  }
  const dif = FOCOS_FECHA && r.fecha && r.fecha < FOCOS_FECHA;
  wrap.innerHTML = `<div class="sheet"><div class="grab"></div>
    <div><div class="eyebrow" style="margin-bottom:6px">Mapa recibido</div>
    <h2 class="vh" style="font-size:17px">${esc(r.hacienda||'Campo sin nombre')}</h2>
    <div class="sub">${esc(file.name)}</div></div>
    <div class="ndebox" style="margin-top:10px">
      <div class="ndh" style="font-size:12px">
        <b>${r.focos}</b> lote(s) para recorrer${r.fecha?` · escena del <b>${esc(r.fecha)}</b>`:''}${r.perimetro?' · con perímetro del campo':''}
      </div>
    </div>
    ${dif?`<div class="ndverdict at" style="margin-top:8px">${IC.alert} Este mapa es <b>más viejo</b> que el que tenés cargado (${esc(FOCOS_FECHA)}).</div>`:''}
    ${r.aviso?`<div class="sub" style="font-size:11px;margin-top:8px">⚠ ${esc(r.aviso)}</div>`:''}
    <p class="sub" style="font-size:11px;margin-top:8px">Reemplaza el mapa que estás usando. Lo que ya registraste <b>no se borra</b>.</p>
    <div style="display:flex;gap:8px;margin-top:10px">
      <button class="btn ghost" id="i-c" style="flex:1">Cancelar</button>
      <button class="btn lima big" id="i-ok" style="flex:2">Usar este mapa</button></div></div>`;
  $('#app').appendChild(wrap);
  const cerrar = () => wrap.remove();
  wrap.querySelector('#i-c').onclick = cerrar;
  wrap.onclick = e => { if(e.target===wrap) cerrar(); };
  wrap.querySelector('#i-ok').onclick = async () => {
   const nombre = file.name.replace(/\.(geo)?json$/i,'') || 'importado';
   try{ await Importar.guardar(nombre, r.texto); }catch(e){}
   LOADED_FOCI = GeoLoad.fociFromGeoJSON(r.gj, {
     hacienda: r.hacienda||'Campo',
     cultivo: (function(){
       const c=String(((r.gj.features||[]).map(f=>f.properties||{}).find(p=>p.cultivo)||{}).cultivo||'').toLowerCase().replace(/[\s-]+/g,'_');
       return (c && D.cultivos && D.cultivos[c]) ? c : 'trigo'; })(),
     cultivoLabel: (((r.gj.features||[]).map(f=>f.properties||{}).find(p=>p.cultivo)||{}).cultivo)||'Lote',
     idPrefix:'F'});
   LOADED_BOUNDARY = GeoLoad.boundaryFromGeoJSON(r.gj);
   FOCOS_FECHA = r.fecha; FOCOS_ORIGEN = 'recibido por WhatsApp'; FOCOS_ERROR = null;
   cerrar(); toast('Mapa cargado: '+r.focos+' lote(s).');
   renderFocos();
  };
 };
 rd.readAsText(file);
}

function buildList(el){
 const fs=activeFoci();
 el.innerHTML=`<div class="view">
   <div class="eyebrow">${IC.route} Origen · ${LOADED_FOCI?'GeoJSON de anomalías':'motor satelital'}</div>
   <h2 class="vh">${fs.length} focos para validar</h2>
   <p class="sub">${CIEGO?'Orden de recorrida asignado. El nivel de alerta no se muestra hasta registrar.':'Ordenados por prioridad de recorrida.'} Tocá un foco para navegar por GPS y diagnosticar.</p>
   ${fs.map((f,i)=>focoCard(f,i)).join('')}
   <div class="callout">${IC.info}<div>Cada validación vuelve como <b>verdad de campo</b> y recalibra el próximo mapa de anomalías.</div></div></div>`;
 el.querySelectorAll('.foco').forEach(e=>e.onclick=()=>renderNav(fs[+e.dataset.i]));
}
function buildMap(el){
 el.innerHTML=`<canvas id="scoutcanvas" style="width:100%;height:100%;display:block;touch-action:none"></canvas>
  <div class="mapctrls">
    <button class="mapbtn" id="msat" aria-label="Satélite / vector" title="Satélite / vector">${IC.sat}</button>
    <button class="mapbtn" id="mzin" aria-label="Acercar">+</button>
    <button class="mapbtn" id="mzout" aria-label="Alejar">&#8211;</button>
    <button class="mapbtn" id="mrec" aria-label="Centrar en mí">${IC.pin}</button>
    <button class="mapbtn" id="mfit" aria-label="Ver todo">${IC.grid}</button>
  </div>
  <div class="maplegend"><span><i style="background:#ef4444"></i>Muy alta</span><span><i style="background:#f59e0b"></i>Alta</span><span><i style="background:#14b8a6"></i>Media</span><span><i style="background:#84cc16"></i>Baja</span></div>
  <div class="maphint" id="maphint"></div>
  <div class="mapsheet" id="mapsheet" hidden></div>`;
 const fs=activeFoci();
 const mapFoci=fs.map(f=>Object.assign({},f,{sevClass:sevC(f.sev)}));
 const dark=(document.documentElement.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light'))!=='light';
 mapInst=ScoutMap.create($('#scoutcanvas'), {onSelect:onFocoTap, dark});
 if(LOADED_BOUNDARY && LOADED_BOUNDARY.length) mapInst.setBoundary(LOADED_BOUNDARY);   // perímetro del lote
 mapInst.setFoci(mapFoci);
 // Con GeoJSON real (focos de una misma finca) muestra todos; si están dispersos, centra en el prioritario.
 if(LOADED_FOCI){ mapInst.fit(); } else { const f0=fs[0]; if(f0) mapInst.centerOn(f0.lat, f0.lon, 1200); }
 Geo.start(); Geo.startCompass();
 const push=()=>{ const p=Geo.current(); if(p&&p.lat!=null&&mapInst) mapInst.setUser({lat:p.lat,lon:p.lon,acc:p.acc}, Geo.heading()); updHint(); };
 mapSubs.push(Geo.onPos(push)); mapSubs.push(Geo.onHeading(push)); push();
 $('#mzin').onclick=()=>mapInst&&mapInst.zoomIn(); $('#mzout').onclick=()=>mapInst&&mapInst.zoomOut();
 $('#mrec').onclick=()=>mapInst&&mapInst.recenter(); $('#mfit').onclick=()=>mapInst&&mapInst.fit();
 const sbtn=$('#msat'); if(sbtn){ sbtn.classList.toggle('act', mapInst.isSatellite());
   sbtn.onclick=()=>{ const on=!mapInst.isSatellite(); mapInst.setSatellite(on); sbtn.classList.toggle('act',on); }; }
}
function updHint(){ const h=$('#maphint'); if(!h)return; const sh=$('#mapsheet'); if(sh && !sh.hidden){ h.style.display='none'; return; } h.style.display='';
 const p=Geo.current();
 if(!Geo.available()||!p||p.lat==null){ h.innerHTML=IC.pin+' <span>GPS buscando señal — el mapa igual funciona.</span>'; }
 else { h.innerHTML=IC.pin+' <span>Tu posición · ±'+Math.round(p.acc||0)+' m. Tocá un foco para navegar.</span>'; } }
function onFocoTap(f){
 const sheet=$('#mapsheet'); if(!sheet) return; const p=Geo.current();
 const dm=(p&&p.lat!=null&&mapInst)?mapInst.dist({lat:p.lat,lon:p.lon},{lat:f.lat,lon:f.lon}):null;
 const sc=sevC(f.sev);
 sheet.hidden=false; updHint();
 sheet.innerHTML=`<div class="ms-h"><span class="cdot" style="background:var(--${sc})"></span>
   <div class="ms-t"><b>${esc(f.cultivoLabel)} · ${esc(f.lote)}</b><span>${esc(f.hacienda)} · ${esc(f.estadio)} · ${sevTxt(f)}${dm!=null?' · '+esc(mapInst.fmt(dm))+' de acá':''}</span></div>
   <button class="ms-x" id="ms-x" aria-label="Cerrar">&#10005;</button></div>
   <div class="ms-b">
     <button class="btn ghost" id="ms-nav" style="flex:1">${IC.compass} Navegar</button>
     <button class="btn brand" id="ms-diag" style="flex:1">${IC.check} Diagnosticar</button>
   </div>`;
 $('#ms-x').onclick=()=>{ sheet.hidden=true; mapInst&&mapInst.select(null); updHint(); };
 $('#ms-nav').onclick=()=>renderNav(f);
 $('#ms-diag').onclick=()=>startWizardFoco(f);
}
function focoCard(f,i){const s=sevC(f.sev);
 return `<div class="foco" data-i="${i}"><div class="stripe" style="background:var(--${s})"></div>
  <div class="fmain"><div class="frow"><span class="fcrop">${esc(f.cultivoLabel)}</span><span class="chip ${CIEGO?'media':s}"><span class="sev-i ${CIEGO?'media':s}"></span>${sevTxt(f)}</span></div>
  <div class="floc">${esc(f.hacienda)} · ${esc(f.lote)}</div>
  <div class="fmeta"><span>Área <b>${f.area_ha} ha</b></span><span>Punto <b>${f.punto}</b></span><span>Sev <b>${scoreTxt(f)}</b></span></div>
  <div class="fpat">Patrón satelital: <b>${esc(f.patronLabel)}</b> · ${esc(f.resumen)}</div></div>
  <span class="fgo">${IC.route}</span></div>`;
}

/* ===== NAVEGACIÓN GPS ===== */
let navUnsub=[];
function clearNav(){navUnsub.forEach(u=>{try{u();}catch(e){}});navUnsub=[];}
function renderNav(f){
 nav='nav'; teardownMap(); crumb('Navegación al foco'); setTab(); clearNav();
 const tgt={lat:f.lat,lon:f.lon};
 main().innerHTML=`<div class="view">
  <div class="ctx"><span class="cdot" style="background:var(--${sevC(f.sev)})"></span>
   <div class="ct"><b>${esc(f.cultivoLabel)} · ${esc(f.lote)}</b><span>${esc(f.hacienda)} · ${esc(f.estadio)} · ${sevTxt(f)}</span></div>
   <span class="chip ${sevCls(f)}">${scoreTxt(f)}</span></div>
  <div class="navcard" id="navcard">
   <div class="compass"><span class="ndeg" id="ndeg">N</span><div class="arrow" id="arrow">${IC.arrow}</div></div>
   <div class="navdist" id="ndist">buscando…</div>
   <div class="navsub" id="nsub">señal GPS</div>
   <div class="gpsline" id="gline">${IC.pin}<span>Adquiriendo posición…</span></div>
  </div>
  <div class="navrow">
   <button class="btn ghost" id="nv-back" style="flex:1">${IC.back} Focos</button>
   <button class="btn brand big" id="nv-diag" style="flex:2">${IC.compass} Diagnosticar aquí</button>
  </div>
  <div class="navrow" style="margin-top:8px">
   <button class="btn ghost block" id="nv-nada">${IC.check} Llegué y no encontré nada</button>
  </div>
  <div class="callout">${IC.info}<div>La flecha apunta al foco; se orienta con la brújula del teléfono si está disponible. La app no bloquea el diagnóstico si el GPS es impreciso.</div></div>
 </div>`;
 $('#nv-back').onclick=()=>{clearNav();renderFocos();};
 $('#nv-diag').onclick=()=>{clearNav();startWizardFoco(f);};
 // sin clearNav(): si el técnico cancela, la brújula tiene que seguir viva detrás
 $('#nv-nada').onclick=()=>registrarSinHallazgo(f);
 Geo.start(); Geo.startCompass();
 const upd=()=>{
  const p=Geo.current(), h=Geo.heading();
  const dist=(p&&p.lat!=null)?Geo.haversine({lat:p.lat,lon:p.lon},tgt):null;
  const brg=(p&&p.lat!=null)?Geo.bearing({lat:p.lat,lon:p.lon},tgt):null;
  const dEl=$('#ndist'),sEl=$('#nsub'),gEl=$('#gline'),ar=$('#arrow'),nd=$('#ndeg'),card=$('#navcard');
  if(!dEl) return;
  if(!Geo.available()){dEl.textContent='GPS no disp.';sEl.textContent='sin geolocalización';gEl.innerHTML=IC.pin+'<span>Este dispositivo no expone GPS.</span>';return;}
  if(!p||p.error){dEl.textContent='—';sEl.textContent=p&&p.error?'permiso denegado':'buscando señal';gEl.innerHTML=IC.pin+'<span>'+(p&&p.msg?esc(p.msg):'Activá la ubicación / permití GPS')+'</span>';return;}
  dEl.textContent=Geo.fmtDist(dist);
  const near=dist!=null&&dist<=CFG.PROXIMITY_M;
  sEl.textContent=near?'estás en el foco':('rumbo '+(brg!=null?Math.round(brg)+'°':'—'));
  card.classList.toggle('navclose',near);
  gEl.innerHTML=IC.pin+'<span>'+p.lat.toFixed(5)+', '+p.lon.toFixed(5)+' · ±'+Math.round(p.acc||0)+' m</span>';
  if(brg!=null){const rot=(h!=null)?(brg-h):brg; ar.style.transform='rotate('+rot+'deg)'; nd.textContent=(h!=null)?'brújula':'norte';}
 };
 navUnsub.push(Geo.onPos(upd)); navUnsub.push(Geo.onHeading(upd)); upd();
 const iv=setInterval(upd,1000); navUnsub.push(()=>clearInterval(iv));
}

/* ===== WIZARD (motor Dx) ===== */
function startWizardFoco(f){teardownMap();wiz={foco:f,cultivo:f.cultivo,estadio:f.estadio,patron:f.patron,host:'no',temporal:'gradual',signo:null,signoCat:null,fork:null,branch:null,step:0,fromBanco:false};renderWizard();}
function startWizardBanco(c){teardownMap();wiz={foco:null,cultivo:c,estadio:'Vegetativo',patron:null,host:'no',temporal:'gradual',signo:null,signoCat:null,fork:null,branch:null,step:0,fromBanco:true};renderWizard();}
function wizCtx(){const c=D.cultivos[wiz.cultivo],f=wiz.foco,s=f?sevC(f.sev):'media';
 return `<div class="ctx"><span class="cdot" style="background:var(--${s})"></span><div class="ct"><b>${esc(c.label)}${f?' · '+esc(f.lote):''} · ${esc(wiz.estadio)}</b><span>${f?esc(f.hacienda)+' · '+sevTxt(f):'Consulta desde el banco'}</span></div>${f?`<span class="chip ${CIEGO?'media':s}">${scoreTxt(f)}</span>`:''}</div>`;}
function stepsBar(cur){let h='';for(let i=0;i<4;i++)h+=`<div class="stepdot ${i<cur?'done':i===cur?'on':''}"></div>`;return `<div class="steps">${h}</div>`;}
const ICN={foco:IC.target,difuso:IC.leaf,borde:IC.compass,relieve:IC.drop,estructura_fungica:IC.fungus,insecto:IC.bug,larva:IC.bug,ninguno:IC.none,masticador:IC.leaf,picador_succionador:IC.drop,cortador_subterraneo:IC.spray,minador_barrenador:IC.target,ascendente:IC.up,localizado:IC.target,espiga:IC.flask,nutricional:IC.leaf,abiotico:IC.wind,vieja_a_nueva:IC.leaf,nueva:IC.up,generalizado:IC.none};
function optHTML(o,sel){const bias=o.bias?`<span class="obias ${o.bias}">${o.bias==='bio'?'biótico':'abiótico'}</span>`:`<span class="oc">${IC.chevron}</span>`;
 return `<button class="opt ${o.v===sel?'sel':''}" data-v="${o.v}"><span class="oi">${ICN[o.v]||IC.none}</span><span class="ol"><b>${esc(o.b)}</b><small>${esc(o.s)}</small></span>${bias}</button>`;}
function wizQuestion(step,qnum,q,help,opts,sel,onPick){
 crumb('Diagnóstico diferencial'); setTab();
 main().innerHTML=`<div class="view">${wizCtx()}${stepsBar(step)}<div class="qnum">${esc(qnum)}</div><div class="q">${esc(q)}</div><div class="qhelp">${esc(help)}</div><div class="opts">${opts.map(o=>optHTML(o,sel)).join('')}</div><div class="navfoot"><button class="btn ghost block" id="w-back">${IC.back} Atrás</button></div></div>`;
 main().querySelectorAll('.opt').forEach(el=>el.onclick=()=>onPick(el.dataset.v));
 $('#w-back').onclick=wizBack;
}
function renderWizard(){
 nav='wizard'; setTab();
 const s=wiz.step;
 if(s===0) return wizContexto();
 if(s===1) return wizQuestion(1,'Paso 2 · patrón','¿Cómo se distribuye el daño en el lote?','Foco irregular → biótico. Parejo/geométrico, bordes o topografía → sospechar abiótico.',Dx.PATRON_OPTS,wiz.patron,v=>{wiz.patron=v;wiz.step=2;renderWizard();});
 if(s===2) return wizQuestion(2,'Paso 3 · signo','¿Hay signo del organismo? Mirá con lupa, incluido el envés.','SIGNO = presencia física (pústula, insecto, huevo). SÍNTOMA = solo la reacción de la planta. El signo confirma la causa biótica.',Dx.SIGNO_OPTS,wiz.signo,v=>{wiz.signo=v;wiz.signoCat=Dx.SIGNO_OPTS.find(o=>o.v===v).cat;wiz.fork=null;wiz.branch=null;wiz.step=3;renderWizard();});
 if(s===3){
  if(wiz.signoCat==='plaga') return wizQuestion(3,'Paso 4 · tipo de daño','¿Qué tipo de daño hace?','El aparato bucal define el grupo de plaga y acota los candidatos.',Dx.DANO_OPTS,wiz.branch,v=>{wiz.branch=v;wiz.step=4;renderWizard();});
  if(wiz.signoCat==='enfermedad') return wizQuestion(3,'Paso 4 · avance','¿Dónde empezó y cómo avanza?','Muchas royas suben de las bajeras; otras atacan el estrato medio o la espiga.',Dx.DIST_OPTS,wiz.branch,v=>{wiz.branch=v;wiz.step=4;renderWizard();});
  if(wiz.fork==null) return wizQuestion(3,'Paso 4 · sin signo','Sin signo del organismo. ¿Qué explica mejor el síntoma?','Separa deficiencia nutricional de una causa abiótica (deriva, agua, clima, suelo).',Dx.FORK_OPTS,null,v=>{wiz.fork=v;if(v==='abiotico')wiz.step=4;renderWizard();});
  if(wiz.fork==='nutricional') return wizQuestion(3,'Paso 4 · gradiente de hoja','¿En qué hojas aparece primero?','Móviles (N,P,K,Mg) migran a las nuevas → síntoma en las VIEJAS. Inmóviles (S,Fe,Zn,B,Cu,Mn) → en las NUEVAS.',Dx.GRAD_OPTS,wiz.branch,v=>{wiz.branch=v;wiz.step=4;renderWizard();});
  if(wiz.fork==='abiotico') return renderResults();
 }
 if(s===4) return renderResults();
}
function wizContexto(){
 crumb('Contexto del foco'); setTab();
 main().innerHTML=`<div class="view">${wizCtx()}${stepsBar(0)}
  <div class="qnum">Paso 1 · contexto</div><div class="q">Antes de mirar la planta: contexto del lote</div>
  <div class="qhelp">El diagnóstico profesional empieza por el contexto, no por la foto. Estadio, si hay otros cultivos afectados y cuándo apareció el daño deciden la mitad de los casos.</div>
  <div class="field"><div class="flabel" style="margin-bottom:7px">Estadio fenológico</div><div class="chips" id="ph">${Dx.PHENO.map(p=>`<button class="selchip ${p===wiz.estadio?'on':''}" data-p="${p}">${p}</button>`).join('')}</div></div>
  <div class="field"><div class="flabel" style="margin-bottom:7px">¿El mismo daño aparece en otros cultivos o lotes vecinos?</div><div class="toggle2" id="tgH">
   <div class="tg ${wiz.host==='no'?'on':''}" data-v="no"><b>No, solo este cultivo</b><small>Sugiere biótico</small></div>
   <div class="tg ${wiz.host==='si'?'on':''}" data-v="si"><b>Sí, varias especies</b><small>Sugiere abiótico</small></div></div></div>
  <div class="field"><div class="flabel" style="margin-bottom:7px">¿Cómo apareció?</div><div class="toggle2" id="tgT">
   <div class="tg ${wiz.temporal==='gradual'?'on':''}" data-v="gradual"><b>Fue progresando</b><small>Sugiere biótico</small></div>
   <div class="tg ${wiz.temporal==='subito'?'on':''}" data-v="subito"><b>De golpe / súbito</b><small>Sugiere abiótico</small></div></div></div>
  <div class="navfoot"><button class="btn ghost" id="cx-b">${IC.back} Atrás</button><button class="btn brand big block" id="cx-n" style="flex:1">Continuar ${IC.chevron}</button></div></div>`;
 main().querySelectorAll('#ph .selchip').forEach(el=>el.onclick=()=>{wiz.estadio=el.dataset.p;main().querySelectorAll('#ph .selchip').forEach(x=>x.classList.toggle('on',x.dataset.p===wiz.estadio));$('.ctx .ct b').innerHTML=esc(D.cultivos[wiz.cultivo].label)+(wiz.foco?' · '+esc(wiz.foco.lote):'')+' · '+esc(wiz.estadio);});
 const bt=(sel,k)=>main().querySelectorAll(sel+' .tg').forEach(el=>el.onclick=()=>{wiz[k]=el.dataset.v;main().querySelectorAll(sel+' .tg').forEach(x=>x.classList.toggle('on',x.dataset.v===wiz[k]));});
 bt('#tgH','host'); bt('#tgT','temporal');
 $('#cx-b').onclick=()=>wiz.fromBanco?renderBancoList(wiz.cultivo):(wiz.foco?renderNav(wiz.foco):renderFocos());
 $('#cx-n').onclick=()=>{wiz.step=1;renderWizard();};
}
function wizBack(){
 if(wiz.step===4){ if(wiz.signoCat==='indef'&&wiz.fork==='abiotico'){wiz.fork=null;wiz.step=3;} else {wiz.branch=null;wiz.step=3;} return renderWizard(); }
 if(wiz.step===3){ if(wiz.signoCat==='indef'&&wiz.fork==='nutricional'){wiz.fork=null;wiz.branch=null;return renderWizard();} wiz.signo=null;wiz.signoCat=null;wiz.fork=null;wiz.branch=null;wiz.step=2;return renderWizard(); }
 if(wiz.step===2){wiz.signo=null;wiz.step=1;return renderWizard();}
 if(wiz.step===1){wiz.step=0;return renderWizard();}
 return wiz.fromBanco?renderBancoList(wiz.cultivo):(wiz.foco?renderNav(wiz.foco):renderFocos());
}
function renderResults(){
 nav='wizard'; crumb('Diagnóstico'); setTab();
 const R=Dx.evaluate(wiz);
 const cc=R.topConf>=70?'var(--baja)':R.topConf>=55?'var(--alta)':'var(--crit)';
 main().innerHTML=`<div class="view">${wizCtx()}${stepsBar(4)}
  <div class="verdict ${R.uncertain?'warn':''}"><span class="vk">${R.uncertain?IC.alert:IC.check} Hipótesis presuntiva de la clave</span>
   <span class="vt">Probable ${CAT_LABEL[R.cat]} · ${R.candidates.length} candidato${R.candidates.length!==1?'s':''}</span>
   <div class="conf"><div class="confbar"><i style="width:${Math.max(R.topConf,4)}%;background:${cc}"></i></div><b style="color:${cc}">${R.topConf}%</b></div>
   <p class="sub" style="margin-top:2px">Coincidencia con lo observado + coherencia biótico/abiótico. No es un diagnóstico cerrado: comparás con la ficha y confirmás vos.</p></div>
  ${R.uncertain?`<div class="callout lab">${IC.flask}<div><b>Diagnóstico no concluyente.</b> Señales mixtas o confianza baja. Buscá el signo con lupa o colectá muestra a laboratorio (IBRA) antes de aplicar.</div></div>`:''}
  ${R.candidates.length?R.candidates.map(x=>`<div class="cand"><div class="chead" data-id="${x.f.id}"><span class="cbadge" style="background:${CAT_COL[x.f.categoria]}">${x.conf}</span><span class="cti"><b>${esc(x.f.nombre_comun)}</b><i>${esc(x.f.nombre_cientifico)}</i><span class="catpill ${x.f.categoria}">${x.f.categoria}</span></span><span class="cmatch"><b>${x.conf}%</b><span>confianza</span></span></div></div>`).join(''):`<div class="empty">Sin coincidencias claras. Ajustá el patrón o el signo, o colectá muestra a IBRA.</div>`}
  <div class="callout">${IC.info}<div>Diagnóstico visual = <b>hipótesis</b>, no verdad. Ante virus, nematodos o decisión de alto costo, confirmá por laboratorio.</div></div>
  <div class="navfoot"><button class="btn ghost" id="r-b">${IC.back} Cambiar</button><button class="btn brand" id="r-lab" style="flex:1">${IC.flask} Colectar a laboratorio</button></div></div>`;
 main().querySelectorAll('.cand .chead').forEach(el=>el.onclick=()=>renderFicha(el.dataset.id,'results'));
 $('#r-b').onclick=wizBack;
 $('#r-lab').onclick=()=>toast('Muestra marcada para IBRA megalab. Se generó la ficha de envío georreferenciada.');
}

/* ===== FICHA ===== */
function renderFicha(id,from){
 const r=Dx.findFicha(id); if(!r)return; const f=r.f;
 nav='ficha'; crumb(f.nombre_comun); setTab();
 const s=sevC(f.severidad_potencial);
 const conf=(f.confusiones||[]).map(c=>`<div class="confu"><b>${esc(c.con)}</b><span>${esc(c.como_diferenciar)}</span></div>`).join('');
 const ph=(f.fotos||[]).filter(p=>typeof p==='object');
 const phHTML=ph.length?`<div class="field"><div class="fl">${IC.photo} Fotos de referencia · licencia abierta</div><div class="photos">${ph.map(p=>`<a class="photo" href="${esc(p.url)}" target="_blank" rel="noopener"><span class="pimg">${IC.photo}</span><span class="pcap"><b>${esc(p.muestra)}</b><span class="plic">${esc(p.licencia)}</span><span class="paut">${esc(p.autor)}</span></span></a>`).join('')}</div></div>`:(f.categoria==='abiotico'?'':`<div class="callout">${IC.photo}<div>Foto con licencia abierta pendiente de curar. En campo se muestra junto a la que saca el técnico.</div></div>`);
 const isLoc=/VERIFICAR_LOCAL/.test(f.umbral_accion||'');
 const um=f.umbral_accion?`<div class="umbral"><div class="uh">${IC.gauge} Umbral de acción MIP ${isLoc?`<span class="locflag">${IC.alert} verificar local</span>`:''}</div><div class="ub">${esc(f.umbral_accion)}</div>${f.fuente_umbral?`<div class="usrc">Fuente: ${linkify(f.fuente_umbral)}</div>`:''}</div>`:'';
 main().innerHTML=`<div class="view">
  <div style="display:flex;gap:9px"><button class="btn ghost block" id="f-b">${IC.back} Atrás</button></div>
  <div style="display:flex;gap:11px;align-items:flex-start">
   <span class="cbadge" style="width:46px;height:46px;border-radius:12px;background:${CAT_COL[f.categoria]};display:grid;place-items:center;color:#fff">${CAT_ICON[f.categoria]}</span>
   <div style="flex:1;min-width:0"><h2 class="vh" style="font-size:18px">${esc(f.nombre_comun)}</h2>
    <div style="font-size:12px;color:var(--ink-soft);font-style:italic">${esc(f.nombre_cientifico)}${f.nombre_pt?' · '+esc(f.nombre_pt):''}</div>
    <div style="display:flex;gap:6px;margin-top:6px;flex-wrap:wrap"><span class="catpill ${f.categoria}">${f.categoria}</span><span class="chip ${s}"><span class="sev-i ${s}"></span>Impacto ${SEVL[f.severidad_potencial]}</span></div></div></div>
  <div class="field signo"><div class="fl">${IC.eye} Signo · presencia del organismo</div><div class="fv">${esc(f.signo)}</div></div>
  <div class="field sintoma"><div class="fl">${IC.leaf} Síntoma · reacción de la planta</div><div class="fv">${esc(f.sintoma)}</div></div>
  <div class="field"><div class="fl">${IC.target} Confirmación a campo</div><div class="fv">${esc(f.confirmacion_campo)}</div></div>
  ${conf?`<div class="field"><div class="fl">${IC.info} Diagnóstico diferencial</div>${conf}</div>`:''}
  ${um}${phHTML}
  ${f.manejo_ref?`<div class="field"><div class="fl">${IC.spray} Manejo</div><div class="fv">${esc(f.manejo_ref)}</div></div>`:''}
  <button class="btn lima big block" id="f-v">${IC.check} Confirmar y registrar validación</button></div>`;
 $('#f-b').onclick=()=> from==='results'?renderResults(): from==='banco'?renderBancoList(r.cultivo):renderFocos();
 $('#f-v').onclick=()=>openValidacion(f, r.cultivo);
}

/* ===== REGISTRO NEGATIVO =====
   El técnico llegó al foco y no encontró nada. Sin este registro no hay falsos
   positivos medibles ni falsos negativos: el protocolo de validación exige muestrear
   también el estrato verde, y sin "nada encontrado" toda visita termina en un
   hallazgo. Es la diferencia entre calibrar el motor y confirmarle lo que ya creía. */
function registrarSinHallazgo(f){
 const p=Geo.current(), gpsFix=!!(p&&p.lat!=null);
 const coord = gpsFix ? p.lat.toFixed(5)+', '+p.lon.toFixed(5) : (f?f.lat.toFixed(5)+', '+f.lon.toFixed(5):'—');
 const wrap=document.createElement('div'); wrap.className='scrim';
 wrap.innerHTML=`<div class="sheet"><div class="grab"></div>
  <div><div class="eyebrow" style="margin-bottom:6px">Registro sin hallazgo</div>
   <h2 class="vh" style="font-size:17px">No se encontró nada en el foco</h2>
   <div class="sub">${esc(f?f.hacienda:'')} · ${esc(f?f.lote:'')}</div></div>
  <div class="gpsbox${gpsFix?'':' nogps'}">${gpsFix?IC.pin:IC.alert}<span>${esc(coord)}${gpsFix?' · ±'+Math.round(p.acc||0)+' m':' · SIN fijar GPS'}</span></div>
  <div class="field"><div class="lbl" style="margin-bottom:6px">¿Qué se revisó?</div>
   <div class="segbar" data-g="alcance">${['Punto','Recorrido parcial','Lote completo'].map((x,i)=>`<div class="seg ${i===0?'on':''}" data-v="${esc(x)}">${esc(x)}</div>`).join('')}</div></div>
  <div class="field"><div class="lbl" style="margin-bottom:6px">Observación (opcional)</div>
   <textarea id="obs" rows="3" placeholder="Cultivo sano, sin síntomas visibles…"></textarea></div>
  <div style="display:flex;gap:8px"><button class="btn ghost" id="n-c" style="flex:1">Cancelar</button>
   <button class="btn lima big" id="n-s" style="flex:2">${IC.check} Guardar sin hallazgo</button></div>
  <div class="sub" style="text-align:center;font-size:10.5px">Este registro vale tanto como uno positivo: es lo que mide si el aviso fue correcto.</div></div>`;
 $('#app').appendChild(wrap);
 const st={alcance:'Punto'};
 wrap.querySelectorAll('.segbar').forEach(bar=>{const g=bar.dataset.g;bar.querySelectorAll('.seg').forEach(s=>s.onclick=()=>{bar.querySelectorAll('.seg').forEach(o=>o.classList.remove('on'));s.classList.add('on');st[g]=s.dataset.v;});});
 const close=()=>wrap.remove();
 wrap.querySelector('#n-c').onclick=close;
 wrap.onclick=e=>{if(e.target===wrap)close();};
 wrap.querySelector('#n-s').onclick=async()=>{
  const v={focoId:f?f.id:null, focoIdEstable:(f&&f.idEstable!=null)?!!f.idEstable:null,
   estrato:f?f.estrato:null,
   hacienda:f?f.hacienda:null, lote:f?f.lote:null, fechaImg:f?f.fechaImg:null,
   hallazgo:'nada', categoria:null, fichaId:null, alcance:st.alcance,
   // dirigido = el satelite eligio el sitio. NO entra al calculo del umbral MIP.
   tipo_muestreo:'dirigido_satelital',
   // el historial pinta estos campos; sin ellos el registro negativo — que es el
   // que permite medir los falsos positivos — sale como una fila en blanco
   nombre:'Sin hallazgo', cultivo:(f?f.cultivoLabel:''), estadio:(f?f.estadio:''),
   severidad:'—',
   observacion:(wrap.querySelector('#obs').value||'').trim(),
   coord, acc:gpsFix?Math.round(p.acc||0):null, gps_real:gpsFix,
   tecnico:(SESSION?(SESSION.nombre||SESSION.username):'campo'), cliente:(SESSION?SESSION.cliente:'')};
  try{ await Store.saveValidacion(v); }catch(e){}
  close(); toast('Registrado: sin hallazgo. Es el dato que permite medir los falsos positivos.');
  updateSync(); Store.syncNow().then(updateSync);
  clearNav(); renderFocos();     // el foco quedó resuelto: se sale de la navegación
 };
}

/* ===== VALIDACIÓN (guardado offline + cámara) ===== */
let camStream=null;
function stopCam(){if(camStream){camStream.getTracks().forEach(t=>t.stop());camStream=null;}}
function openValidacion(f, cultivoFicha){
 // Si se llegó por el Banco, `wiz` todavía arrastra el último foco navegado: sin este
 // guard el registro sale estampado con la identidad de OTRO foco, que es justo el
 // dato con el que después se mide la precisión del motor.
 const foco=(wiz&&!wiz.fromBanco)?wiz.foco:null;
 const est=(wiz&&wiz.estadio)||'Vegetativo', isPlaga=f.categoria==='plaga';
 const p=Geo.current(); const gpsFix = !!(p&&p.lat!=null);
 const coord = gpsFix ? p.lat.toFixed(5)+', '+p.lon.toFixed(5) : (foco? foco.lat.toFixed(5)+', '+foco.lon.toFixed(5) : '—');
 const acc = gpsFix ? Math.round(p.acc||0) : null;
 const gpsNote = gpsFix ? ('±'+acc+' m'+(foco?' · '+foco.hacienda+' / '+foco.lote:'')) : 'SIN fijar GPS · centro del foco satelital';
 // Sin default sesgado: 'Media'/20%/'Si' preseleccionados empujan la respuesta. En
 // modo ciego ademas no se pregunta por la coincidencia con el satelite — el tecnico
 // no vio el aviso, y preguntarlo se lo revela.
 const st={sev:null,inc:null,coin:null,photo:null,nde:null};
 // AVISO DE SESGO: el umbral MIP esta definido sobre muestreo REPRESENTATIVO del
 // lote (Embrapa 6-10 puntos por lote; AAPRESID 1 estacion cada 10-15 ha). Este
 // conteo se toma parado DENTRO del foco, o sea en el peor sitio: compararlo con
 // el umbral sobreestima la infestacion y empuja a aplicar de mas.
 // El umbral deja de ser una opinion: si la ficha tiene reglas computables, el
 // veredicto lo CALCULA umbral.js a partir del conteo, la unidad y el contexto
 // declarado. El control de 3 botones solo sobrevive donde NO hay umbral establecido,
 // y ahi queda rotulado como criterio del tecnico, que es lo que realmente es.
 const uUnidades = (window.Umbral && isPlaga) ? Umbral.unidadesDe(f.id) : [];
 const uComputable = uUnidades.length > 0;
 // claves de contexto que las reglas de ESTA ficha necesitan (fase / destino / material)
 const uCtxKeys = [];
 if(uComputable){
  const tab=((window.PIXDATA&&PIXDATA.umbrales&&PIXDATA.umbrales.umbrales)||{})[f.id]||{};
  (tab.reglas||[]).forEach(r=>Object.keys(r.condicion||{}).forEach(k=>{ if(uCtxKeys.indexOf(k)<0) uCtxKeys.push(k); }));
 }
 const CTX_LABEL={fase:'Estadio del cultivo',destino:'Destino del lote',material:'Material genético'};
 function ctxOpciones(k){
  const tab=((window.PIXDATA&&PIXDATA.umbrales&&PIXDATA.umbrales.umbrales)||{})[f.id]||{};
  const vals=[]; (tab.reglas||[]).forEach(r=>{ const v=(r.condicion||{})[k]; if(v && vals.indexOf(v)<0) vals.push(v); });
  return vals;
 }
 const ctxHtml = uCtxKeys.map(k=>`<div style="padding:0 9px 8px"><div class="lbl" style="margin-bottom:5px;font-size:11px">${esc(CTX_LABEL[k]||k)}</div><select id="ctx-${esc(k)}" style="width:100%"><option value="">— elegir —</option>${ctxOpciones(k).map(v=>`<option value="${esc(v)}">${esc(String(v).replace(/_/g,' '))}</option>`).join('')}</select></div>`).join('');
 const nde = !isPlaga ? '' : `<div class="field"><div class="lbl" style="margin-bottom:6px">Nivel de acción (MIP)</div><div class="ndebox"><div class="ndh">${esc(f.umbral_accion||'Sin umbral definido — VERIFICAR_LOCAL')}</div>`
  + `<div class="sub" style="font-size:10.5px;padding:0 9px 6px">⚠ Este conteo es <b>dirigido</b> (estás parado en el foco). El umbral MIP se define sobre muestreo <b>representativo</b> del lote: <b>no decidas la aplicación con este número</b> — confirmá en las estaciones fijas.</div>`
  + (uComputable ? ctxHtml
     : `<div class="sub" style="font-size:10.5px;padding:0 9px 6px"><b>Sin umbral computable para esta plaga.</b> Lo de abajo es tu criterio, no un cálculo.</div><div class="segbar" data-g="nde" style="padding:9px;gap:6px"><div class="seg" data-v="under">Por debajo</div><div class="seg" data-v="at">En el umbral</div><div class="seg" data-v="over">Lo supera</div></div>`)
  + `<div id="ndeOut"></div></div></div>`;
 const wrap=document.createElement('div'); wrap.className='scrim';
 wrap.innerHTML=`<div class="sheet"><div class="grab"></div>
  <div><div class="eyebrow" style="margin-bottom:6px">Captura de validación</div><h2 class="vh" style="font-size:17px">${esc(f.nombre_comun)}</h2><div class="sub">${esc(f.nombre_cientifico)} · ${esc(est)}</div></div>
  <div class="gpsbox${gpsFix?'':' nogps'}">${gpsFix?IC.pin:IC.alert}<span>${esc(coord)} · ${esc(gpsNote)}</span></div>
  ${nde}
  <div class="field"><div class="lbl" style="margin-bottom:6px">Severidad in situ</div><div class="segbar" data-g="sev">${['Baja','Media','Alta','Muy alta'].map(x=>`<div class="seg ${x==='Media'?'on':''}" data-v="${x}">${x}</div>`).join('')}</div></div>
  <div class="field"><div class="lbl" style="margin-bottom:6px">% de incidencia (plantas afectadas) · <b id="pv" style="font-family:var(--mono)">20%</b></div><input type="range" min="0" max="100" value="20" id="pct"></div>
  <div class="field"><div class="lbl" style="margin-bottom:6px">¿Coincide con el aviso del satélite?</div><div class="segbar" data-g="coin">${['Sí','Parcial','No'].map(x=>`<div class="seg ${x==='Sí'?'on':''}" data-v="${x}">${x}</div>`).join('')}</div></div>
  <div class="field"><div class="lbl" style="margin-bottom:6px">Conteo medido <span class="sub" style="font-weight:400">— la unidad del protocolo MIP (nº/m, nº/planta, % de plantas)</span></div>
   <div style="display:flex;gap:8px"><input type="text" inputmode="decimal" id="cnt" placeholder="valor" style="flex:1">
    ${uComputable
      ? `<select id="cntu" style="flex:2"><option value="">— unidad —</option>${uUnidades.map(u=>`<option value="${esc(u.clave)}">${esc(u.label)}</option>`).join('')}</select>`
      : `<input type="text" id="cntu" placeholder="unidad (ej. lagartas/m)" style="flex:2">`}</div>
   <div class="sub" style="font-size:10.5px;margin-top:4px">${uComputable
      ? 'La unidad se elige de la lista porque el umbral está definido en esa unidad: comparar unidades distintas no significa nada.'
      : 'Sin el conteo, el umbral MIP no se puede recalcular: queda como opinión, no como medición.'}</div></div>
  <div class="field"><div class="lbl" style="margin-bottom:6px">Observación (opcional)</div><textarea id="obsv" rows="2" placeholder="Distribución, bordadura, reincidencia…"></textarea></div>
  <div class="field"><div class="lbl" style="margin-bottom:6px">Foto georreferenciada <span class="req">*</span></div><div id="shotArea"></div></div>
  <input type="file" accept="image/*" capture="environment" id="fileIn" style="display:none">
  <div style="display:flex;gap:8px"><button class="btn ghost" id="v-c" style="flex:1">Cancelar</button><button class="btn lima big" id="v-s" style="flex:2" disabled>${IC.check} Guardar</button></div>
  <div class="sub" style="text-align:center;font-size:10.5px">La foto es obligatoria para corroborar el diagnóstico.</div></div>`;
 $('#app').appendChild(wrap);
 const save=wrap.querySelector('#v-s'), refresh=()=>save.disabled=!st.photo;
 // camera area
 const shotArea=wrap.querySelector('#shotArea');
 function shotIdle(){shotArea.innerHTML=`<button class="btn ghost block" id="camBtn">${IC.camera} Tomar foto</button>`;wrap.querySelector('#camBtn').onclick=startCam;}
 function startCam(){
  if(!(navigator.mediaDevices&&navigator.mediaDevices.getUserMedia)){wrap.querySelector('#fileIn').click();return;}
  navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}}).then(str=>{camStream=str;
   shotArea.innerHTML=`<div class="shot"><video id="vid" autoplay playsinline muted></video></div><div class="shotbtns" style="margin-top:8px"><button class="btn ghost" id="camCancel" style="flex:1">Cancelar</button><button class="btn brand" id="camShot" style="flex:2">${IC.camera} Capturar</button></div>`;
   const v=wrap.querySelector('#vid'); v.srcObject=str;
   wrap.querySelector('#camCancel').onclick=()=>{stopCam();shotIdle();};
   wrap.querySelector('#camShot').onclick=()=>{const cv=document.createElement('canvas');cv.width=v.videoWidth||640;cv.height=v.videoHeight||480;cv.getContext('2d').drawImage(v,0,0,cv.width,cv.height);st.photo=cv.toDataURL('image/jpeg',0.7);stopCam();showShot();};
  }).catch(()=>{wrap.querySelector('#fileIn').click();});
 }
 function showShot(){shotArea.innerHTML=`<div class="shot"><img src="${st.photo}" alt="foto"></div><button class="btn ghost block" id="reshot" style="margin-top:8px">${IC.camera} Volver a tomar</button>`;wrap.querySelector('#reshot').onclick=()=>{st.photo=null;refresh();shotIdle();};refresh();}
 wrap.querySelector('#fileIn').onchange=e=>{const file=e.target.files&&e.target.files[0];if(!file)return;const rd=new FileReader();rd.onload=()=>{st.photo=rd.result;showShot();};rd.readAsDataURL(file);};
 shotIdle();
 // segmented controls
 wrap.querySelectorAll('.segbar').forEach(bar=>{const g=bar.dataset.g;bar.querySelectorAll('.seg').forEach(s=>s.onclick=()=>{bar.querySelectorAll('.seg').forEach(o=>o.classList.remove('on','crit','alta','baja'));s.classList.add('on');st[g]=s.dataset.v;
  if(g==='nde'){const out=wrap.querySelector('#ndeOut'),v=s.dataset.v;
   if(v==='over'){s.classList.add('crit');out.innerHTML=`<div class="ndverdict over">${IC.alert} Supera el nivel de acción → intervención justificada (MIP primero)</div>`;}
   else if(v==='at'){s.classList.add('alta');out.innerHTML=`<div class="ndverdict at">${IC.clock} En el umbral → re-monitorear en 2–3 días</div>`;}
   else{s.classList.add('baja');out.innerHTML=`<div class="ndverdict under">${IC.check} Por debajo → no tratar, seguir monitoreando</div>`;}}});});
 // --- veredicto CALCULADO del umbral (reemplaza la opinion cuando hay reglas) ---
 st.umbral=null;
 function ctxActual(){
  const c={tipo_muestreo:'dirigido_satelital'};
  uCtxKeys.forEach(k=>{ const el=wrap.querySelector('#ctx-'+k); if(el&&el.value) c[k]=el.value; });
  return c;
 }
 function recalcUmbral(){
  if(!uComputable) return;
  const out=wrap.querySelector('#ndeOut'); if(!out) return;
  const raw=(wrap.querySelector('#cnt').value||'').trim().replace(',','.');
  const uni=(wrap.querySelector('#cntu').value||'').trim();
  const v=Umbral.evaluar(f.id, (raw!==''&&isFinite(+raw))?+raw:null, uni||null, ctxActual());
  st.umbral=v;
  // El color NO se decide por 'supera' a secas: con muestreo dirigido nunca se pinta
  // como una orden de aplicar, porque el numero no es comparable con el MIP.
  const cls = v.estado==='supera' ? 'over'
            : v.estado==='referencia_supera' ? 'at'
            : (v.estado==='por_debajo'||v.estado==='referencia_por_debajo') ? 'under' : '';
  const ico = v.estado==='supera' ? IC.alert : (v.calculado? (cls==='under'?IC.check:IC.clock) : IC.alert);
  let txt=esc(Umbral.resumen(v));
  if(v.calculado && v.regla){
   txt += ' <span style="opacity:.85">(medido '+esc(raw)+' vs umbral '+esc(v.regla.operador)+' '+esc(String(v.regla.valor))+' '+esc(v.regla.unidad_label)+')</span>';
  }
  const detalle = [v.motivo].concat(v.advertencias||[]).filter(Boolean)
    .map(a=>'<div style="font-size:10.5px;opacity:.9;margin-top:3px">· '+esc(a)+'</div>').join('');
  const fuente = v.fuente ? '<div style="font-size:10px;opacity:.75;margin-top:4px">Fuente: '+esc(v.fuente)+(v.calibrado_en?' · calibrado en '+esc(v.calibrado_en):'')+'</div>' : '';
  out.innerHTML = '<div class="ndverdict '+cls+'">'+(ico||'')+' '+txt+'</div><div style="padding:0 9px 9px">'+detalle+fuente+'</div>';
 }
 if(uComputable){
  wrap.querySelector('#cnt').addEventListener('input', recalcUmbral);
  wrap.querySelector('#cntu').addEventListener('change', recalcUmbral);
  uCtxKeys.forEach(k=>{ const el=wrap.querySelector('#ctx-'+k); if(el) el.addEventListener('change', recalcUmbral); });
  recalcUmbral();
 }
 const pct=wrap.querySelector('#pct'),pv=wrap.querySelector('#pv');pct.oninput=()=>{pv.textContent=pct.value+'%';st.inc=+pct.value;};
 function close(){stopCam();wrap.remove();}
 wrap.querySelector('#v-c').onclick=close;
 wrap.onclick=e=>{if(e.target===wrap)close();};
 save.onclick=async()=>{
  // Teclado es-BO/pt-BR usa COMA decimal. Con <input type=number>, '2,5' devuelve ''
  // y el conteo se guardaba como null sin avisar — justo el campo del que depende
  // que `supera_umbral` sea un calculo y no una opinion.
  const cntRaw=(wrap.querySelector('#cnt').value||'').trim().replace(',','.');
  const cnt=(cntRaw!=='' && isFinite(+cntRaw)) ? cntRaw : '';
  const cntu=(wrap.querySelector('#cntu').value||'').trim();
  const v={focoId:foco?foco.id:null,
   // identidad y contexto del aviso: sin esto el registro no se puede cruzar contra
   // el mapa que lo origino, y la precision del motor queda sin numerador
   focoIdEstable:!!(foco&&foco.idEstable), estrato:foco?foco.estrato:null,
   hacienda:foco?foco.hacienda:null, lote:foco?foco.lote:null, fechaImg:foco?foco.fechaImg:null,
   hallazgo:f.categoria||'otro',
   // El cultivo sale de la FICHA que se esta registrando. El fallback duro a 'soya'
   // hacia que una roya de trigo abierta desde el Banco se guardara como Soya.
   cultivo:(D.cultivos[cultivoFicha||(wiz&&wiz.cultivo)]||{}).label||cultivoFicha||(wiz&&wiz.cultivo)||null,
   fichaId:f.id,categoria:f.categoria,
   nombre:f.nombre_comun,cientifico:f.nombre_cientifico,estadio:est,severidad:st.sev,incidencia:st.inc,
   conteo:cnt===''?null:+cnt, conteo_unidad:cntu||null,
   observacion:(wrap.querySelector('#obsv').value||'').trim(),
   umbral_texto:f.umbral_accion||null, umbral_fuente:f.fuente_umbral||null,
   // dirigido = el satelite eligio el sitio (peor punto del lote). El umbral MIP
   // esta calibrado sobre muestreo representativo: este conteo NO es comparable
   // con el, y marcarlo es lo que evita que el producto empuje a sobre-aplicar.
   tipo_muestreo:'dirigido_satelital',
   coincide:st.coin,nde:st.nde,coord,acc,gps_real:gpsFix,foto:st.photo,
   // `supera_umbral` ahora es un CALCULO, no el boton que aprieta el tecnico (Puerta 3.2).
   // Vale null cuando no se pudo calcular, y `umbral_estado` dice por que. Nunca se
   // rellena por descarte: no poder calcular no es "no supera".
   supera_umbral: st.umbral ? st.umbral.supera_umbral : null,
   umbral_estado: st.umbral ? st.umbral.estado : null,
   umbral_calculado: st.umbral ? !!st.umbral.calculado : false,
   // Con el punto elegido por el satelite el conteo NO es comparable con el MIP.
   // Sin esta bandera, un analisis mezclaria conteos dirigidos con representativos
   // y concluiria que hace falta aplicar mas de lo que hace falta.
   umbral_comparable_mip: st.umbral ? !!st.umbral.comparable_con_mip : false,
   umbral_regla: (st.umbral && st.umbral.regla) ? JSON.stringify(st.umbral.regla) : null,
   tecnico:(SESSION?(SESSION.nombre||SESSION.username):'campo'),cliente:(SESSION?SESSION.cliente:'')};
  try{ await Store.saveValidacion(v); }catch(e){}
  close();
  const extra=(isPlaga&&st.nde==='over')?' Supera el nivel de acción: acción recomendada con criterio MIP.':'';
  toast('Validación guardada offline.'+extra+' Realimenta el motor de anomalías.');
  updateSync(); Store.syncNow().then(updateSync);
 };
}

/* ===== BANCO ===== */
function renderBanco(){
 // P0: sin esto, `wiz` sigue apuntando al ultimo foco navegado y el registro sale
 // estampado con la identidad de OTRO foco — justo el dato con el que se mide la
 // precision del motor. Y el cultivo caia al fallback 'soya'.
 wiz=null;
 nav='banco'; teardownMap(); crumb('Banco de conocimiento'); setTab();
 const ks=Object.keys(D.cultivos);
 main().innerHTML=`<div class="view"><div class="eyebrow">${IC.grid} Referencia · por cultivo</div>
  <h2 class="vh">Banco de enfermedades, plagas y carencias</h2>
  <p class="sub">${D.stats.fichas} fichas en ${ks.length} cultivos · ${D.stats.umbrales} umbrales MIP con fuente · ${D.stats.fotos} fotos con licencia · ${Dx.ABIOTICO.length} causas abióticas.</p>
  <div class="cropgrid">${ks.map(k=>`<div class="cropcard" data-k="${k}"><span class="cemoji">${CROP_EMOJI[k]||'🌿'}</span><b>${esc(D.cultivos[k].label)}</b><small>${D.cultivos[k].fichas.length} fichas</small></div>`).join('')}</div></div>`;
 main().querySelectorAll('.cropcard').forEach(el=>el.onclick=()=>renderBancoList(el.dataset.k));
}
function renderBancoList(k){
 wiz=null;
 nav='banco'; teardownMap(); const c=D.cultivos[k]; crumb(c.label); setTab();
 bancoSel={cultivo:k,filtro:bancoSel&&bancoSel.cultivo===k?bancoSel.filtro:'todas'};
 const cats=[['todas','Todas'],['enfermedad','Enf.'],['plaga','Plagas'],['carencia','Carencias']];
 const draw=()=>{const fl=bancoSel.filtro;return c.fichas.filter(f=>fl==='todas'||f.categoria===fl).map(f=>{const s=sevC(f.severidad_potencial);return `<div class="brow" data-id="${f.id}"><span class="bdot" style="background:${CAT_COL[f.categoria]}"></span><span class="bt"><b>${esc(f.nombre_comun)}</b><i>${esc(f.nombre_cientifico)}</i></span><span class="chip ${s}">${SEVL[f.severidad_potencial]}</span><span class="bgo">${IC.chevron}</span></div>`;}).join('');};
 main().innerHTML=`<div class="view"><div style="display:flex;gap:9px"><button class="btn ghost block" id="b-b">${IC.back} Cultivos</button></div>
  <h2 class="vh">${CROP_EMOJI[k]||'🌿'} ${esc(c.label)}</h2>
  <div class="filterbar">${cats.map(([v,l])=>`<button class="fpill ${bancoSel.filtro===v?'on':''}" data-f="${v}">${l}</button>`).join('')}</div>
  <div id="bl" style="display:flex;flex-direction:column;gap:9px">${draw()}</div>
  <button class="btn brand big block" id="b-diag">${IC.compass} Diagnosticar en ${esc(c.label)}</button></div>`;
 $('#b-b').onclick=renderBanco;
 $('#b-diag').onclick=()=>startWizardBanco(k);
 const bind=()=>main().querySelectorAll('.brow').forEach(el=>el.onclick=()=>renderFicha(el.dataset.id,'banco'));
 main().querySelectorAll('.fpill').forEach(el=>el.onclick=()=>{bancoSel.filtro=el.dataset.f;main().querySelectorAll('.fpill').forEach(p=>p.classList.toggle('on',p.dataset.f===bancoSel.filtro));$('#bl').innerHTML=draw();bind();});
 bind();
}

/* ===== HISTORIAL ===== */
async function renderHistorial(){
 nav='hist'; teardownMap(); crumb('Mis validaciones'); setTab();
 let vs=[]; try{vs=await Store.allValidaciones();}catch(e){}
 vs.sort((a,b)=>(b.created||'').localeCompare(a.created||''));
 const pend=vs.filter(v=>!v.synced).length;
 main().innerHTML=`<div class="view"><div class="eyebrow">${IC.list} Registro de campo</div>
  <h2 class="vh">${vs.length} validacion${vs.length!==1?'es':''}</h2>
  <p class="sub">${pend} pendiente${pend!==1?'s':''} de sincronizar · guardadas en el dispositivo (offline-first).</p>
  ${vs.length?vs.map(v=>{const s=sevC({Baja:'baja',Media:'media',Alta:'alta','Muy alta':'muy_alta'}[v.severidad]||'media');return `<div class="histrow"><span class="hi" style="background:${CAT_COL[v.categoria]||'var(--brand)'}">${CAT_ICON[v.categoria]||IC.check}</span><span class="ht"><b>${esc(v.nombre)}</b><span>${esc(v.cultivo||'')} · ${esc(v.estadio||'')} · ${esc(v.severidad)} · ${esc((v.created||'').slice(0,16).replace('T',' '))}</span></span><span class="chip ${v.synced?'baja':'alta'}">${v.synced?'sync':'pend'}</span></div>`;}).join(''):`<div class="empty">Todavía no registraste validaciones.<br>Diagnosticá un foco y confirmá el hallazgo.</div>`}
  ${vs.length&&pend?`<button class="btn brand big block" id="h-sync">${IC.sync} Sincronizar ${pend} pendiente${pend!==1?'s':''}</button>`:''}</div>`;
 const b=$('#h-sync'); if(b) b.onclick=async()=>{toast('Sincronizando…');const r=await Store.syncNow();updateSync();toast(r.sent?('Sincronizadas '+r.sent+' validaciones.'):'Sin conexión o sin backend configurado — quedan en cola segura.');renderHistorial();};
}

/* ===== LOGIN / CUENTA / USUARIOS ===== */
const gate=()=>$('#gate');
function showChrome(on){document.querySelector('.appbar').style.display=on?'':'none';$('#tabbar').style.display=on?'':'none';document.querySelectorAll('.statusbar .gps,.statusbar .syncpill').forEach(e=>e.style.visibility=on?'':'hidden');}
function pwdField(id,ph){return `<div class="pwd"><input class="inp" id="${id}" type="password" autocomplete="current-password" placeholder="${ph||''}"><button class="peek" type="button" data-peek="${id}" aria-label="Ver">${IC.eye}</button></div>`;}
function bindPeek(root){root.querySelectorAll('.peek').forEach(b=>b.onclick=()=>{const i=root.querySelector('#'+b.dataset.peek);i.type=i.type==='password'?'text':'password';});}
function gerr(msg){const e=gate().querySelector('#gerr');if(e){e.innerHTML=IC.alert+'<span>'+esc(msg)+'</span>';e.style.display='flex';}}

async function boot(){
 const params=new URLSearchParams(location.search);
 // Atajos de captura SOLO en modo desarrollo (no saltan auth en producción).
 if(CFG.DEV_MODE){ const demo=params.get('demo'); if(demo) return runDemo(demo); }
 // Cargar un GeoJSON de anomalías. NO saltea el login: se muestra tras autenticarse.
 const load=params.get('load');
 if(load){ try{ await loadFocosGeojson(load); }catch(e){ LOADED_FOCI=null; FOCOS_ERROR=e.message; } }
 // Contexto seguro requerido para el login cifrado (crypto.subtle).
 if(CFG.AUTH.REQUIRE && !Auth.available()){
   gate().hidden=false; showChrome(false);
   gate().innerHTML='<div class="gwrap"><div class="glogo"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"><path d="M12 21s-7-5.2-7-11a7 7 0 0 1 14 0c0 5.8-7 11-7 11Z"/><circle cx="12" cy="10" r="2.4"/></svg></div><h1>Contexto no seguro</h1><p class="gsub">El login cifrado necesita HTTPS. Abrí PIX Scout desde el APK instalado (no como archivo suelto).</p></div>';
   return;
 }
 SESSION = await Auth.session();
 if(!CFG.AUTH.REQUIRE){ SESSION=SESSION||{username:'campo',nombre:'Campo',role:'tecnico'}; return enterApp(); }
 if(SESSION) return enterApp();
 const has = await Auth.hasUsers();
 gate().hidden=false; showChrome(false);
 has ? renderLogin() : renderCreateAdmin();
}

/* Modo demo para capturas (solo con ?demo=; inerte en producción) */
async function runDemo(screen){
 SESSION={username:'nilton',nombre:'Nilton Camargo',cliente:'Cerro Alto',role:'admin'};
 const F=D.focos;
 const setWiz=o=>{wiz=Object.assign({foco:null,cultivo:'soya',estadio:'Vegetativo',patron:null,host:'no',temporal:'gradual',signo:null,signoCat:null,fork:null,branch:null,step:0,fromBanco:false},o);};
 if(screen==='login'){ gate().hidden=false; showChrome(false); return renderCreateAdmin(); }
 gate().hidden=true; showChrome(true);
 try{
  if(screen==='focos'){ focosMode='lista'; return renderFocos(); }
  if(screen==='mapa'){ const t=F[4]; Geo.current=()=>({lat:t.lat+0.0007,lon:t.lon-0.0005,acc:6}); Geo.heading=()=>40; focosMode='mapa'; renderFocos(); setTimeout(()=>{ if(mapInst){ mapInst.centerOn(t.lat,t.lon,700); mapInst.setUser({lat:t.lat+0.0007,lon:t.lon-0.0005,acc:6},40); mapInst.select(t.id); onFocoTap(t); } },450); return; }
  if(screen==='nav'){ const t=F[4]; Geo.current=()=>({lat:t.lat+0.0009,lon:t.lon+0.0006,acc:4}); Geo.heading=()=>28; return renderNav(t); }
  if(screen==='contexto'){ return startWizardFoco(F[4]); }
  if(screen==='signo'){ startWizardFoco(F[0]); wiz.step=2; return renderWizard(); }
  if(screen==='results'){ setWiz({foco:F[4],cultivo:F[4].cultivo,estadio:F[4].estadio,patron:'relieve',host:'si',temporal:'gradual',signo:'ninguno',signoCat:'indef',fork:'abiotico',step:4}); return renderResults(); }
  if(screen==='ficha'){ setWiz({foco:F[3],cultivo:F[3].cultivo}); return renderFicha('maiz-cogollero','banco'); }
  if(screen==='validacion'){ setWiz({foco:F[3],cultivo:F[3].cultivo,estadio:'Vegetativo'}); const r=Dx.findFicha('maiz-cogollero'); openValidacion(r.f); const seg=document.querySelector('.segbar[data-g="nde"] .seg[data-v="over"]'); if(seg) seg.click(); return; }
  if(screen==='historial'){ try{await Store.saveValidacion({focoId:'F-2607-P9',cultivo:'Pastura',nombre:'Anegamiento / asfixia radicular',categoria:'abiotico',estadio:'Vegetativo',severidad:'Alta',incidencia:35,coincide:'Sí',coord:'-14.90190, -55.43950',tecnico:'Nilton Camargo',synced:false}); await Store.saveValidacion({focoId:'F-2607-P3',cultivo:'Maíz',nombre:'Gusano cogollero',categoria:'plaga',estadio:'Vegetativo',severidad:'Media',incidencia:22,coincide:'Parcial',coord:'-13.25540, -46.88910',tecnico:'Nilton Camargo',nde:'over',synced:true});}catch(e){} return renderHistorial(); }
  if(screen==='users'){ try{await Auth.createUser({username:'jose.campo',password:'x123',nombre:'José Pérez',cliente:'Cerro Alto',role:'tecnico'}); await Auth.createUser({username:'maria.tec',password:'x123',nombre:'María López',cliente:'São Francisco',role:'tecnico'});}catch(e){} return renderUsers(); }
  if(screen==='banco'){ return renderBancoList('trigo'); }
 }catch(e){ document.getElementById('main').innerHTML='<div class="view"><p>demo error: '+esc(e.message)+'</p></div>'; }
 return renderFocos();
}
async function enterApp(){ gate().hidden=true; showChrome(true); updateSync();
 if(CFG.DEFAULT_FOCOS && !LOADED_FOCI){
   try{ await loadFocosGeojson(CFG.DEFAULT_FOCOS); }
   catch(e){ LOADED_FOCI=null; FOCOS_ERROR=e.message; }
 }   // carga el GeoJSON de anomalías empaquetado
 renderFocos();
}

function renderCreateAdmin(){
 gate().innerHTML=`<div class="gwrap">
  <div class="glogo"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"><path d="M12 21s-7-5.2-7-11a7 7 0 0 1 14 0c0 5.8-7 11-7 11Z"/><circle cx="12" cy="10" r="2.4"/></svg></div>
  <span class="gbadge">Primer arranque</span>
  <h1>Crear administrador</h1>
  <p class="gsub">Definí la cuenta de administrador. Con ella vas a dar de alta a los técnicos que trabajarán a campo.</p>
  <div class="card gform">
   <div id="gerr" class="gerr" style="display:none"></div>
   <div class="fld"><label>Usuario admin</label><input class="inp" id="au" autocomplete="username" placeholder="ej. nilton"></div>
   <div class="fld"><label>Nombre</label><input class="inp" id="an" placeholder="Nombre y apellido"></div>
   <div class="fld"><label>Contraseña</label>${pwdField('ap','mínimo 6 caracteres')}</div>
   <div class="fld"><label>Repetir contraseña</label>${pwdField('ap2','')}</div>
   <button class="btn brand big block" id="ago">${IC.check} Crear administrador</button>
  </div>
  <p class="gfoot">Las contraseñas se guardan cifradas (PBKDF2) en el dispositivo. Funciona sin conexión.</p></div>`;
 bindPeek(gate());
 gate().querySelector('#ago').onclick=async()=>{
  const u=gate().querySelector('#au').value, n=gate().querySelector('#an').value, p=gate().querySelector('#ap').value, p2=gate().querySelector('#ap2').value;
  if(p!==p2) return gerr('Las contraseñas no coinciden.');
  try{ await Auth.createUser({username:u,password:p,nombre:n,role:'admin'}); SESSION=await Auth.login(u,p); enterApp(); toast('Administrador creado. Ya podés dar de alta técnicos desde Cuenta.'); }
  catch(e){ gerr(e.message); }
 };
}
function renderLogin(){
 gate().innerHTML=`<div class="gwrap">
  <div class="glogo"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"><path d="M12 21s-7-5.2-7-11a7 7 0 0 1 14 0c0 5.8-7 11-7 11Z"/><circle cx="12" cy="10" r="2.4"/></svg></div>
  <h1>PIX Scout</h1>
  <p class="gsub">Ingresá con el usuario que te dio tu administrador.</p>
  <div class="card gform">
   <div id="gerr" class="gerr" style="display:none"></div>
   <div class="fld"><label>Usuario</label><input class="inp" id="lu" autocomplete="username" placeholder="usuario"></div>
   <div class="fld"><label>Contraseña</label>${pwdField('lp','contraseña')}</div>
   <button class="btn brand big block" id="lgo">${IC.compass} Ingresar</button>
  </div>
  <p class="gfoot">Sesión offline válida ${CFG.AUTH.OFFLINE_TTL_DAYS} días sin reconectar. Datos cifrados en el dispositivo.</p></div>`;
 bindPeek(gate());
 const submit=async()=>{const u=gate().querySelector('#lu').value,p=gate().querySelector('#lp').value;try{SESSION=await Auth.login(u,p);enterApp();toast('Bienvenido, '+esc(SESSION.nombre||SESSION.username)+'.');}catch(e){gerr(e.message);}};
 gate().querySelector('#lgo').onclick=submit;
 gate().querySelector('#lp').addEventListener('keydown',e=>{if(e.key==='Enter')submit();});
}

function openAccount(){
 const s=SESSION||{}; const admin=s.role==='admin';
 const wrap=document.createElement('div');wrap.className='scrim';
 wrap.innerHTML=`<div class="sheet"><div class="grab"></div>
  <div class="urow" style="box-shadow:none"><span class="ua">${esc((s.nombre||s.username||'?').slice(0,1).toUpperCase())}</span><span class="ut"><b>${esc(s.nombre||s.username||'—')}</b><span>@${esc(s.username||'')} · ${esc(s.cliente||'sin cliente')}</span></span><span class="rolechip ${admin?'admin':'tecnico'}">${admin?'admin':'técnico'}</span></div>
  ${admin?`<button class="btn brand big block" id="ac-users">${IC.grid} Gestionar usuarios</button>`:''}
  <button class="btn ghost block" id="ac-theme">Cambiar tema (claro/oscuro)</button>
  <button class="btn ghost block" id="ac-help">${IC.info} Acerca de PIX Scout</button>
  <button class="btn ghost block" id="ac-logout" style="color:var(--crit)">Cerrar sesión</button></div>`;
 $('#app').appendChild(wrap);
 const close=()=>wrap.remove();
 wrap.onclick=e=>{if(e.target===wrap)close();};
 if(admin) wrap.querySelector('#ac-users').onclick=()=>{close();renderUsers();};
 wrap.querySelector('#ac-theme').onclick=()=>{const r=document.documentElement,c=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');r.setAttribute('data-theme',c==='dark'?'light':'dark');};
 wrap.querySelector('#ac-help').onclick=()=>{close();toast('PIX Scout '+CFG.APP_VERSION+' · offline-first. Diagnóstico presuntivo con confianza honesta; distingue biótico/abiótico/nutricional y escala a laboratorio.');};
 wrap.querySelector('#ac-logout').onclick=async()=>{teardownMap();await Auth.logout();SESSION=null;close();gate().hidden=false;showChrome(false);renderLogin();};
}

async function renderUsers(){
 nav='users'; teardownMap(); crumb('Usuarios');
 let us=[]; try{us=await Auth.listUsers();}catch(e){}
 main().innerHTML=`<div class="view">
  <div style="display:flex;gap:9px"><button class="btn ghost block" id="u-back">${IC.back} Volver</button></div>
  <div class="eyebrow">${IC.grid} Administración</div>
  <h2 class="vh">${us.length} usuario${us.length!==1?'s':''}</h2>
  <p class="sub">Cada técnico entra con su usuario y contraseña. Podés activarlos o desactivarlos para habilitar/bloquear el trabajo a campo.</p>
  <div style="display:flex;flex-direction:column;gap:9px" id="ulist">${us.map(uRow).join('')}</div>
  <div class="card gform" style="margin-top:4px">
   <div class="eyebrow">${IC.check} Dar de alta técnico</div>
   <div id="uerr" class="gerr" style="display:none"></div>
   <div class="fld"><label>Usuario</label><input class="inp" id="nu" placeholder="ej. jose.campo"></div>
   <div class="fld"><label>Nombre del técnico</label><input class="inp" id="nn" placeholder="Nombre y apellido"></div>
   <div class="fld"><label>Cliente / finca</label><input class="inp" id="ncl" placeholder="ej. Cerro Alto"></div>
   <div class="fld"><label>Rol</label><select class="inp" id="nr"><option value="tecnico">Técnico</option><option value="admin">Administrador</option></select></div>
   <div class="fld"><label>Contraseña</label>${pwdField('np','mínimo 6 caracteres')}</div>
   <button class="btn brand big block" id="uadd">${IC.check} Crear usuario</button>
  </div></div>`;
 bindPeek(main());
 $('#u-back').onclick=renderFocos;
 bindUserRows();
 $('#uadd').onclick=async()=>{
  const u=$('#nu').value,n=$('#nn').value,cl=$('#ncl').value,r=$('#nr').value,p=$('#np').value;
  const err=main().querySelector('#uerr');
  try{ await Auth.createUser({username:u,password:p,nombre:n,cliente:cl,role:r}); toast('Técnico '+esc(u.trim().toLowerCase())+' habilitado.'); renderUsers(); }
  catch(e){ err.innerHTML=IC.alert+'<span>'+esc(e.message)+'</span>'; err.style.display='flex'; }
 };
}
function uRow(u){const me=SESSION&&SESSION.username===u.username;
 return `<div class="urow"><span class="ua">${esc((u.nombre||u.username).slice(0,1).toUpperCase())}</span>
  <span class="ut"><b>${esc(u.nombre||u.username)}</b><span>@${esc(u.username)}${u.cliente?' · '+esc(u.cliente):''}</span></span>
  <span class="uacts"><span class="rolechip ${u.role==='admin'?'admin':'tecnico'}">${u.role==='admin'?'admin':'téc'}</span>
  <button class="swpill ${u.activo?'on':'off'}" data-u="${esc(u.username)}" data-act="toggle">${u.activo?'activo':'off'}</button></span></div>`;
}
function bindUserRows(){
 main().querySelectorAll('.swpill[data-act="toggle"]').forEach(b=>b.onclick=async()=>{
  const un=b.dataset.u; const us=await Auth.listUsers(); const u=us.find(x=>x.username===un);
  await Auth.setActivo(un,!u.activo); renderUsers();
 });
}

/* ===== chrome ===== */
function setTab(){document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('on',t.dataset.tab===nav||(nav==='nav'&&t.dataset.tab==='focos')||(nav==='wizard'&&t.dataset.tab==='focos')||(nav==='ficha'&&t.dataset.tab==='focos')));}
function toast(msg){const o=$('.toast');if(o)o.remove();const t=document.createElement('div');t.className='toast';t.innerHTML=IC.check+'<span>'+esc(msg)+'</span>';$('#app').appendChild(t);setTimeout(()=>t.remove(),4600);}
async function updateSync(){let n=0;try{n=(await Store.pending()).length;}catch(e){}const el=$('#syncpill');if(!el)return;el.className='syncpill'+(n?' pend':'');el.innerHTML=IC.sync+(n?('<span>'+n+'</span>'):'<span>sync</span>');}
function updateGpsBar(){const el=$('#gpspill');if(!el)return;const p=Geo.current();if(!Geo.available()){el.className='gps off';el.innerHTML='<span class="gpsdot"></span> GPS n/d';return;}if(!p||p.error){el.className='gps warn';el.innerHTML='<span class="gpsdot"></span> GPS…';return;}el.className='gps ok';el.innerHTML='<span class="gpsdot"></span> ±'+Math.round(p.acc||0)+' m';}

document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{const x=t.dataset.tab;if(x==='focos')renderFocos();else if(x==='banco')renderBanco();else if(x==='hist')renderHistorial();});
$('#sunBtn').onclick=()=>{$('#app').classList.toggle('sun');$('#sunBtn').classList.toggle('act');};
$('#themeBtn').onclick=()=>{const r=document.documentElement,c=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');r.setAttribute('data-theme',c==='dark'?'light':'dark');};
$('#acctBtn').onclick=openAccount;
$('#syncpill').onclick=async()=>{toast('Sincronizando…');const r=await Store.syncNow();updateSync();toast(r.sent?('Sincronizadas '+r.sent+'.'):'Sin conexión/backend — cola segura.');};

// install
let deferredPrompt=null;
window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();deferredPrompt=e;const b=document.createElement('button');b.className='btn brand installbtn';b.id='installBtn';b.innerHTML=IC.download+' Instalar PIX Scout';b.onclick=()=>{deferredPrompt.prompt();deferredPrompt=null;b.remove();};$('#app').appendChild(b);});

// GPS status heartbeat
Geo.onPos(updateGpsBar); setInterval(updateGpsBar,2000); updateGpsBar();
window.addEventListener('online',()=>Store.syncNow().then(updateSync));
boot();
})();
