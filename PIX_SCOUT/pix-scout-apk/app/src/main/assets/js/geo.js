/* PIX Scout — geolocalización real de dispositivo.
   watchPosition + haversine (distancia) + bearing (rumbo al foco) + heading de brújula. */
window.Geo = (function(){
  const R = 6371000; // radio terrestre (m)
  const rad = d => d*Math.PI/180;
  const deg = r => r*180/Math.PI;

  function haversine(a, b){
    if(!a||!b) return null;
    const dLat = rad(b.lat-a.lat), dLon = rad(b.lon-a.lon);
    const la1 = rad(a.lat), la2 = rad(b.lat);
    const h = Math.sin(dLat/2)**2 + Math.cos(la1)*Math.cos(la2)*Math.sin(dLon/2)**2;
    return 2*R*Math.asin(Math.min(1, Math.sqrt(h)));
  }
  function bearing(a, b){ // rumbo inicial de a->b, 0=N, sentido horario
    if(!a||!b) return null;
    const dLon = rad(b.lon-a.lon), la1=rad(a.lat), la2=rad(b.lat);
    const y = Math.sin(dLon)*Math.cos(la2);
    const x = Math.cos(la1)*Math.sin(la2) - Math.sin(la1)*Math.cos(la2)*Math.cos(dLon);
    return (deg(Math.atan2(y,x))+360)%360;
  }
  function fmtDist(m){
    if(m==null) return '—';
    if(m<1000) return Math.round(m)+' m';
    return (m/1000).toFixed(m<10000?2:1)+' km';
  }

  let watchId=null, pos=null, heading=null;
  const posSubs=new Set(), headSubs=new Set();
  const emitPos=()=>posSubs.forEach(f=>{try{f(pos);}catch(e){}});
  const emitHead=()=>headSubs.forEach(f=>{try{f(heading);}catch(e){}});

  function start(){
    if(watchId!=null || !('geolocation' in navigator)) return;
    watchId = navigator.geolocation.watchPosition(p=>{
      pos = { lat:p.coords.latitude, lon:p.coords.longitude, acc:p.coords.accuracy,
              heading:(p.coords.heading!=null&&!isNaN(p.coords.heading))?p.coords.heading:null,
              t:p.timestamp };
      if(pos.heading!=null){ heading=pos.heading; emitHead(); }
      emitPos();
    }, err=>{ pos={error:err.code, msg:err.message}; emitPos(); }, PIXCONFIG.GPS);
  }
  function stop(){ if(watchId!=null){ navigator.geolocation.clearWatch(watchId); watchId=null; } stopCompass(); }

  // Brújula (heading del dispositivo) — idempotente y removible; prioriza el rumbo ABSOLUTO.
  let compassStarted=false, compassHandler=null, haveAbsolute=false;
  function startCompass(){
    if(compassStarted) return;                       // no acumular listeners
    compassStarted=true;
    compassHandler = e => {
      let hd=null, absolute=false;
      if(e.webkitCompassHeading!=null){ hd=e.webkitCompassHeading; absolute=true; }          // iOS (absoluto)
      else if(e.absolute===true && e.alpha!=null){ hd=(360-e.alpha); absolute=true; }         // Android absoluto
      else if(e.alpha!=null){ hd=(360-e.alpha); absolute=false; }                             // relativo
      if(hd==null) return;
      if(absolute) haveAbsolute=true;
      if(!absolute && haveAbsolute) return;          // no pisar el rumbo absoluto con el relativo
      heading=hd; emitHead();
    };
    if(typeof DeviceOrientationEvent!=='undefined' && DeviceOrientationEvent.requestPermission){
      DeviceOrientationEvent.requestPermission().then(s=>{ if(s==='granted') window.addEventListener('deviceorientation', compassHandler, true); }).catch(()=>{});
    } else {
      window.addEventListener('deviceorientationabsolute', compassHandler, true);
      window.addEventListener('deviceorientation', compassHandler, true);
    }
  }
  function stopCompass(){
    if(compassHandler){
      window.removeEventListener('deviceorientationabsolute', compassHandler, true);
      window.removeEventListener('deviceorientation', compassHandler, true);
    }
    compassStarted=false; compassHandler=null; haveAbsolute=false;
  }

  return {
    start, stop, startCompass,
    onPos:f=>{posSubs.add(f); if(pos)f(pos); return ()=>posSubs.delete(f);},
    onHeading:f=>{headSubs.add(f); if(heading!=null)f(heading); return ()=>headSubs.delete(f);},
    current:()=>pos, heading:()=>heading,
    haversine, bearing, fmtDist,
    available:()=>('geolocation' in navigator),
    ok:()=>pos&&pos.lat!=null
  };
})();
