/* PIX Scout — importar el mapa de focos desde un archivo del teléfono.

   EL CANAL REAL ES WHATSAPP. El administrador baja el GeoJSON de la corrida y se lo
   manda al cliente por WhatsApp; el técnico lo abre con la app. No hace falta ninguna
   URL publica, ni exponer coordenadas de campos de clientes en internet.

   Hasta ahora la app solo podia usar el GeoJSON EMPAQUETADO dentro del APK, asi que
   cambiar de campo obligaba a recompilar y reinstalar. Con esto, el tecnico recibe el
   archivo y lo abre.

   LO QUE NO HACE, A PROPOSITO
   ---------------------------
   No reemplaza el mapa activo en silencio. Primero dice QUE trae el archivo (campo,
   fecha de escena, cuantos lotes) y recien despues pregunta. Un tecnico que sale al
   campo con el mapa equivocado sin haberse enterado es peor que uno sin mapa.
*/
window.Importar = (function(){
  const CACHE = 'pixscout-focos';       // la misma que usa la descarga por red
  const CLAVE_ACTIVO = 'focos_importado';

  function _num(gj, pred){
    return (gj.features||[]).filter(pred).length;
  }

  /* Mira el archivo y dice si es uno nuestro y que trae. NO lo aplica. */
  function inspeccionar(texto){
    let gj;
    try{
      gj = JSON.parse(texto);
    }catch(e){
      return {ok:false, motivo:'El archivo no es un GeoJSON válido (no se pudo leer).'};
    }
    if(!gj || gj.type!=='FeatureCollection' || !Array.isArray(gj.features)){
      return {ok:false, motivo:'No parece un mapa de focos: falta la lista de features.'};
    }
    const focos = (window.GeoLoad ? GeoLoad.fociFromGeoJSON(gj, {}) : []);
    if(!focos.length){
      return {ok:false, motivo:'El archivo no tiene ningún lote con polígono. '
              + '¿Seguro que es el mapa de focos y no otra cosa?'};
    }
    // Datos para que el tecnico confirme que es SU campo y de esta semana.
    let hacienda=null, fecha=null;
    for(const f of gj.features){
      const p=f.properties||{};
      if(!hacienda && p.hacienda) hacienda=p.hacienda;
      if(p.fecha_img && (!fecha || p.fecha_img>fecha)) fecha=p.fecha_img;
    }
    const sinId = focos.filter(f=>!f.idEstable).length;
    return {ok:true, gj, texto, focos:focos.length, hacienda, fecha,
            perimetro:_num(gj, f=>((f.properties||{}).tipo||'')==='perimetro'),
            // Sin id estable lo que registre el tecnico no se puede rastrear al lote.
            aviso: sinId ? sinId+' lote(s) sin identificador estable: lo que registres '
                           +'ahí no se va a poder cruzar con el informe.' : null};
  }

  /* Guarda el archivo para que sobreviva a cerrar la app y funcione sin señal. */
  async function guardar(nombre, texto){
    const c = await caches.open(CACHE);
    await c.put('focos/'+nombre, new Response(texto,
      {headers:{'Content-Type':'application/json'}}));
    try{ await Store.setMeta(CLAVE_ACTIVO, {nombre, cuando:new Date().toISOString()}); }
    catch(e){}
  }

  async function activo(){
    try{ return await Store.getMeta(CLAVE_ACTIVO); }catch(e){ return null; }
  }

  async function leerGuardado(nombre){
    try{
      const c = await caches.open(CACHE);
      const r = await c.match('focos/'+nombre);
      return r ? await r.json() : null;
    }catch(e){ return null; }
  }

  async function olvidar(){
    try{ await Store.setMeta(CLAVE_ACTIVO, null); }catch(e){}
  }

  return { inspeccionar, guardar, activo, leerGuardado, olvidar, CACHE, CLAVE_ACTIVO };
})();
