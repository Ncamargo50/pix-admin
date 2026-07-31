/* PIX Scout — cargador de GeoJSON de anomalías (Polygon / MultiPolygon, WGS84).
   Convierte un FeatureCollection en focos con polígono real, centroide, área y severidad.
   Sirve tanto para el pipeline de anomalías (FOCOS_ENDPOINT) como para probar datos reales. */
window.GeoLoad = (function(){
  const SEVS = ['muy_alta','alta','media','baja'];
  const SEVSCORE = { muy_alta:93, alta:80, media:62, baja:45 };

  function centroid(ring){ // centroide de área (ring: [[lon,lat],...])
    let a=0, cx=0, cy=0;
    for(let i=0, j=ring.length-1; i<ring.length; j=i++){
      const x0=ring[j][0], y0=ring[j][1], x1=ring[i][0], y1=ring[i][1], f=x0*y1 - x1*y0;
      a+=f; cx+=(x0+x1)*f; cy+=(y0+y1)*f;
    }
    if(Math.abs(a) < 1e-12){ let sx=0, sy=0; ring.forEach(p=>{sx+=p[0]; sy+=p[1];}); return [sx/ring.length, sy/ring.length]; }
    a*=0.5; return [cx/(6*a), cy/(6*a)];
  }
  function areaHa(ring){ // área planar aproximada en ha (proyección local)
    const lat0=ring[0][1], mlat=110540, mlon=111320*Math.cos(lat0*Math.PI/180);
    let a=0; for(let i=0,j=ring.length-1;i<ring.length;j=i++){
      const x0=ring[j][0]*mlon, y0=ring[j][1]*mlat, x1=ring[i][0]*mlon, y1=ring[i][1]*mlat; a+=x0*y1 - x1*y0; }
    return Math.abs(a/2)/10000;
  }

  // Severidad a partir de campos típicos del pipeline (nivel / SI / clase / severidad).
  function deriveSev(props, idx){
    if(props.sev) return props.sev;
    if(props.severidad) return props.severidad;
    const nivel=(props.nivel||'').toLowerCase();
    const si = props.SI!=null ? +props.SI : (props.si!=null ? +props.si : null);
    if(si!=null && isFinite(si)){
      let s = si<0.45?'muy_alta' : si<0.50?'alta' : si<0.55?'media' : 'baja';
      if(nivel.indexOf('priorit')>=0 && (s==='media'||s==='baja')) s='alta';   // prioritario sube un escalón
      return s;
    }
    if(nivel.indexOf('priorit')>=0) return 'alta';
    if(nivel.indexOf('vigil')>=0)  return 'media';
    const clase=(props.clase||'').toLowerCase();
    if(clase.indexOf('baja')>=0) return clase.indexOf('media')>=0 ? 'alta' : 'muy_alta';
    if(clase.indexOf('media')>=0) return 'media';
    // NO inventar. `SEVS[idx%4]` asignaba muy_alta/alta/media/baja ROTANDO POR
    // POSICION cuando el GeoJSON no traia ningun campo de severidad — que es
    // exactamente lo que pasa con la salida del motor de ranking de lotes. No
    // fallaba: mostraba algo plausible y falso, que es peor. Se declara sin dato.
    return null;
  }
  function resumenOf(props){
    // En MODO CIEGO no se filtra NADA de la severidad: ni el nivel, ni la clase, ni el
    // SI, ni el % de clorofila. El SI es la severidad en numero — mostrarlo es lo mismo
    // que mostrar el color. El dato viaja en `estrato`, que se guarda y no se muestra.
    if(window.PIXCONFIG && window.PIXCONFIG.MODO_CIEGO) return 'punto asignado para recorrida';
    if(props.resumen) return props.resumen;
    const bits=[];
    if(props.SI!=null) bits.push('SI '+(+props.SI).toFixed(2));
    if(props.clorofila_pct_vs_mejor5!=null) bits.push((+props.clorofila_pct_vs_mejor5).toFixed(0)+'% clorofila vs P95');
    // `nivel` y `clase` NO entran al resumen: se pintan en la tarjeta y revelan el
    // estrato antes de que el tecnico registre. El dato viaja en `estrato`, que se
    // guarda y no se muestra.
    if(props.nivel && !(window.PIXCONFIG&&window.PIXCONFIG.MODO_CIEGO)) bits.push(props.nivel.toLowerCase());
    if(props.clase && !(window.PIXCONFIG&&window.PIXCONFIG.MODO_CIEGO)) bits.push('vigor '+props.clase);
    return bits.length ? bits.join(' · ') : 'zona del GeoJSON de anomalías';
  }
  function scoreOf(props, sev){
    if(props.score!=null) return +props.score;
    // SI puede ser > 1 (el P95 de la zona no es un maximo): con el clamp anterior
    // un foco de SI=1,23 daba score 1 y el Prioritario se mostraba como 'Sev 1'.
    // Se mapea el rango util 0,3-1,2 y se conserva el orden.
    if(props.SI!=null && isFinite(+props.SI)){
      const si=+props.SI;
      return Math.max(1, Math.min(99, Math.round((1.2-si)/0.9*100)));
    }
    return SEVSCORE[sev]||60;
  }

  // ¿Es una feature de perímetro/límite del lote (no un foco)?
  function isPerimeter(props){
    const t=(props.tipo||props.role||props.capa||'').toString().toLowerCase();
    return ['perimetro','perímetro','limite','límite','lote','boundary','campo','contorno'].indexOf(t)>=0;
  }

  // ¿Es una capa de CONTEXTO? No es foco y TAMPOCO es perímetro.
  //
  // El motor produce dos capas que NO son alerta: zonas estructurales («esta parte viene
  // peor de lo que su porte indica») y bloques de siembra («este bloque se implantó más
  // tarde de lo que su fecha explica»). Hasta ahora esas capas NO podían mandarse al
  // teléfono, porque esta función trataba como FOCO todo lo que no fuera perímetro: le
  // asignaba severidad y número de recorrida, y mandaba al técnico a caminar una mancha
  // de suelo como si fuera un brote de la semana.
  //
  // Por eso el motor las emite en un archivo aparte (`contexto_*.geojson`). Con esta
  // versión la app ya sabe ignorarlas, así que pueden viajar en el mismo archivo sin
  // ensuciar la recorrida. Ver PIX_ALERTA/pix_alerta/capas.py.
  //
  // Se distinguen por `capa:'contexto'` o por su `tipo`. NO se las trata como perímetro
  // a propósito: si lo fueran, `ringsFromGeoJSON(gj,true)` las dibujaría como el límite
  // del lote y el mapa quedaría mal.
  function isContexto(props){
    if((props.capa||'').toString().toLowerCase()==='contexto') return true;
    const t=(props.tipo||'').toString().toLowerCase();
    return t==='zona' || t==='estrato';
  }

  function fociFromGeoJSON(gj, def){
    def=def||{};
    const feats = gj.type==='FeatureCollection' ? (gj.features||[])
                : gj.type==='Feature' ? [gj]
                : Array.isArray(gj) ? gj : [];
    const foci=[]; let n=0;
    feats.forEach(ft=>{
      const g=ft.geometry||{}, props=ft.properties||{};
      if(isPerimeter(props)) return;                 // el perímetro no es un foco
      if(isContexto(props)) return;                  // las capas de contexto tampoco
      const polys = g.type==='Polygon' ? [g.coordinates]
                  : g.type==='MultiPolygon' ? g.coordinates : [];
      polys.forEach(poly=>{
        const ring = poly && poly[0]; if(!ring || ring.length<3) return; n++;
        const [clon, clat] = centroid(ring);
        if(!isFinite(clat) || !isFinite(clon)) return;
        const area = props.area_ha!=null ? +props.area_ha : areaHa(ring);
        const sev  = deriveSev(props, n-1);   // puede ser null = SIN DATO de severidad
        foci.push({
          // El pipeline emite ahora un id ESTABLE por posición (SA-7f3a2c): el mismo
          // foco conserva su id entre corridas, que es lo que permite seguir un
          // hallazgo en el tiempo. El fallback por índice se renumera y no sirve
          // para el lazo de retorno: si se usa, el registro no es rastreable.
          id: props.id || props.name || (def.idPrefix||'F')+'-'+n,
          idEstable: !!props.id,
          // Nivel de alerta del satélite. Se GUARDA con el registro y NO se muestra
          // antes de que el técnico anote: si sabe que va a un rojo, encuentra algo.
          estrato: props.estrato || props.nivel || null,
          fechaImg: props.fecha_img || null,
          cultivo: def.cultivo || 'trigo',
          cultivoLabel: props.cultivo || def.cultivoLabel || 'Lote',
          // `etiqueta` (P1, V3) es lo que dice el mapa del PDF; `name` ahora es el id
          // estable (SA-c2aac5), que no le sirve al tecnico para casar con el informe.
          lote: props.lote || props.etiqueta || props.name || (props.zona!=null?('Zona '+props.zona):('Lote '+n)),
          hacienda: props.hacienda || def.hacienda || 'Campo',
          sev, score: scoreOf(props, sev),
          area_ha: +(+area).toFixed(area<1?2:1),
          patron: props.patron || 'foco', patronLabel: props.patronLabel || 'foco de anomalía (GeoJSON)',
          estadio: props.estadio || def.estadio || 'Vegetativo',
          resumen: resumenOf(props),
          lat: clat, lon: clon,
          poly: ring.map(c=>[c[0], c[1]])
        });
      });
    });
    // Ordenar por SEVERIDAD y recien despues por score. Ordenar solo por score ponia
    // focos de Vigilancia por delante de Prioritarios (medido sobre el archivo real:
    // un Prioritario caia al puesto 22 de 24) mientras la UI decia 'ordenados por
    // severidad'. El `punto` (1/N) define la ruta de recorrida del tecnico.
    const RANK={muy_alta:0,alta:1,media:2,baja:3};
    foci.sort((a,b)=> (RANK[a.sev]-RANK[b.sev]) || (b.score-a.score));
    foci.forEach((f,i)=> f.punto = (i+1)+'/'+foci.length);
    return foci;
  }
  // Extrae los anillos exteriores (perímetro/límite) de un GeoJSON de Polygon/MultiPolygon.
  // onlyPerimeter=true → solo features marcadas como perímetro (para leerlo del MISMO geojson de anomalías).
  function ringsFromGeoJSON(gj, onlyPerimeter){
    const feats = gj.type==='FeatureCollection' ? (gj.features||[])
                : gj.type==='Feature' ? [gj]
                : Array.isArray(gj) ? gj : [];
    const out=[];
    feats.forEach(ft=>{
      if(onlyPerimeter && !isPerimeter(ft.properties||{})) return;
      const g=ft.geometry||{};
      const polys = g.type==='Polygon' ? [g.coordinates] : g.type==='MultiPolygon' ? g.coordinates : [];
      polys.forEach(poly=>{ const r=poly && poly[0]; if(r && r.length>2) out.push(r.map(c=>[c[0],c[1]])); });
    });
    return out;
  }
  // Perímetro embebido en el propio geojson de anomalías (features tipo perímetro).
  function boundaryFromGeoJSON(gj){ return ringsFromGeoJSON(gj, true); }
  return { fociFromGeoJSON, ringsFromGeoJSON, boundaryFromGeoJSON };
})();
