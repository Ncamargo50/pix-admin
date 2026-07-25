"""Cohorte de siembra ESTIMADA por fenologia, cuando no hay fecha declarada.

`ESPECIFICACION.md` Paso 2 la declara obligatoria: con lotes escalonados, sin cohorte
lo que se mide es la fecha de siembra, no la plaga. Y §5 Paso 0 dice explicitamente que,
a falta del dato, hay que derivarla del satelite y **rotularla como estimada**.

Medido el 2026-07-24 sobre HDS: con cohorte unica el criterio marcaba 1,3% de media
contra un control nulo de 2,0% — o sea NO DISCRIMINABA NADA. La hipotesis era que la
trayectoria mediana de una cohorte que mezcla estadios no describe a ningun lote, los
residuos quedan grandes y ruidosos, y la escala por fecha se infla hasta que todo parece
normal. Este modulo existe para poder falsarla.

METODO — fecha de emergencia por MITAD DE AMPLITUD PROPIA (half-max del rango del propio
lote sobre la rama ascendente). Es el estimador estandar de "greenup" en fenologia
satelital y es RELATIVO a cada lote: no usa ningun umbral absoluto de NDVI, que no
transferiria entre cultivares ni sitios (Decision 2 de la especificacion).
"""
import numpy as np
import pandas as pd

# Ancho del bin de cohorte, en dias. 15 dias es la ventana con la que se planifica la
# siembra en la practica y es ~1 estadio fenologico en soya de verano.
BIN_DIAS = 15
MIN_OBS_FENOLOGIA = 5      # con menos puntos la curva no es interpretable
MIN_AMPLITUD = 0.15        # NDVI: por debajo de esto no hubo un ciclo, hubo ruido


def _emergencia(fechas, ndvi):
    """Fecha en que el lote cruza la mitad de SU PROPIA amplitud, subiendo.

    Devuelve None si la serie no describe un ciclo (amplitud chica, sin rama
    ascendente, o muy pocos puntos). No se inventa una cohorte donde no hay ciclo.
    """
    ok = np.isfinite(ndvi)
    if ok.sum() < MIN_OBS_FENOLOGIA:
        return None
    f, v = fechas[ok], ndvi[ok]
    orden = np.argsort(f)
    f, v = f[orden], v[orden]
    # suavizado minimo: mediana movil de 3, para que un pico de una escena no fije la fecha
    if len(v) >= 3:
        v = pd.Series(v).rolling(3, center=True, min_periods=1).median().to_numpy()
    lo, hi = float(np.nanmin(v)), float(np.nanmax(v))
    if hi - lo < MIN_AMPLITUD:
        return None
    medio = lo + 0.5 * (hi - lo)
    i_max = int(np.nanargmax(v))
    if i_max == 0:
        return None                      # ya estaba en su maximo: no se ve la emergencia
    # primer cruce ascendente del medio, ANTES del maximo
    for i in range(1, i_max + 1):
        if v[i - 1] < medio <= v[i]:
            # interpolacion lineal entre las dos fechas
            t0 = pd.Timestamp(f[i - 1]).value
            t1 = pd.Timestamp(f[i]).value
            frac = (medio - v[i - 1]) / max(v[i] - v[i - 1], 1e-9)
            return pd.Timestamp(int(t0 + frac * (t1 - t0)))
    return None


def estimar(df, col_ndvi='NDVI', solo_pleno=True, bin_dias=BIN_DIAS, verbose=True):
    """Agrega la columna `cohorte` al DataFrame de series, estimada por fenologia.

    La cohorte se rotula SIEMPRE como `EST-<fecha>` para que en el entregable quede
    explicito que es estimada y no declarada. Los lotes sin ciclo interpretable quedan
    en `EST-SIN-CICLO` y se tratan como una cohorte aparte, no se mezclan con el resto.
    """
    d = df.copy()
    base = d[d['calidad'] == 'pleno'] if (solo_pleno and 'calidad' in d) else d
    emer = {}
    for lote, g in base.groupby('lote_id'):
        g = g.sort_values('fecha')
        emer[lote] = _emergencia(g['fecha'].to_numpy(), g[col_ndvi].to_numpy(dtype=float))

    validas = [v for v in emer.values() if v is not None]
    if not validas:
        d['cohorte'] = 'EST-SIN-CICLO'
        if verbose:
            print('[cohorte] ningun lote tiene ciclo interpretable: cohorte unica')
        return d

    ref = min(validas)
    def _bin(v):
        if v is None:
            return 'EST-SIN-CICLO'
        k = int((v - ref).days // bin_dias)
        ini = ref + pd.Timedelta(days=k * bin_dias)
        return 'EST-' + str(ini.date())

    d['cohorte'] = d['lote_id'].map({k: _bin(v) for k, v in emer.items()})
    if verbose:
        vc = d.groupby('cohorte')['lote_id'].nunique().sort_index()
        sin = int((d['cohorte'] == 'EST-SIN-CICLO').groupby(d['lote_id']).any().sum())
        print('[cohorte] %d cohortes ESTIMADAS por fenologia (bin %d d) | %d lotes sin ciclo'
              % (len(vc) - (1 if sin else 0), bin_dias, sin))
        for c, n in vc.items():
            print('   %-16s %3d lotes' % (c, n))
    return d
