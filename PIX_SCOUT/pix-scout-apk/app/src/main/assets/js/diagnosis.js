/* PIX Scout — motor de diagnóstico diferencial (biótico / abiótico / nutricional).
   Devuelve HIPÓTESIS PRESUNTIVA con confianza honesta; nunca fuerza un único resultado. */
window.Dx = (function(){

  const ABIOTICO = [
   {id:'ab-deriva',categoria:'abiotico',nombre_comun:'Deriva / fitotoxicidad de herbicida',nombre_cientifico:'Abiótico · químico',severidad_potencial:'alta',
    signo:'Ninguno (causa abiótica). Buscar el patrón, no un organismo.',
    sintoma:'Hojas nuevas deformadas/acopadas (hormonales 2,4-D/dicamba), blanqueo internervial (ALS/HPPD) o quemado de contacto. El daño se ALINEA con las pasadas de la pulverizadora o con el borde hacia el lote vecino.',
    confirmacion_campo:'Preguntar aplicaciones recientes propias y del vecino; patrón geométrico alineado a pasadas o al borde a favor del viento; suele afectar VARIAS especies a la vez.',
    confusiones:[{con:'Virus (mosaico)',como_diferenciar:'El virus da mosaico en focos que se expanden en el tiempo; la deriva es súbita y geométrica.'}],
    manejo_ref:'Revisar registro de aplicación, limpieza de tanque y carryover; documentar con foto para el productor/vecino.',
    patronBias:['borde','difuso'],temporal:'subito',hostBias:'si'},
   {id:'ab-anegamiento',categoria:'abiotico',nombre_comun:'Anegamiento / asfixia radicular',nombre_cientifico:'Abiótico · hídrico',severidad_potencial:'alta',
    signo:'Ninguno (causa abiótica).',
    sintoma:'Amarillamiento y marchitez en los BAJOS del lote tras lluvias; raíces oscuras, pobres, con mal olor; plantas atrofiadas.',
    confirmacion_campo:'Coincide con bajos / mal drenaje y con las lluvias recientes; revisar raíz (oscura, sin pelos) y encharcamiento.',
    confusiones:[{con:'Deficiencia de N',como_diferenciar:'El N responde a fertilización y no se limita a los bajos anegados.'}],
    manejo_ref:'Drenaje, evitar tráfico en húmedo; en pastura, cultivar tolerante (evitar Marandu en bajos).',
    patronBias:['relieve'],temporal:'gradual',hostBias:'si'},
   {id:'ab-sequia',categoria:'abiotico',nombre_comun:'Estrés hídrico / sequía',nombre_cientifico:'Abiótico · hídrico',severidad_potencial:'alta',
    signo:'Ninguno (causa abiótica).',
    sintoma:'Marchitez y quemado en las LOMAS y suelos arenosos/superficiales; hojas plegadas, secado desde bordes; peor en horas de calor.',
    confirmacion_campo:'Coincide con altos del relieve y suelos livianos; mejora en el bajo; ligado a veranico.',
    confusiones:[{con:'Podredumbre carbonosa (Macrophomina)',como_diferenciar:'La carbonosa deja microesclerocios negros en la base del tallo; la sequía no.'}],
    manejo_ref:'Manejo de agua/cobertura; no confundir con deficiencia nutricional.',
    patronBias:['relieve'],temporal:'gradual',hostBias:'si'},
   {id:'ab-helada',categoria:'abiotico',nombre_comun:'Daño por helada / frío',nombre_cientifico:'Abiótico · climático',severidad_potencial:'alta',
    signo:'Ninguno (causa abiótica).',
    sintoma:'Tejido acuoso que se torna marrón/necrótico de golpe; afecta el estrato expuesto y los bajos donde baja el aire frío; uniforme, súbito.',
    confirmacion_campo:'Aparición súbita tras noche fría; peor en bajos; varias especies afectadas por igual.',
    confusiones:[{con:'Enfermedad foliar',como_diferenciar:'La enfermedad progresa y tiene signo; la helada es súbita y sin organismo.'}],
    manejo_ref:'Sin control curativo; evaluar rebrote antes de decidir.',
    patronBias:['relieve','difuso'],temporal:'subito',hostBias:'si'},
   {id:'ab-granizo',categoria:'abiotico',nombre_comun:'Granizo / daño mecánico',nombre_cientifico:'Abiótico · mecánico',severidad_potencial:'alta',
    signo:'Ninguno (causa abiótica).',
    sintoma:'Heridas, hojas rasgadas y tallos quebrados con orientación direccional; súbito; sin patrón biológico. Puede abrir puerta a hongos después.',
    confirmacion_campo:'Coincide con evento de granizo/viento; heridas frescas sin organismo.',
    confusiones:[{con:'Daño de oruga',como_diferenciar:'La oruga deja bordes mordidos + excremento; el granizo, roturas irregulares sin heces.'}],
    manejo_ref:'Evaluar rebrote; vigilar entrada de patógenos por las heridas.',
    patronBias:['difuso'],temporal:'subito',hostBias:'si'},
   {id:'ab-salinidad',categoria:'abiotico',nombre_comun:'Salinidad / sodicidad',nombre_cientifico:'Abiótico · suelo',severidad_potencial:'media',
    signo:'Ninguno (causa abiótica).',
    sintoma:'Quemado marginal de hojas y manchones de bajo vigor en sectores del lote; a veces costra/eflorescencia salina en superficie.',
    confirmacion_campo:'Manchones ligados al suelo (bajos con sal, cabeceras); confirmar con CE en análisis de suelo.',
    confusiones:[{con:'Deficiencia de K',como_diferenciar:'El K también quema el borde pero sigue la edad de la hoja y responde a fertilización.'}],
    manejo_ref:'Manejo de sales / yeso según análisis; ver interpretación de suelos.',
    patronBias:['relieve','borde'],temporal:'gradual',hostBias:'si'},
  ];

  const PHENO=['Emergencia','Vegetativo','Floración','Llenado','Madurez'];
  const PATRON_OPTS=[
    {v:'foco',b:'En foco / parche denso',s:'Borde definido, concentrado',bias:'bio'},
    {v:'difuso',b:'Difuso / homogéneo',s:'Toda una zona, parejo',bias:'abio'},
    {v:'borde',b:'En bordes, franjas o pasadas',s:'Alineado a aplicación o entrada',bias:'abio'},
    {v:'relieve',b:'En bajos / altos del relieve',s:'Sigue la topografía',bias:'abio'},
  ];
  const SIGNO_OPTS=[
    {v:'estructura_fungica',b:'Pústula / micelio / mancha con estructura',s:'Signo de hongo o bacteria',cat:'enfermedad'},
    {v:'insecto',b:'Insecto visible (chinche, pulgón, mosca)',s:'Adulto o ninfa',cat:'plaga'},
    {v:'larva',b:'Larva / oruga / gusano',s:'En hoja, cogollo o suelo',cat:'plaga'},
    {v:'ninguno',b:'Sin signo — solo cambio de color',s:'Clorosis o necrosis, sin organismo',cat:'indef'},
  ];
  const DANO_OPTS=[
    {v:'masticador',b:'Mastica hojas',s:'Defoliación, agujeros, ventanas'},
    {v:'picador_succionador',b:'Pica y succiona',s:'Punteado, melaza, granos manchados'},
    {v:'cortador_subterraneo',b:'Corta / daña base o raíz',s:'Plantas segadas, raíz comida'},
    {v:'minador_barrenador',b:'Barrena tallo o mina/perfora',s:'Galerías, corazón muerto, panícula'},
  ];
  const DIST_OPTS=[
    {v:'ascendente',b:'De bajeras hacia arriba',s:'Avance ascendente (muchas royas)'},
    {v:'localizado',b:'Estrato medio o localizado',s:'Manchas puntuales'},
    {v:'espiga',b:'En espiga / vaina / grano',s:'Órganos reproductivos'},
  ];
  const FORK_OPTS=[
    {v:'nutricional',b:'Sigue la edad de la hoja',s:'Amarilleo en hojas viejas o nuevas → nutriente'},
    {v:'abiotico',b:'Patrón parejo / geométrico o ligado a clima-manejo',s:'Deriva, anegamiento, helada, granizo, sal'},
  ];
  const GRAD_OPTS=[
    {v:'vieja_a_nueva',b:'En hojas VIEJAS (bajeras)',s:'Nutriente móvil: N, P, K, Mg'},
    {v:'nueva',b:'En hojas NUEVAS (brotes)',s:'Inmóvil: S, Fe, Zn, B, Cu, Mn'},
    {v:'generalizado',b:'Generalizado en toda la planta',s:'N general, hídrico o múltiple'},
  ];

  function coherence(w, cat){
    let bio=0,abio=0;
    if(w.patron==='foco')bio+=2; else abio+=1;
    if(w.host==='no')bio+=1; else abio+=2;
    if(w.temporal==='gradual')bio+=1; else abio+=2;
    if(w.signo&&w.signo!=='ninguno')bio+=3; else abio+=1;
    const tot=bio+abio, isBio=(cat==='enfermedad'||cat==='plaga');
    return isBio? bio/tot : abio/tot;
  }
  function scoreBiotic(w, fi){
    const t=fi.dd_tags||{};
    let s=0,max=0;
    max+=2; if((t.patron_espacial||[]).includes(w.patron))s+=2;
    max+=2; if(t.tipo_signo===w.signo)s+=2;
    max+=3;
    if(w.signoCat==='plaga'){if(t.dano===w.branch)s+=3;}
    else{ if(w.branch==='espiga'){if(t.organo==='espiga_vaina_grano')s+=3;} else if(t.distribucion_planta===w.branch)s+=3; }
    return s/max;
  }
  function scoreNutri(w, fi){const t=fi.dd_tags||{}; let s=0,max=0; max+=2; if((t.patron_espacial||[]).includes(w.patron))s+=2; max+=3; if(t.gradiente_hoja===w.branch)s+=3; return s/max;}
  function scoreAbio(w, a){let s=0,max=5; if((a.patronBias||[]).includes(w.patron))s+=2; if(a.temporal===w.temporal)s+=2; if(a.hostBias===w.host)s+=1; return s/max;}

  // Devuelve {cat, coherence, candidates:[{f,conf}], top, uncertain}
  function evaluate(w){
    const c=(window.PIXDATA.cultivos||{})[w.cultivo];
    const fichas = c && Array.isArray(c.fichas) ? c.fichas : [];
    let cat, list;
    if(w.signoCat==='enfermedad'||w.signoCat==='plaga'){cat=w.signoCat;
      list=fichas.filter(f=>f.categoria===cat).map(f=>({f,m:scoreBiotic(w,f)}));
    } else if(w.fork==='nutricional'){cat='carencia';
      list=fichas.filter(f=>f.categoria==='carencia').map(f=>({f,m:scoreNutri(w,f)}));
    } else {cat='abiotico';
      list=ABIOTICO.map(a=>({f:a,m:scoreAbio(w,a)}));
    }
    const coh=coherence(w,cat);
    list.forEach(x=>x.conf=Math.round((0.6*x.m+0.4*coh)*100));
    list.sort((a,b)=>b.conf-a.conf);
    const top=list.filter(x=>x.conf>0).slice(0,5);
    const topConf=top.length?top[0].conf:0;
    const uncertain = topConf<55 || coh<0.5 || top.length===0;
    return {cat, coherence:coh, candidates:top, topConf, uncertain};
  }
  function findFicha(id){
    for(const k in window.PIXDATA.cultivos){const f=window.PIXDATA.cultivos[k].fichas.find(x=>x.id===id);if(f)return{f,cultivo:k};}
    const a=ABIOTICO.find(x=>x.id===id); if(a)return{f:a,cultivo:null}; return null;
  }

  return {ABIOTICO,PHENO,PATRON_OPTS,SIGNO_OPTS,DANO_OPTS,DIST_OPTS,FORK_OPTS,GRAD_OPTS,evaluate,findFicha};
})();
