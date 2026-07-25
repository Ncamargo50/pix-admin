/* PIX Scout — autenticación offline-first.
   Verificación LOCAL con PBKDF2 (Web Crypto): nunca se guarda la contraseña en texto.
   Modelo: el ADMIN da de alta usuarios (usuario+contraseña); el técnico entra con esas credenciales.
   Funciona 100% sin señal. El modo Supabase (multi-dispositivo) es opcional y va documentado. */
window.Auth = (function(){
  const A = window.PIXCONFIG.AUTH;
  const enc = new TextEncoder();
  const hex = buf => Array.from(new Uint8Array(buf)).map(b=>b.toString(16).padStart(2,'0')).join('');
  const unhex = h => new Uint8Array(h.match(/.{1,2}/g).map(x=>parseInt(x,16)));

  function randSalt(){ const s=new Uint8Array(16); crypto.getRandomValues(s); return hex(s); }
  async function derive(pw, saltHex, iters){
    const key = await crypto.subtle.importKey('raw', enc.encode(pw), 'PBKDF2', false, ['deriveBits']);
    const bits = await crypto.subtle.deriveBits({name:'PBKDF2', salt:unhex(saltHex), iterations:iters||A.PBKDF2_ITERS, hash:'SHA-256'}, key, 256);
    return hex(bits);
  }
  async function makeHash(pw){ const salt=randSalt(); const h=await derive(pw,salt); return {salt,hash:h,iters:A.PBKDF2_ITERS}; }
  async function check(pw, rec){ if(!rec) return false; const h=await derive(pw, rec.salt, rec.iters); return timingSafeEq(h, rec.hash); }
  function timingSafeEq(a,b){ if(a.length!==b.length) return false; let r=0; for(let i=0;i<a.length;i++) r|=a.charCodeAt(i)^b.charCodeAt(i); return r===0; }

  const norm = u => (u||'').trim().toLowerCase();

  async function hasUsers(){ return (await Store.allUsers()).length>0; }
  async function listUsers(){ return (await Store.allUsers()).sort((a,b)=>a.username.localeCompare(b.username)); }

  // Crea usuario (usado por el admin, o el primer admin en el arranque)
  async function createUser({username, password, nombre, cliente, role}){
    username = norm(username);
    const minp = A.MIN_PASSWORD || 6;
    if(!username || username.length<3) throw new Error('Usuario mínimo 3 caracteres.');
    if(!password || password.length<minp) throw new Error('Contraseña mínimo '+minp+' caracteres.');
    if(await Store.getUser(username)) throw new Error('Ese usuario ya existe.');
    const h = await makeHash(password);
    const rec = {username, salt:h.salt, hash:h.hash, iters:h.iters, nombre:nombre||'', cliente:cliente||'', role:role||'tecnico', activo:true, created:new Date().toISOString()};
    await Store.putUser(rec);
    return pub(rec);
  }
  async function setActivo(username, activo){ const u=await Store.getUser(norm(username)); if(u){ u.activo=!!activo; await Store.putUser(u);} }
  async function resetPassword(username, password){ const u=await Store.getUser(norm(username)); if(!u) throw new Error('Usuario inexistente.'); const h=await makeHash(password); u.salt=h.salt;u.hash=h.hash;u.iters=h.iters; await Store.putUser(u); }
  async function removeUser(username){ await Store.deleteUser(norm(username)); }

  function pub(u){ return {username:u.username, nombre:u.nombre, cliente:u.cliente, role:u.role, activo:u.activo}; }

  // Login: verifica local. (Si hay Supabase configurado, se puede extender a validar online la 1ra vez.)
  async function login(username, password){
    username = norm(username);
    const u = await Store.getUser(username);
    if(!u) throw new Error('Usuario o contraseña incorrectos.');
    if(!u.activo) throw new Error('Usuario deshabilitado. Contactá al administrador.');
    const ok = await check(password, u);
    if(!ok) throw new Error('Usuario o contraseña incorrectos.');
    const now = Date.now();
    const ses = {username:u.username, nombre:u.nombre, cliente:u.cliente, role:u.role, loginAt:now, expiresAt: now + A.OFFLINE_TTL_DAYS*86400000};
    await Store.setMeta('session', ses);
    return ses;
  }
  async function session(){
    if(!A.REQUIRE) return {username:'campo', nombre:'Campo', role:'tecnico', activo:true, expiresAt:Infinity};
    const s = await Store.getMeta('session');
    if(!s) return null;
    if(s.expiresAt && Date.now() > s.expiresAt) return null; // expiró la sesión offline
    // el usuario podría haber sido deshabilitado por el admin en este dispositivo
    const u = await Store.getUser(s.username);
    if(u && u.activo===false) return null;
    return s;
  }
  async function logout(){ await Store.setMeta('session', null); }

  return { hasUsers, listUsers, createUser, setActivo, resetPassword, removeUser, login, session, logout,
           available: ()=> !!(window.crypto && crypto.subtle) };
})();
