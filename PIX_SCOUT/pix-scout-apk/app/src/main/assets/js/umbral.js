/* PIX Scout — evaluacion de umbrales MIP.
   Convierte `supera_umbral` de OPINION del tecnico en CALCULO trazable (Puerta 3.2).

   LA REGLA QUE NO SE PUEDE ROMPER
   -------------------------------
   El umbral MIP esta definido sobre MUESTREO REPRESENTATIVO del lote (Embrapa fija
   6-10 puntos segun superficie, repartidos). Cuando el punto lo eligio el satelite,
   el tecnico esta parado en el PEOR sitio del lote por construccion: comparar ese
   conteo contra el umbral empuja a sobre-aplicar, que es exactamente lo contrario de
   lo que el MIP ahorra (Embrapa: R$270/ha decidiendo por umbral y no por calendario).

   Por eso el veredicto SIEMPRE viaja con `comparable_con_mip`. Con muestreo dirigido
   la salida es 'referencia', nunca 'supera el umbral, aplicar'.
*/
window.Umbral = (function(){

  function tabla(){
    return (window.PIXDATA && window.PIXDATA.umbrales) || {umbrales:{}, unidades:{}};
  }

  function etiquetaUnidad(u){
    const t = tabla();
    return (t.unidades && t.unidades[u]) || u;
  }

  // ¿La condicion de la regla se cumple con el contexto declarado?
  // Sin contexto NO se asume que se cumple: una regla condicionada que no se puede
  // verificar queda 'no_aplicable', no 'cumple'. Suponer el estadio es inventar el dato.
  function condicionOk(regla, ctx){
    if(!regla.condicion) return {ok:true, faltante:null};
    const c = regla.condicion;
    for(const k in c){
      const declarado = ctx && ctx[k];
      if(!declarado) return {ok:false, faltante:k};
      if(String(declarado) !== String(c[k])) return {ok:false, faltante:null};
    }
    return {ok:true, faltante:null};
  }

  function compara(valor, op, ref){
    switch(op){
      case '>=': return valor >= ref;
      case '>':  return valor >  ref;
      case '<=': return valor <= ref;
      case '<':  return valor <  ref;
      default:   return null;
    }
  }

  /* Evalua un conteo contra el umbral de una ficha.
     conteo  : numero medido por el tecnico (o null)
     unidad  : clave de unidad (ver umbrales.json -> unidades)
     ctx     : {fase, destino, material, tipo_muestreo}
     Devuelve SIEMPRE un objeto explicando el resultado; nunca lanza.            */
  function evaluar(fichaId, conteo, unidad, ctx){
    ctx = ctx || {};
    const t = tabla();
    const u = (t.umbrales || {})[fichaId];
    const base = {
      fichaId: fichaId,
      supera_umbral: null,          // true | false | null (null = no se pudo calcular)
      estado: 'sin_umbral',
      calculado: false,
      comparable_con_mip: false,
      motivo: null,
      regla: null,
      fuente: u ? u.fuente : null,
      calibrado_en: u ? u.calibrado_en : null,
      advertencias: (u && u.advertencias) ? u.advertencias.slice() : []
    };

    if(!u){
      base.motivo = 'Esta ficha no tiene umbral de accion cargado.';
      return base;
    }
    if(!u.computable){
      base.estado = 'no_computable';
      base.motivo = u.motivo_no_computable || 'Umbral no establecido para esta plaga.';
      return base;
    }
    if(conteo == null || conteo === '' || !isFinite(+conteo)){
      base.estado = 'sin_conteo';
      base.motivo = 'Falta el conteo. Sin numero no hay comparacion posible.';
      return base;
    }
    if(!unidad){
      base.estado = 'sin_unidad';
      base.motivo = 'Falta declarar en que unidad se conto.';
      return base;
    }

    const candidatas = (u.reglas || []).filter(r => r.unidad === unidad);
    if(!candidatas.length){
      const disponibles = (u.reglas || []).map(r => etiquetaUnidad(r.unidad));
      base.estado = 'unidad_no_coincide';
      base.motivo = 'Se conto en "' + etiquetaUnidad(unidad) + '" y el umbral esta definido en: '
                  + (disponibles.join(' / ') || '—') + '. No se comparan unidades distintas.';
      return base;
    }

    // De las reglas de esa unidad, la que corresponde al contexto declarado.
    let elegida = null, faltante = null;
    for(const r of candidatas){
      const c = condicionOk(r, ctx);
      if(c.ok){ elegida = r; break; }
      if(c.faltante) faltante = c.faltante;
    }
    if(!elegida){
      base.estado = 'contexto_insuficiente';
      base.motivo = faltante
        ? 'El umbral cambia segun "' + faltante + '" y ese dato no esta declarado. No se asume.'
        : 'Ninguna regla del umbral aplica al contexto declarado.';
      return base;
    }

    const n = +conteo;
    const res = compara(n, elegida.operador, elegida.valor);
    if(res === null){
      base.motivo = 'Operador desconocido en la regla: ' + elegida.operador;
      return base;
    }

    base.calculado = true;
    base.supera_umbral = res;
    base.regla = {
      valor: elegida.valor, operador: elegida.operador,
      unidad: elegida.unidad, unidad_label: etiquetaUnidad(elegida.unidad),
      condicion: elegida.condicion || null, nota: elegida.nota || null
    };
    if(elegida.nota) base.advertencias.push(elegida.nota);
    if(u.muestreo_minimo) base.advertencias.push('Muestreo minimo del protocolo: ' + u.muestreo_minimo);

    // AQUI esta la decision que evita que el producto empuje a sobre-aplicar.
    const dirigido = (ctx.tipo_muestreo || '').indexOf('dirigido') >= 0;
    base.comparable_con_mip = !dirigido;
    if(dirigido){
      base.estado = res ? 'referencia_supera' : 'referencia_por_debajo';
      base.motivo = 'Conteo en punto elegido por el satelite (el peor del lote). El umbral MIP '
                  + 'esta calibrado sobre muestreo representativo: esto es una REFERENCIA, no un '
                  + 'criterio de aplicacion. Para decidir, muestrear el lote segun protocolo.';
    } else {
      base.estado = res ? 'supera' : 'por_debajo';
      base.motivo = 'Muestreo representativo: la comparacion contra el umbral MIP es valida.';
    }
    return base;
  }

  // Texto corto para la UI (el detalle largo va en `motivo`).
  function resumen(v){
    if(!v) return '—';
    switch(v.estado){
      case 'supera':              return 'SUPERA el umbral MIP';
      case 'por_debajo':          return 'Por debajo del umbral MIP';
      case 'referencia_supera':   return 'Por encima de la referencia (muestreo dirigido)';
      case 'referencia_por_debajo': return 'Por debajo de la referencia (muestreo dirigido)';
      case 'no_computable':       return 'Sin umbral establecido';
      case 'sin_conteo':          return 'Falta el conteo';
      case 'sin_unidad':          return 'Falta la unidad';
      case 'unidad_no_coincide':  return 'Unidad distinta a la del umbral';
      case 'contexto_insuficiente': return 'Falta el estadio/destino';
      default:                    return 'Sin umbral cargado';
    }
  }

  // Unidades en las que ESTA ficha admite conteo (para ofrecerlas en la UI en vez
  // de que el tecnico escriba texto libre que despues no se puede comparar).
  function unidadesDe(fichaId){
    const u = (tabla().umbrales || {})[fichaId];
    if(!u || !u.computable) return [];
    const vistas = [];
    (u.reglas || []).forEach(r => {
      if(vistas.indexOf(r.unidad) < 0) vistas.push(r.unidad);
    });
    return vistas.map(k => ({clave:k, label:etiquetaUnidad(k)}));
  }

  return { evaluar, resumen, unidadesDe, etiquetaUnidad };
})();
