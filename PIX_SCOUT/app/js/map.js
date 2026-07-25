/* PIX Scout — mapa en canvas (Web Mercator) con base satelital opcional (tiles XYZ, caché offline)
   + capa vectorial: perímetro del lote, focos de anomalía por severidad, GPS y línea al foco.
   La capa satelital se cachea (Cache API 'pixscout-tiles') → funciona sin señal tras verla una vez. */
window.ScoutMap = (function(){
  const SEVCOL = { crit:'#ef4444', alta:'#f59e0b', media:'#14b8a6', baja:'#84cc16' };
  const TILES_CACHE = 'pixscout-tiles';
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));

  function mPerDegLat(lat){ return 111132.92 - 559.82*Math.cos(2*lat*Math.PI/180) + 1.175*Math.cos(4*lat*Math.PI/180); }
  function mPerDegLon(lat){ return 111412.84*Math.cos(lat*Math.PI/180) - 93.5*Math.cos(3*lat*Math.PI/180); }
  function seeded(str){ let h=2166136261>>>0; for(let i=0;i<str.length;i++){ h^=str.charCodeAt(i); h=Math.imul(h,16777619); }
    return ()=>{ h+=0x6D2B79F5; let t=h; t=Math.imul(t^(t>>>15),1|t); t^=t+Math.imul(t^(t>>>7),61|t); return ((t^(t>>>14))>>>0)/4294967296; }; }
  function ringFor(f){
    if(Array.isArray(f.poly) && f.poly.length>2) return f.poly;
    const rnd=seeded(f.id||(''+f.lat+f.lon));
    const areaM=Math.max(0.6,(f.area_ha||3))*10000, base=Math.sqrt(areaM/Math.PI);
    const mlat=mPerDegLat(f.lat), mlon=mPerDegLon(f.lat), n=11, ring=[];
    for(let i=0;i<n;i++){ const a=i/n*2*Math.PI, r=base*(0.62+0.72*rnd());
      ring.push([ f.lon + (r*Math.cos(a))/mlon, f.lat + (r*Math.sin(a))/mlat ]); }
    ring.push(ring[0]); return ring;
  }
  function sevC(f){ return SEVCOL[f.sevClass] || SEVCOL.media; }

  // ---- Web Mercator (world px = 256·2^z) ----
  function projZ(lat,lon,z){ const s=256*Math.pow(2,z);
    const x=(lon+180)/360*s;
    const sn=Math.sin(clamp(lat,-85.0511,85.0511)*Math.PI/180);
    const y=(0.5 - Math.log((1+sn)/(1-sn))/(4*Math.PI))*s; return [x,y]; }
  function unprojZ(x,y,z){ const s=256*Math.pow(2,z);
    const lon=x/s*360-180; const n=Math.PI-2*Math.PI*y/s;
    const lat=180/Math.PI*Math.atan(0.5*(Math.exp(n)-Math.exp(-n))); return [lat,lon]; }

  function create(canvas, opts){
    opts=opts||{};
    const ctx=canvas.getContext('2d');
    const SAT=(window.PIXCONFIG&&window.PIXCONFIG.SAT_TILES)||{};
    let foci=[], rings=[], boundary=[], user=null, heading=null, sel=null;
    let center={lat:0,lon:0}, zoom=16, satellite=!!(window.PIXCONFIG&&window.PIXCONFIG.SAT_DEFAULT);
    let W=0,H=0,dpr=1, ro=null, screenRings=[];
    const tileMem=new Map();               // url -> Image | 'loading' | 'err'
    let rafPending=false;

    function schedule(){ if(rafPending) return; rafPending=true; requestAnimationFrame(()=>{ rafPending=false; draw(); }); }
    function resize(){ dpr=Math.min(window.devicePixelRatio||1,2.5);
      const r=canvas.getBoundingClientRect(); W=Math.max(1,r.width); H=Math.max(1,r.height);
      canvas.width=Math.round(W*dpr); canvas.height=Math.round(H*dpr); ctx.setTransform(dpr,0,0,dpr,0,0); draw(); }

    function projF(lat,lon){ return projZ(lat,lon,zoom); }
    function screen(lon,lat){ const cw=projF(center.lat,center.lon), p=projF(lat,lon); return [W/2+(p[0]-cw[0]), H/2+(p[1]-cw[1])]; }

    function setFoci(f){ foci=f||[]; rings=foci.map(ringFor); if(!center.lat) fit(); else draw(); }
    function setBoundary(b){ boundary=b||[]; if(!center.lat) fit(); else draw(); }
    function setUser(p,h){ user=p; if(h!=null) heading=h; draw(); }
    function select(id){ sel=id; draw(); }
    function selected(){ return foci.find(f=>f.id===sel)||null; }
    function setSatellite(on){ satellite=!!on; draw(); }
    function isSatellite(){ return satellite; }

    function bounds(){ const pts=[]; (boundary.length?boundary:rings).forEach(r=>r.forEach(c=>pts.push(c))); rings.forEach(r=>r.forEach(c=>pts.push(c))); if(user) pts.push([user.lon,user.lat]);
      if(!pts.length) return null; let a=1e9,b=1e9,c=-1e9,d=-1e9;
      pts.forEach(([lo,la])=>{a=Math.min(a,lo);c=Math.max(c,lo);b=Math.min(b,la);d=Math.max(d,la);}); return {mnx:a,mny:b,mxx:c,mxy:d}; }
    function fit(){ const bb=bounds(); if(!bb) return;
      center={lat:(bb.mny+bb.mxy)/2, lon:(bb.mnx+bb.mxx)/2};
      const latR=l=>Math.log(Math.tan(Math.PI/4 + clamp(l,-85,85)*Math.PI/360));
      const latFrac=Math.abs(latR(bb.mxy)-latR(bb.mny))/(2*Math.PI) || 1e-6;
      const lonFrac=Math.abs(bb.mxx-bb.mnx)/360 || 1e-6;
      zoom=clamp(Math.min(Math.log2(H/256/latFrac), Math.log2(W/256/lonFrac))-0.35, 3, 20); draw(); }
    function centerOn(lat,lon,across){ center={lat,lon};
      if(across){ const mpp=across/Math.max(W,1); zoom=clamp(Math.log2(156543.03*Math.cos(lat*Math.PI/180)/mpp), 3, 20); } draw(); }
    function recenter(){ if(user){ center={lat:user.lat,lon:user.lon}; zoom=Math.max(zoom,17.5); draw(); } else fit(); }
    function zoomBy(dz,ox,oy){ ox=(ox==null)?W/2:ox; oy=(oy==null)?H/2:oy;
      const cw=projF(center.lat,center.lon); const ll=unprojZ(cw[0]+(ox-W/2), cw[1]+(oy-H/2), zoom);
      zoom=clamp(zoom+dz, 3, 21);
      const cw2=projZ(ll[0],ll[1],zoom); center={}; const c=unprojZ(cw2[0]-(ox-W/2), cw2[1]-(oy-H/2), zoom); center={lat:c[0],lon:c[1]}; draw(); }

    // ---- tiles satelitales (cache-first, fallback red; se guardan para offline) ----
    function tileUrl(z,x,y){ return (SAT.url||'').replace('{z}',z).replace('{x}',x).replace('{y}',y); }
    function requestTile(url){
      const v=tileMem.get(url); if(v){ return v==='loading'||v==='err'?null:v; }
      tileMem.set(url,'loading');
      (async()=>{
        try{
          const cache = ('caches' in window) ? await caches.open(TILES_CACHE) : null;
          let resp = cache ? await cache.match(url) : null;
          if(!resp){ resp=await fetch(url,{mode:'cors'}); if(resp&&resp.ok&&cache){ try{ await cache.put(url,resp.clone()); }catch(e){} } }
          if(resp&&resp.ok){ const blob=await resp.blob(); const img=new Image();
            img.onload=()=>{ tileMem.set(url,img); schedule(); };
            img.onerror=()=>{ tileMem.set(url,'err'); }; img.src=URL.createObjectURL(blob); }
          else tileMem.set(url,'err');
        }catch(e){
          // fallback online sin caché (proveedores sin CORS): imagen directa
          const img=new Image(); img.onload=()=>{ tileMem.set(url,img); schedule(); }; img.onerror=()=>{ tileMem.set(url,'err'); }; img.src=url;
        }
      })();
      return null;
    }
    function drawTiles(){
      if(!satellite || !SAT.url) return false;
      const zc=clamp(Math.round(zoom), 0, SAT.maxZoom||19);
      const scale=Math.pow(2, zoom-zc), ts=256*scale;
      const cw=projF(center.lat,center.lon);
      const worldToScreen=(wx,wy)=>[ W/2 + (wx*scale - cw[0]), H/2 + (wy*scale - cw[1]) ]; // wx,wy en world px a zc
      // world px del centro a zc:
      const cz=projZ(center.lat,center.lon,zc);
      const minX=Math.floor((cz[0]-(W/2)/scale)/256), maxX=Math.floor((cz[0]+(W/2)/scale)/256);
      const minY=Math.floor((cz[1]-(H/2)/scale)/256), maxY=Math.floor((cz[1]+(H/2)/scale)/256);
      const nmax=Math.pow(2,zc); let drew=false;
      for(let x=minX;x<=maxX;x++) for(let y=minY;y<=maxY;y++){
        const tx=((x%nmax)+nmax)%nmax; if(y<0||y>=nmax) continue;
        const sx=W/2 + (x*256 - cz[0])*scale, sy=H/2 + (y*256 - cz[1])*scale;
        const img=requestTile(tileUrl(zc,tx,y));
        if(img){ try{ ctx.drawImage(img, sx, sy, ts+0.5, ts+0.5); drew=true; }catch(e){} }
      }
      return drew;
    }

    function draw(){
      if(!W) return;
      ctx.clearRect(0,0,W,H);
      const hasSat = drawTiles();
      // fondo/grilla solo en modo vectorial (sin satélite)
      if(!hasSat){
        ctx.fillStyle = opts.dark===false ? '#eef3f0' : '#0e1b18'; ctx.fillRect(0,0,W,H);
        const grid=opts.dark===false ? 'rgba(13,148,136,.12)' : 'rgba(45,212,191,.10)';
        const mpp=156543.03*Math.cos(center.lat*Math.PI/180)/Math.pow(2,zoom);
        const stepM=niceMeters(mpp), stepPx=stepM/mpp;
        if(stepPx>16 && stepPx<300){ ctx.strokeStyle=grid; ctx.lineWidth=1; ctx.beginPath();
          for(let x=(W/2)% stepPx; x<W; x+=stepPx){ ctx.moveTo(x,0); ctx.lineTo(x,H);} for(let y=(H/2)%stepPx;y<H;y+=stepPx){ ctx.moveTo(0,y); ctx.lineTo(W,y);} ctx.stroke(); }
      } else if(satellite){ ctx.fillStyle='rgba(0,0,0,.12)'; ctx.fillRect(0,0,W,H); } // leve oscurecido para legibilidad de overlays

      // perímetro del lote
      if(boundary.length){ boundary.forEach(r=>{ const pts=r.map(([lo,la])=>screen(lo,la));
        ctx.beginPath(); pts.forEach((p,k)=> k?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1])); ctx.closePath();
        ctx.fillStyle= hasSat?'rgba(255,255,255,.04)':(opts.dark===false?'rgba(13,148,136,.05)':'rgba(130,170,160,.05)'); ctx.fill();
        ctx.setLineDash([]); ctx.lineWidth=hasSat?3:2.5; ctx.strokeStyle= hasSat?'rgba(255,255,255,.9)':(opts.dark===false?'rgba(11,61,56,.6)':'rgba(200,224,214,.55)');
        if(hasSat){ ctx.shadowColor='rgba(0,0,0,.6)'; ctx.shadowBlur=3; } ctx.stroke(); ctx.shadowBlur=0; }); }

      // focos de anomalía
      screenRings=[];
      foci.forEach((f,i)=>{ const col=sevC(f), on=f.id===sel, pts=rings[i].map(([lo,la])=>screen(lo,la)); screenRings[i]=pts;
        ctx.beginPath(); pts.forEach((p,k)=> k?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1])); ctx.closePath();
        ctx.fillStyle=hexA(col, on?0.5:(hasSat?0.34:0.26)); ctx.fill();
        ctx.lineWidth=on?3:1.8; ctx.strokeStyle=col; ctx.stroke();
        const c=screen(f.lon,f.lat);
        ctx.beginPath(); ctx.arc(c[0],c[1], on?7:5, 0, 2*Math.PI); ctx.fillStyle=col; ctx.fill();
        ctx.lineWidth=2; ctx.strokeStyle= hasSat?'#fff':(opts.dark===false?'#fff':'#0e1b18'); ctx.stroke();
        if(zoom>15.3 || on){ label(c[0]+9,c[1]+4, (f.cultivoLabel||'')+(f.lote?' · '+f.lote:''), col, false, hasSat); }
      });

      // línea usuario→foco + distancia
      const s=selected();
      if(user && s){ const a=screen(user.lon,user.lat), b=screen(s.lon,s.lat);
        ctx.setLineDash([7,6]); ctx.lineWidth=2.5; ctx.strokeStyle=sevC(s);
        ctx.beginPath(); ctx.moveTo(a[0],a[1]); ctx.lineTo(b[0],b[1]); ctx.stroke(); ctx.setLineDash([]);
        label((a[0]+b[0])/2,(a[1]+b[1])/2, fmt(dist(user,s)), sevC(s), true, hasSat); }

      // usuario GPS
      if(user){ const u=screen(user.lon,user.lat);
        if(user.acc){ const rr=clamp(user.acc/(156543.03*Math.cos(center.lat*Math.PI/180)/Math.pow(2,zoom)), 6, Math.max(W,H));
          ctx.beginPath(); ctx.arc(u[0],u[1],rr,0,2*Math.PI); ctx.fillStyle='rgba(37,99,235,.14)'; ctx.fill();
          ctx.strokeStyle='rgba(37,99,235,.55)'; ctx.lineWidth=1; ctx.stroke(); }
        if(heading!=null){ ctx.save(); ctx.translate(u[0],u[1]); ctx.rotate(heading*Math.PI/180);
          ctx.beginPath(); ctx.moveTo(0,-16); ctx.lineTo(7,7); ctx.lineTo(0,3); ctx.lineTo(-7,7); ctx.closePath(); ctx.fillStyle='#2563eb'; ctx.fill(); ctx.restore(); }
        ctx.beginPath(); ctx.arc(u[0],u[1],7,0,2*Math.PI); ctx.fillStyle='#2563eb'; ctx.fill(); ctx.lineWidth=2.5; ctx.strokeStyle='#fff'; ctx.stroke(); }

      scaleBar(); northArrow(); if(hasSat) attribution();
    }

    function niceMeters(mpp){ const target=80*mpp; const pow=Math.pow(10,Math.floor(Math.log10(target)));
      return [1,2,5,10].map(x=>x*pow).find(x=>x>=target)||10*pow; }
    function label(x,y,txt,col,center,sat){ if(!txt) return; ctx.font='600 12px system-ui,sans-serif';
      const w=ctx.measureText(txt).width, px=center?x-w/2-5:x-4;
      ctx.fillStyle= sat?'rgba(6,17,14,.82)':(opts.dark===false?'rgba(255,255,255,.82)':'rgba(6,17,14,.72)'); ctx.fillRect(px, y-12, w+9, 17);
      ctx.fillStyle= sat?'#eafff9':(opts.dark===false?'#0b3d38':'#e8f0ec'); ctx.textBaseline='alphabetic'; ctx.fillText(txt, center?x-w/2:x, y+1); }
    function scaleBar(){ const mpp=156543.03*Math.cos(center.lat*Math.PI/180)/Math.pow(2,zoom); const m=niceMeters(mpp), px=m/mpp, x=14,y=H-18;
      ctx.strokeStyle= satellite?'#fff':(opts.dark===false?'#0b3d38':'#cfe'); ctx.lineWidth=2.5;
      if(satellite){ ctx.shadowColor='rgba(0,0,0,.6)'; ctx.shadowBlur=2; }
      ctx.beginPath(); ctx.moveTo(x,y); ctx.lineTo(x+px,y); ctx.moveTo(x,y-5); ctx.lineTo(x,y+5); ctx.moveTo(x+px,y-5); ctx.lineTo(x+px,y+5); ctx.stroke(); ctx.shadowBlur=0;
      ctx.font='700 11px system-ui'; ctx.fillStyle= satellite?'#fff':(opts.dark===false?'#0b3d38':'#cfe'); ctx.fillText(m>=1000?(m/1000)+' km':Math.round(m)+' m', x, y-8); }
    function northArrow(){ const x=W-24,y=26; ctx.save(); ctx.translate(x,y);
      if(satellite){ ctx.shadowColor='rgba(0,0,0,.6)'; ctx.shadowBlur=2; }
      ctx.beginPath(); ctx.moveTo(0,-12); ctx.lineTo(6,10); ctx.lineTo(0,5); ctx.lineTo(-6,10); ctx.closePath();
      ctx.fillStyle= satellite?'#fff':(opts.dark===false?'#0b3d38':'#cfe'); ctx.fill();
      ctx.font='700 10px system-ui'; ctx.textAlign='center'; ctx.fillText('N',0,-14); ctx.textAlign='left'; ctx.shadowBlur=0; ctx.restore(); }
    function attribution(){ const t=SAT.attribution||''; if(!t) return; ctx.font='500 9px system-ui';
      const w=ctx.measureText(t).width; ctx.fillStyle='rgba(0,0,0,.45)'; ctx.fillRect(W-w-10, H-15, w+8, 13);
      ctx.fillStyle='rgba(255,255,255,.85)'; ctx.fillText(t, W-w-6, H-5); }

    function dist(a,b){ const dLat=(b.lat-a.lat)*Math.PI/180, dLon=(b.lon-a.lon)*Math.PI/180, la1=a.lat*Math.PI/180, la2=b.lat*Math.PI/180;
      const h=Math.sin(dLat/2)**2+Math.cos(la1)*Math.cos(la2)*Math.sin(dLon/2)**2; return 2*6371000*Math.asin(Math.min(1,Math.sqrt(h))); }
    function fmt(m){ return m<1000?Math.round(m)+' m':(m/1000).toFixed(m<10000?2:1)+' km'; }
    function hexA(hex,a){ const n=parseInt(hex.slice(1),16); return `rgba(${(n>>16)&255},${(n>>8)&255},${n&255},${a})`; }
    function pip(pt, poly){ let c=false; for(let i=0,j=poly.length-1;i<poly.length;j=i++){ const xi=poly[i][0],yi=poly[i][1],xj=poly[j][0],yj=poly[j][1];
      if(((yi>pt[1])!==(yj>pt[1])) && (pt[0] < (xj-xi)*(pt[1]-yi)/(yj-yi)+xi)) c=!c; } return c; }
    function hit(sx,sy){ for(let i=0;i<foci.length;i++){ if(screenRings[i] && pip([sx,sy],screenRings[i])) return foci[i]; }
      let best=null,bd=26; foci.forEach(f=>{ const p=screen(f.lon,f.lat), d=Math.hypot(p[0]-sx,p[1]-sy); if(d<bd){bd=d;best=f;} }); return best; }

    // ---- interacción ----
    let down=false,lx=0,ly=0,moved=0, ptrs=new Map(), pd=0;
    function panBy(dx,dy){ const cw=projF(center.lat,center.lon); const c=unprojZ(cw[0]-dx, cw[1]-dy, zoom); center={lat:c[0],lon:c[1]}; draw(); }
    function onDown(e){ canvas.setPointerCapture&&canvas.setPointerCapture(e.pointerId); ptrs.set(e.pointerId,[e.clientX,e.clientY]);
      if(ptrs.size===1){ down=true; lx=e.clientX; ly=e.clientY; moved=0; } if(ptrs.size===2){ pd=pdist(); } }
    function onMove(e){ if(!ptrs.has(e.pointerId)) return; ptrs.set(e.pointerId,[e.clientX,e.clientY]);
      if(ptrs.size>=2){ const nd=pdist(); if(pd>0){ const cxy=pcenter(), r=canvas.getBoundingClientRect(); zoomBy(Math.log2(nd/pd), cxy[0]-r.left, cxy[1]-r.top); } pd=nd; return; }
      if(down){ const dx=e.clientX-lx, dy=e.clientY-ly; panBy(dx,dy); lx=e.clientX; ly=e.clientY; moved+=Math.abs(dx)+Math.abs(dy); } }
    function onUp(e){ const wasTap = down && moved<6; ptrs.delete(e.pointerId); if(ptrs.size<2) pd=0; if(ptrs.size===0){ down=false;
      if(wasTap && opts.onSelect){ const r=canvas.getBoundingClientRect(); const f=hit(e.clientX-r.left, e.clientY-r.top); if(f){ sel=f.id; draw(); opts.onSelect(f); } } } }
    function pdist(){ const v=[...ptrs.values()]; return Math.hypot(v[0][0]-v[1][0], v[0][1]-v[1][1]); }
    function pcenter(){ const v=[...ptrs.values()]; return [(v[0][0]+v[1][0])/2,(v[0][1]+v[1][1])/2]; }
    function onWheel(e){ e.preventDefault(); const r=canvas.getBoundingClientRect(); zoomBy(e.deltaY<0?0.5:-0.5, e.clientX-r.left, e.clientY-r.top); }

    canvas.style.touchAction='none';
    canvas.addEventListener('pointerdown',onDown); canvas.addEventListener('pointermove',onMove);
    canvas.addEventListener('pointerup',onUp); canvas.addEventListener('pointercancel',onUp);
    canvas.addEventListener('wheel',onWheel,{passive:false});
    if(window.ResizeObserver){ ro=new ResizeObserver(resize); ro.observe(canvas); }
    resize();
    function destroy(){ try{ro&&ro.disconnect();}catch(e){}
      canvas.removeEventListener('pointerdown',onDown); canvas.removeEventListener('pointermove',onMove);
      canvas.removeEventListener('pointerup',onUp); canvas.removeEventListener('pointercancel',onUp); canvas.removeEventListener('wheel',onWheel);
      tileMem.clear(); }

    return { setFoci, setBoundary, setUser, select, selected, setSatellite, isSatellite, fit, recenter, centerOn,
             zoomIn:()=>zoomBy(0.6), zoomOut:()=>zoomBy(-0.6), resize, destroy, dist:(a,b)=>dist(a,b), fmt };
  }
  return { create };
})();
