"""Diseño del muestreo de validacion (Puertas 4.1 y 4.2).

POR QUE ESTO VA ANTES DE OCTUBRE Y NO DESPUES
---------------------------------------------
Una vez que la campaña arranca, el muestreo ya no se puede diseñar sin sesgar el
resultado. Y hay un sesgo especifico que arruina la validacion entera:

**SESGO DE VERIFICACION** (Begg & Greenes 1983, 10.2307/2530820): si el tecnico solo
va a los lotes que el sistema marco en rojo, el sistema SIEMPRE parece excelente y
nunca se sabe cuantos focos se escaparon. La precision sale alta por construccion y
no significa nada.

La solucion de diseño (Olofsson et al. 2014, 10.1016/j.rse.2014.02.015) es sortear
tambien en el VERDE, sobremuestrear el rojo porque ahi esta la señal, y **guardar las
probabilidades de inclusion** para poder corregir despues. Sin esas probabilidades el
sobremuestreo del rojo contamina cualquier estimacion poblacional.

QUE NO HACE ESTE MODULO
-----------------------
No decide a que lotes mandar al tecnico en la operacion normal: eso es `ranking.py`.
Esto es el instrumento de MEDICION del sistema, que corre en paralelo y por diseño
manda a lugares donde el sistema dijo que no pasaba nada.
"""
import math

import numpy as np
import pandas as pd

# Los tres estratos del diseño. El verde no es opcional: es el unico que puede
# revelar los falsos negativos, que son justo los que el operador nunca ve.
ESTRATOS = ('ATENCION', 'VIGILANCIA', 'SIN SEÑAL')
# 'SIN DATO' queda FUERA: no es un veredicto del criterio, es la ausencia de
# observacion. Meterlo como estrato mezclaria "no vi nada" con "mire y no habia nada".
EXCLUIDOS = ('SIN DATO',)

Z = {0.80: 1.2816, 0.90: 1.6449, 0.95: 1.9600, 0.99: 2.5758}


def _z(conf):
    if conf not in Z:
        raise ValueError('confianza soportada: %s' % sorted(Z))
    return Z[conf]


def n_para_proporcion(p_esperada, semiancho, N=None, confianza=0.95):
    """Tamaño de muestra para estimar una proporcion con el IC pedido.

    `semiancho` es la mitad del ancho del IC (d). Si se pasa N, aplica correccion por
    poblacion finita. Devuelve un entero >= 1.

    OJO CON LA PREVALENCIA BAJA: n crece como p(1-p)/d^2, pero lo que importa es el
    ERROR RELATIVO. Estimar una prevalencia del 5% con +-5 puntos es inutil (el IC
    cubre desde 0 hasta el doble). Por eso `dimensionar()` reporta el error relativo
    y no solo el n.
    """
    if not (0 < p_esperada < 1):
        raise ValueError('p_esperada debe estar en (0,1), es %r' % p_esperada)
    if semiancho <= 0:
        raise ValueError('semiancho debe ser > 0')
    z = _z(confianza)
    n = (z ** 2) * p_esperada * (1 - p_esperada) / (semiancho ** 2)
    if N:
        n = n / (1 + (n - 1) / N)          # correccion por poblacion finita
    return max(1, int(math.ceil(n)))


def dimensionar(N_por_estrato, p_esperada, semiancho=0.10, confianza=0.95,
                K_por_ronda=None, rondas_disponibles=None):
    """Cuantos lotes hay que visitar por estrato, y si el cliente puede pagarlo.

    Devuelve un DataFrame por estrato y un dict con el veredicto. La pregunta que
    contesta no es "cuantos", es **"alcanza el año con la capacidad real del cliente"**.
    """
    filas = []
    for e in ESTRATOS:
        N = int(N_por_estrato.get(e, 0))
        if N <= 0:
            filas.append(dict(estrato=e, N=N, n=0, frac=float('nan'),
                              nota='sin lotes en este estrato'))
            continue
        n = min(N, n_para_proporcion(p_esperada, semiancho, N=N, confianza=confianza))
        filas.append(dict(estrato=e, N=N, n=n, frac=n / N, nota=''))
    d = pd.DataFrame(filas)

    n_total = int(d['n'].sum())
    err_rel = semiancho / p_esperada
    ver = {
        'n_total': n_total,
        'p_esperada': p_esperada,
        'semiancho': semiancho,
        'confianza': confianza,
        'error_relativo': err_rel,
        'avisos': [],
    }
    if err_rel > 1.0:
        ver['avisos'].append(
            'El IC (+-%.0f pp) es MAS ANCHO que la prevalencia esperada (%.0f%%): el '
            'resultado no va a distinguir "funciona" de "no funciona". Achicar el '
            'semiancho o aceptar que la campaña no concluye nada.'
            % (100 * semiancho, 100 * p_esperada))
    elif err_rel > 0.5:
        ver['avisos'].append(
            'Error relativo %.0f%%: el IC va a cubrir de %.0f%% a %.0f%%. Sirve para '
            'descartar extremos, no para afirmar una cifra.'
            % (100 * err_rel, 100 * max(0, p_esperada - semiancho),
               100 * (p_esperada + semiancho)))

    if K_por_ronda and rondas_disponibles:
        capacidad = int(K_por_ronda) * int(rondas_disponibles)
        ver['capacidad_campaña'] = capacidad
        ver['alcanza'] = capacidad >= n_total
        if not ver['alcanza']:
            ver['avisos'].append(
                'NO ALCANZA: hacen falta %d visitas y la capacidad declarada es %d '
                '(K=%d x %d rondas). Opciones: subir K, bajar la confianza, aceptar un '
                'IC mas ancho, o validar solo un subconjunto de estratos y declararlo.'
                % (n_total, capacidad, K_por_ronda, rondas_disponibles))
    return d, ver


def sortear(rank, N_por_estrato=None, n_por_estrato=None, semilla=0,
            columna_estado='estado', columna_id='lote_id'):
    """Sorteo aleatorio DENTRO de cada estrato, guardando la probabilidad de inclusion.

    `rank` es la salida de `ranking.ranking()` SIN cortar por K: hace falta la
    poblacion entera, incluido el verde, que es el que el operador nunca visitaria.

    Cada fila sale con:
      estrato          — el veredicto del sistema en el momento del sorteo
      prob_inclusion   — n_h / N_h. Sin esto, el sobremuestreo del rojo sesga
                         cualquier estimacion poblacional posterior
      peso_diseño      — 1 / prob_inclusion
    """
    if rank is None or rank.empty:
        return pd.DataFrame()
    d = rank[~rank[columna_estado].isin(EXCLUIDOS)].copy()
    if d.empty:
        return pd.DataFrame()

    rng = np.random.default_rng(semilla)
    n_por_estrato = n_por_estrato or {}
    partes = []
    for e in ESTRATOS:
        pool = d[d[columna_estado] == e]
        N = len(pool)
        if N == 0:
            continue
        n = int(n_por_estrato.get(e, 0))
        if n <= 0:
            continue
        n = min(n, N)
        idx = rng.choice(pool.index.to_numpy(), size=n, replace=False)
        sel = pool.loc[idx].copy()
        sel['estrato'] = e
        sel['N_estrato'] = N
        sel['n_estrato'] = n
        sel['prob_inclusion'] = n / N
        sel['peso_diseño'] = N / n
        partes.append(sel)

    if not partes:
        return pd.DataFrame()
    out = pd.concat(partes, ignore_index=True)
    # El orden de visita se baraja: si el tecnico recorre primero todos los rojos,
    # el orden mismo le revela el estrato y el ciego se cae solo.
    out = out.sample(frac=1.0, random_state=semilla).reset_index(drop=True)
    out['orden_visita'] = np.arange(1, len(out) + 1)
    return out


def a_geojson_ciego(muestra, geoms_por_id, ruta):
    """Emite el GeoJSON de la muestra SIN revelar el estrato.

    El estrato viaja en el archivo porque hace falta para el analisis, pero con nombre
    `_estrato_oculto` y acompañado de `ciego: true`, para que ninguna vista lo pinte por
    accidente. La app ya sabe guardar y no mostrar (MODO_CIEGO).

    Si el tecnico sabe que va a un rojo, encuentra algo: el ciego no es formalismo, es
    lo que hace que el numero final signifique algo.
    """
    import json
    feats = []
    vistos = set()
    for _, r in muestra.iterrows():
        lid = str(r['lote_id'])
        if lid in vistos:
            raise RuntimeError('lote_id duplicado en la muestra: %s' % lid)
        vistos.add(lid)
        g = geoms_por_id.get(lid)
        if g is None:
            continue
        feats.append({
            'type': 'Feature',
            'geometry': g,
            'properties': {
                'lote_id': lid,
                'orden': int(r['orden_visita']),
                'ciego': True,
                '_estrato_oculto': r['estrato'],
                'prob_inclusion': float(r['prob_inclusion']),
                'peso_diseño': float(r['peso_diseño']),
                'status': 'pending',
            },
        })
    with open(ruta, 'w', encoding='utf-8') as fh:
        json.dump({'type': 'FeatureCollection', 'features': feats}, fh,
                  ensure_ascii=False)
    return len(feats)
