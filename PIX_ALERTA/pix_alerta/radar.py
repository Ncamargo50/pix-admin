# -*- coding: utf-8 -*-
"""Continuidad bajo nubes con Sentinel-1. NO es un tercer eje del criterio.

POR QUE EXISTE
--------------
La medicion que mas importa de todo el motor: el poder de discriminacion sigue a
la COBERTURA, no al indice. Sobre las tres campañas de HDS, con la misma
configuracion de ejes, la campaña con 16,0% de observaciones opticas plenas dio
lift 36x y la de 11,8% dio 6,7x. Cambiar de indice compro ~2x; la disponibilidad
de imagen vale ~5x. Por eso esto va antes que seguir afinando indices.

Medido sobre HDS (oct-2025 a ene-2026): S1 aporta **9 pasadas en 4 meses, de UNA
sola orbita relativa, solo descendente**, con hueco mediano de 12 dias. Los 6 dias
nominales NO existen ahi: una sola orbita cubre el punto. Planificar con 12.

QUE PUEDE Y QUE NO PUEDE DECIR EL RADAR
---------------------------------------
El retrodispersor mide ESTRUCTURA del dosel y constante dielectrica (agua), no
pigmentos. **S1 no detecta enfermedad.** Meterlo como tercer eje del mismo EWMA
seria mezclar dos cosas fisicamente distintas y ensuciar el criterio optico que ya
esta medido.

Lo que si hace, y es exactamente el agujero que hay que tapar: cuando un lote se
queda sin observacion optica, el criterio lo declara SIN DATO — que es honesto
pero inutil, y le pasa al 66% de los lotes en algun momento de la campaña, con
huecos de hasta 175 dias. El radar convierte ese "no se" en **"el radar no vio
cambio estructural"**, que es informacion debil pero real, o en **"el radar vio un
cambio abrupto"**, que manda al tecnico igual.

Un cambio brusco de retrodispersion sobre un lote en campaña es: vuelco (acame),
cosecha anticipada, anegamiento, o perdida severa de biomasa. Ninguna de esas es
una plaga, y todas justifican una visita.

EL INDICE
---------
RVI = 4 * VH / (VV + VH), en potencia LINEAL (no en dB — promediar decibeles es
promediar logaritmos y sesga). Crece con la dispersion de volumen, o sea con la
biomasa y la complejidad del dosel.

LA ORBITA ES OBLIGATORIA
------------------------
Mezclar orbitas mezcla geometrias de vista: el mismo lote cambia de retrodispersion
por el angulo de incidencia, no por el cultivo. Se trabaja SOLO con la orbita
relativa dominante del sitio, y se declara cual.
"""
import json

import ee
import pandas as pd

from . import config as cfg
from . import series as sr

# Una orbita con menos pasadas que esto no hace serie temporal.
MIN_ESCENAS_ORBITA = 5
# Minimos SIN LOS CUALES NO SE PUEDE AFIRMAR "sin cambio". Medido 2026-07-26: sin
# ellos, un sitio de UN lote daba SIN CAMBIO garantizado ante una caida de RVI de
# -0,40 (el lote es su propia mediana: resid=0, MAD=0, z=0), las primeras 4
# observaciones de cada lote eran inmunes, y un lote con 2 pixeles utiles sobre
# 30 ha producia un z finito. Cuatro vias distintas, todas hacia la misma mentira.
MIN_LOTES_COHORTE_RADAR = 8   # sin esto la mediana de la cohorte no significa nada
MIN_OBS_RADAR = 5             # > N_BASE: hace falta al menos una obs de fase II
MIN_PX_RADAR = 8              # mismo criterio de soporte que el camino optico
# Cambio estructural: sigmas del residuo del lote respecto de su cohorte. Mas alto
# que el del criterio optico a proposito — acá solo interesan los eventos gruesos
# (vuelco, cosecha, anegamiento), no el estres fino, que el radar no ve.
Z_CAMBIO = 3.0
ESCALA = 20


def _coleccion(aoi, ini, fin):
    return (ee.ImageCollection('COPERNICUS/S1_GRD')
            .filterBounds(aoi).filterDate(ini, fin)
            .filter(ee.Filter.eq('instrumentMode', 'IW'))
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')))


def orbita_dominante(aoi, ini, fin, verbose=True):
    """(orbita relativa, pasada) con mas escenas sobre el sitio. None si no alcanza.

    Se elige UNA y se declara. Combinar orbitas hace que el mismo lote cambie de
    retrodispersion por el angulo de vista y no por el cultivo: seria fabricar
    variabilidad temporal que no ocurrio en el campo.
    """
    col = _coleccion(aoi, ini, fin)
    orb = col.aggregate_array('relativeOrbitNumber_start').getInfo() or []
    pas = col.aggregate_array('orbitProperties_pass').getInfo() or []
    if not orb:
        return None
    d = pd.DataFrame({'orb': orb, 'pass': pas})
    conteo = d.groupby(['orb', 'pass']).size().sort_values(ascending=False)
    (o, p), n = conteo.index[0], conteo.iloc[0]
    if verbose:
        otras = len(conteo) - 1
        print('[S1] orbita %s %s: %d escenas%s'
              % (o, p, n, (' (se descartan %d de otras %d orbitas)'
                           % (int(conteo.iloc[1:].sum()), otras)) if otras else ''))
    if n < MIN_ESCENAS_ORBITA:
        if verbose:
            print('[S1] menos de %d pasadas: no alcanza para serie'
                  % MIN_ESCENAS_ORBITA)
        return None
    return int(o), str(p)


def _rvi(img):
    """RVI en potencia lineal. Las bandas de S1_GRD vienen en dB."""
    lin = lambda b: ee.Image(10).pow(img.select(b).divide(10))
    vv, vh = lin('VV'), lin('VH')
    rvi = vh.multiply(4).divide(vv.add(vh).max(1e-9)).rename('RVI')
    return rvi.addBands(vv.rename('VV_lin')).addBands(vh.rename('VH_lin'))


def extraer(sitio, ini, fin, escala=ESCALA, verbose=True):
    """Tabla (lote_id, fecha, RVI, VV_lin, VH_lin, n_px) desde una sola orbita.

    Misma geometria y mismo buffer negativo que la serie optica: si midieran areas
    distintas, el radar no podria hablar del mismo lote que el criterio.
    """
    lotes = sr._lotes_ee(sitio)
    aoi = lotes.geometry()
    dom = orbita_dominante(aoi, ini, fin, verbose)
    if dom is None:
        return pd.DataFrame()
    o, p = dom
    col = (_coleccion(aoi, ini, fin)
           .filter(ee.Filter.eq('relativeOrbitNumber_start', o))
           .filter(ee.Filter.eq('orbitProperties_pass', p)))
    n_esc = col.size().getInfo()
    if not n_esc:
        return pd.DataFrame()
    n_lotes = lotes.size().getInfo()

    def por_escena(img):
        img = ee.Image(img)
        campos = _rvi(img)
        stats = campos.reduceRegions(
            collection=lotes,
            reducer=ee.Reducer.mean().combine(ee.Reducer.count(), '', True),
            scale=escala, tileScale=4)
        d = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd')
        return stats.map(lambda f: f.set('fecha', d).setGeometry(None))

    por_bloque = max(1, 4500 // max(n_lotes, 1))
    lista = col.toList(n_esc)
    filas = []
    for i in range(0, n_esc, por_bloque):
        sub = ee.ImageCollection(lista.slice(i, min(i + por_bloque, n_esc)))
        trozo = sub.map(por_escena).flatten().getInfo()['features']
        filas.extend(f['properties'] for f in trozo)
        if verbose:
            print('  [S1] escenas %d-%d/%d: %d filas'
                  % (i + 1, min(i + por_bloque, n_esc), n_esc, len(filas)), flush=True)
    df = pd.DataFrame(filas)
    if df.empty:
        return df
    df = df.rename(columns={'RVI_mean': 'RVI', 'VV_lin_mean': 'VV_lin',
                            'VH_lin_mean': 'VH_lin', 'RVI_count': 'n_px'})
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['orbita'] = '%s-%s' % (o, p)
    # El radar no tiene nubes: toda observacion es plena. La columna existe para
    # que el criterio compartido no tenga que saber de donde vino el dato.
    df['calidad'] = 'pleno'
    cols = ['lote_id', 'fecha', 'area_ha', 'RVI', 'VV_lin', 'VH_lin', 'n_px',
            'calidad', 'orbita']
    df = df[[c for c in cols if c in df.columns]]
    # Con dos frames del mismo dia y misma orbita se conserva el de MEJOR soporte,
    # no uno arbitrario: quedarse con el de 3 pixeles en vez del completo es lo
    # mismo que no medir. El camino optico ya lo hacia asi (series.py).
    if 'n_px' in df.columns:
        df['n_px'] = pd.to_numeric(df['n_px'], errors='coerce').fillna(0)
        df = df.sort_values(['lote_id', 'fecha', 'n_px'])
    else:
        df = df.sort_values(['lote_id', 'fecha'])
    df = df.drop_duplicates(['lote_id', 'fecha'], keep='last')
    if verbose:
        print('[S1] %d filas | %d lotes | %d fechas'
              % (len(df), df.lote_id.nunique(), df.fecha.nunique()))
    return df.reset_index(drop=True)


def cambio_estructural(df_radar, fecha, cohortes=None, z=Z_CAMBIO,
                       caducidad_dias=30):
    """Por lote: ¿el radar vio un cambio grueso, no vio nada, o no tiene dato?

    Se usa el MISMO criterio temporal que el optico —residuo contra la mediana de
    la cohorte en cada fecha, estandarizado por MAD transversal— pero con un umbral
    mas alto y UN solo eje. No se acumula con EWMA: acá interesa el evento abrupto,
    no el desvio sostenido, que es lo que el radar no puede atribuir.

    Devuelve {lote_id: ('CAMBIO'|'SIN CAMBIO'|'SIN DATO RADAR', dias_atras)}.
    """
    import numpy as np
    if df_radar is None or df_radar.empty:
        return {}
    d = df_radar.copy()
    d['fecha'] = pd.to_datetime(d['fecha'])
    f = pd.Timestamp(fecha)
    d = d[d['fecha'] <= f]
    if d.empty:
        return {}
    if cohortes is not None:
        d = d.merge(cohortes, on='lote_id', how='left')
    if 'cohorte' not in d.columns:
        d['cohorte'] = 'unica'

    ref = d.groupby(['cohorte', 'fecha'])['RVI'].median().rename('ref')
    d = d.join(ref, on=['cohorte', 'fecha'])
    d['resid'] = d['RVI'] - d['ref']

    # QUITARLE AL LOTE SU PROPIO DESNIVEL. Sin este paso, un lote consistentemente
    # mas rugoso o mas humedo que sus vecinos —otra variedad, otro suelo, otro
    # rastrojo, otra orientacion de siembra— queda marcado toda la campaña. Eso
    # seria volver a preguntar "¿este lote es distinto de los demas?", que es la
    # nula espacial FALSA POR CONSTRUCCION que todo el motor evita. Lo cazo una
    # prueba: un desnivel constante de +0,10 en RVI salia como CAMBIO.
    # La linea base sale de las primeras observaciones, no de la serie entera: si
    # se usa toda, un evento largo entra en su propia referencia y se anula solo.
    from .ranking import N_BASE
    d = d.sort_values(['lote_id', 'fecha'])
    base = (d.groupby('lote_id').head(N_BASE)
             .groupby('lote_id')['resid'].median().rename('base'))
    d = d.merge(base, on='lote_id', how='left')
    d['centrado'] = d['resid'] - d['base'].fillna(0)

    # Escala transversal POR FECHA, igual que el criterio optico: una escala fija
    # para toda la campaña queda bien calibrada al principio y mal despues.
    # Por (COHORTE, fecha), no por fecha sola: el residuo se calcula DENTRO de la
    # cohorte, asi que mezclar cohortes de dispersion distinta descalibra el z y
    # sube en el ranking a la cohorte mas homogenea.
    esc = d.groupby(['cohorte', 'fecha'])['centrado'].transform(
        lambda v: 1.4826 * np.nanmedian(np.abs(v - np.nanmedian(v))))
    # Piso con la mediana temporal: una fecha donde todos los lotes coinciden daria
    # MAD ~ 0 y el z explotaria, marcando la cartera entera.
    piso = float(np.nanmedian(esc)) * 0.33 if np.isfinite(np.nanmedian(esc)) else 0.0
    d['z'] = d['centrado'] / esc.fillna(piso).clip(lower=max(piso, 1e-6))

    # Tamaño de la cohorte POR FECHA: si la mediana se calcula sobre pocos lotes no
    # es una referencia, es el propio lote mirandose al espejo.
    n_coh = d.groupby(['cohorte', 'fecha'])['RVI'].transform('size')
    d = d.assign(_n_coh=n_coh)

    out = {}
    for lid, g in d.sort_values('fecha').groupby('lote_id'):
        ult = g.iloc[-1]
        dias = int((f - ult['fecha']).days)
        n_obs = int(g['RVI'].notna().sum())
        n_px = ult.get('n_px')
        if dias > caducidad_dias:
            out[str(lid)] = ('SIN DATO RADAR', dias)
        elif int(ult.get('_n_coh', 0) or 0) < MIN_LOTES_COHORTE_RADAR:
            # Con pocos lotes en la cohorte, resid ~ 0 por construccion y el z se
            # va al piso: SIN CAMBIO garantizado pase lo que pase en el campo.
            out[str(lid)] = ('SIN DATO RADAR', dias)
        elif n_obs < MIN_OBS_RADAR:
            # La linea base se come las primeras N_BASE observaciones: hasta que no
            # haya al menos una de fase II, el lote es inmune por construccion.
            out[str(lid)] = ('SIN DATO RADAR', dias)
        elif pd.notna(n_px) and float(n_px) < MIN_PX_RADAR:
            # Un lote en el borde de la pasada, con 2 pixeles utiles sobre 30 ha,
            # produce un RVI medio finito y un z finito. No es una medicion.
            out[str(lid)] = ('SIN DATO RADAR', dias)
        elif not pd.notna(ult['z']):
            # z NaN = el RVI vino enmascarado o sin retorno util. Antes esto caia
            # en el else y se reportaba 'SIN CAMBIO': el informe le decia al
            # productor "el radar no detecto cambio" sobre un lote que NADIE MIRO.
            # Es falsa tranquilidad, el modo de falla contra el que esta escrito
            # todo el paquete. Sin dato es sin dato.
            out[str(lid)] = ('SIN DATO RADAR', dias)
        elif abs(float(ult['z'])) >= z:
            out[str(lid)] = ('CAMBIO', dias)
        else:
            out[str(lid)] = ('SIN CAMBIO', dias)
    return out


def resumen(estados):
    """Contadores para el informe. Vacio si no hubo radar."""
    if not estados:
        return None
    v = [e for e, _ in estados.values()]
    return {'cambio': v.count('CAMBIO'),
            'sin_cambio': v.count('SIN CAMBIO'),
            'sin_dato': v.count('SIN DATO RADAR'),
            'total': len(v)}
