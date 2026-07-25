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
    syncing=true; let sent=0;
    try{
      for(const v of q){
        try{
          const ctrl=new AbortController(); const to=setTimeout(()=>ctrl.abort(),15000);
          const r=await fetch(cfg.SUPABASE_URL+'/rest/v1/'+cfg.VALIDACIONES_TABLE+'?on_conflict=id',{
            method:'POST', signal:ctrl.signal,
            headers:{'Content-Type':'application/json','apikey':cfg.SUPABASE_ANON_KEY,
                     'Authorization':'Bearer '+cfg.SUPABASE_ANON_KEY,'Prefer':'return=minimal,resolution=merge-duplicates'},
            body:JSON.stringify(sanitize(v))
          });
          clearTimeout(to);
          if(r.ok){ await markSynced(v.id); sent++; }
          else if(console&&console.warn) console.warn('sync '+v.id+' HTTP '+r.status);
        }catch(e){ /* queda en cola, se reintenta */ }
      }
    } finally { syncing=false; }
    return {sent, queued:(await pending()).length};
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
