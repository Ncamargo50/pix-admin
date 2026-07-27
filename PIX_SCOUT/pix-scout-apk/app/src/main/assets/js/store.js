/* PIX Scout — almacenamiento offline-first (IndexedDB) + cola de sincronización.
   Regla dura del proyecto: NUNCA perder datos. Se guarda local primero; el sync es diferido y
   no destructivo (solo marca synced=true tras confirmación del servidor). */
window.Store = (function(){
  const DB='pixscout', VER=2;
  let db=null;
  function open(){
    return new Promise((res,rej)=>{
      if(db) return res(db);
      const r=indexedDB.open(DB,VER);
      r.onupgradeneeded=e=>{
        const d=e.target.result;
        if(!d.objectStoreNames.contains('validaciones')) d.createObjectStore('validaciones',{keyPath:'id'});
        if(!d.objectStoreNames.contains('tracks')) d.createObjectStore('tracks',{keyPath:'id'});
        if(!d.objectStoreNames.contains('meta')) d.createObjectStore('meta',{keyPath:'k'});
        if(!d.objectStoreNames.contains('users')) d.createObjectStore('users',{keyPath:'username'});
      };
      r.onsuccess=e=>{db=e.target.result;res(db);};
      r.onerror=e=>rej(e.target.error);
    });
  }
  function tx(store,mode){ return open().then(d=>d.transaction(store,mode).objectStore(store)); }
  function req(p){ return new Promise((res,rej)=>{p.onsuccess=()=>res(p.result);p.onerror=()=>rej(p.error);}); }

  function uid(){ return 'v'+Date.now().toString(36)+Math.random().toString(36).slice(2,7); }

  async function saveValidacion(v){
    v.id=v.id||uid(); v.synced=false; v.created=v.created||new Date().toISOString();
    const s=await tx('validaciones','readwrite'); await req(s.put(v)); return v;   // put: idempotente, nunca pierde
  }
  async function allValidaciones(){ const s=await tx('validaciones','readonly'); return req(s.getAll()); }
  async function pending(){ return (await allValidaciones()).filter(v=>!v.synced); }
  async function markSynced(id){
    const sr=await tx('validaciones','readonly'); const v=await req(sr.get(id));   // lectura y escritura en tx separadas (evita auto-commit)
    if(!v) return; v.synced=true; v.syncedAt=new Date().toISOString();
    const sw=await tx('validaciones','readwrite'); await req(sw.put(v));
  }
  async function saveTrack(t){ t.id=t.id||('t'+Date.now().toString(36)); const s=await tx('tracks','readwrite'); await req(s.put(t)); return t; }

  // Sync a Supabase REST si hay config y conexión. No destructivo: solo marca synced.
  let syncing=false;
  function sanitize(v){ const c=Object.assign({},v); delete c.synced; delete c.syncedAt; return c; }  // manda id (PK) + datos, sin flags internos
  async function syncNow(){
    const cfg=window.PIXCONFIG;
    if(syncing) return {sent:0, queued:(await pending()).length, reason:'en_curso'};   // lock: no correr dos syncs a la vez (evita duplicados)
    const q=await pending();
    if(!q.length) return {sent:0,queued:0};
    if(!navigator.onLine || !cfg.SUPABASE_URL || !cfg.SUPABASE_ANON_KEY) return {sent:0,queued:q.length,reason:'offline_o_sin_config'};
    // Los rechazos PERMANENTES se cuentan y se devuelven. Sin esto la app decia
    // "cola segura" ante un 4xx del servidor —esquema o permisos— y el tecnico
    // seguia registrando creyendo que llegaba. Es exactamente por que el 401 del
    // 100% de los POST paso inadvertido: se saco la causa, faltaba sacar la ceguera.
    syncing=true; let sent=0, rechazadas=0, ultimoError='';
    try{
      for(const v of q){
        try{
          const ctrl=new AbortController(); const to=setTimeout(()=>ctrl.abort(),15000);
          // INSERT PELADO, sin `on_conflict` ni `resolution=ignore-duplicates`.
          //
          // MEDIDO contra el proyecto real (2026-07-27): con `resolution=ignore-duplicates`
          // TODO POST da 401 / 42501 "new row violates row-level security policy". No es
          // el WITH CHECK: es que ese Prefer manda a PostgREST por el camino de UPSERT, y
          // un `ON CONFLICT` necesita mirar la fila en conflicto — o sea, policy de SELECT.
          // La tabla no tiene SELECT para anon A PROPOSITO (la clave viaja dentro del APK),
          // asi que RLS niega. El sintoma habria sido el peor posible: el tecnico ve
          // "guardado offline", la cola no se vacia NUNCA, y la campaña termina sin un solo
          // dato de retorno creyendo que no hubo validaciones.
          //
          // La idempotencia del reintento se resuelve abajo, con el 23505, que es donde
          // corresponde: el servidor ya tiene la fila.
          const r=await fetch(cfg.SUPABASE_URL+'/rest/v1/'+cfg.VALIDACIONES_TABLE,{
            method:'POST', signal:ctrl.signal,
            headers:{'Content-Type':'application/json','apikey':cfg.SUPABASE_ANON_KEY,
                     'Authorization':'Bearer '+cfg.SUPABASE_ANON_KEY,'Prefer':'return=minimal'},
            body:JSON.stringify(sanitize(v))
          });
          clearTimeout(to);
          if(r.ok){ await markSynced(v.id); sent++; }
          else {
            const cuerpo=await r.text().catch(()=>'');
            // 409 / 23505 = clave duplicada: el servidor YA TIENE esta validacion. Pasa
            // cuando el POST anterior llego pero la respuesta se perdio (timeout, tunel,
            // el celular que cambia de antena al salir del lote). Es EXITO, no error:
            // tratarlo como fallo dejaria la fila reintentandose para siempre.
            if(r.status===409 && cuerpo.indexOf('23505')>=0){ await markSynced(v.id); sent++; }
            else {
              // Un 4xx que no es 429 no se arregla reintentando: es esquema o permisos.
              // Sin el cuerpo del error, un PGRST204 (columna que no existe) se ve igual
              // que "no hay señal" y la cola se llena en silencio.
              const permanente = r.status>=400 && r.status<500 && r.status!==429;
              if(permanente){ rechazadas++; ultimoError='HTTP '+r.status; }
              if(console&&console.warn) console.warn('sync '+v.id+' HTTP '+r.status+(permanente?' [PERMANENTE, no se arregla solo]':' [reintentable]')+' '+cuerpo.slice(0,300));
            }
          }
        }catch(e){ /* queda en cola, se reintenta */ }
      }
    } finally { syncing=false; }
    return {sent, queued:(await pending()).length, rechazadas, ultimoError};
  }

  // --- usuarios (auth local) ---
  async function putUser(u){ const s=await tx('users','readwrite'); await req(s.put(u)); return u; }
  async function getUser(username){ const s=await tx('users','readonly'); return req(s.get(username)); }
  async function allUsers(){ const s=await tx('users','readonly'); return req(s.getAll()); }
  async function deleteUser(username){ const s=await tx('users','readwrite'); await req(s.delete(username)); }
  // --- meta (sesión, flags) ---
  async function setMeta(k,v){ const s=await tx('meta','readwrite'); await req(s.put({k,v})); }
  async function getMeta(k){ const s=await tx('meta','readonly'); const r=await req(s.get(k)); return r?r.v:null; }

  return { saveValidacion, allValidaciones, pending, markSynced, saveTrack, syncNow, uid,
           putUser, getUser, allUsers, deleteUser, setMeta, getMeta };
})();
