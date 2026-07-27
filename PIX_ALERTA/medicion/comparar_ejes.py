# -*- coding: utf-8 -*-
"""MEDICION: que par de ejes discrimina mejor. No es una opinion, es un experimento.

El criterio usa DOS ejes de dosel. El primero (NDMI, humedad) no esta en discusion:
es el unico acceso al agua del dosel que da Sentinel-2. El segundo si, y hoy es
PSRI, que tiene dos debilidades conocidas:

  · usa B2 (azul), la banda de peor relacion senal-ruido sobre vegetacion y la mas
    afectada por la atmosfera residual;
  · mezcla resoluciones: B2 y B4 son nativas de 10 m, B6 de 20 m.

Los candidatos de borde rojo (NDRE con B8A/B5, CIre con B7/B5) son ambos nativos
de 20 m y no tocan el azul.

QUE SE MIDE, Y POR QUE ESO
--------------------------
Una configuracion no es mejor porque marque mas lotes. Marcar mas es trivial: bajas
el umbral. Lo que importa es la SEPARACION entre lo que marca sobre el dato real y
lo que marca sobre la nula — el mismo dato con la serie de cada lote rotada
circularmente, que conserva la autocorrelacion intra-lote y rompe la alineacion con
la trayectoria de la cohorte.

  · tasa_real  = % de lotes en ATENCION/VIGILANCIA sobre el dato
  · tasa_nula  = lo mismo sobre la nula (falsa alarma)
  · separacion = tasa_real - tasa_nula   <- el criterio de decision
  · lift       = tasa_real / tasa_nula   <- cuantas veces por encima del ruido

Se reporta ademas la correlacion entre los z de los dos ejes. El diseno se apoya en
que sean INDEPENDIENTES: si el segundo eje replica al primero, exigir los dos no
agrega evidencia, solo la cuenta dos veces. Un par muy correlacionado es un eje
disfrazado de dos, aunque separe bien.

    python -m medicion.comparar_ejes [--serie salida/serie_HDS.csv] [--rep 20]
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pix_alerta import ranking as rk   # noqa: E402

CANDIDATOS = [
    ('NDMI', 'PSRI'),      # el actual
    ('NDMI', 'NDRE'),
    ('NDMI', 'CIRE'),
]


def _fechas_corte(df, n=8):
    """Fechas de evaluacion repartidas por la campana.

    Medir en UNA sola fecha no compara nada: la diferencia entre 0 y 6 lotes
    marcados un dia cualquiera es ruido de muestreo. La tasa hay que promediarla
    sobre varios cortes, igual que se hace con la nula.
    """
    f = sorted(df.loc[df['calidad'] == 'pleno', 'fecha'].unique())
    if len(f) <= n:
        return f
    # Se descarta el primer tercio: antes de eso los lotes no acumularon las
    # MIN_OBS_LOTE observaciones que el criterio exige y todo sale vacio.
    f = f[len(f) // 3:]
    paso = max(1, len(f) // n)
    return f[::paso][:n]


def _tasa(df, ejes, cortes):
    """% medio de lotes fuera de control sobre varias fechas, y cuantos se evaluan."""
    car = rk.ewma(rk.residuos(df, ejes))
    if car.empty:
        return float('nan'), 0
    tasas, n_ult = [], 0
    for f in cortes:
        r = rk.ranking(car, fecha=f)
        if r.empty:
            continue
        tasas.append(r['estado'].isin(('ATENCION', 'VIGILANCIA')).mean())
        n_ult = max(n_ult, len(r))
    if not tasas:
        return float('nan'), 0
    return float(np.mean(tasas)), n_ult


def _nula(df, ejes, cortes, n_rep, semilla=0):
    """Falsa alarma media, sobre las MISMAS fechas de corte que la tasa real.

    Se reimplementa en vez de usar `ranking.control_nulo` porque aquella evalua
    solo la ultima fecha; comparar una tasa promediada contra una nula de un dia
    seria comparar dos cosas distintas.
    """
    rng = np.random.default_rng(semilla)
    tasas = []
    # La calidad viaja con el valor. Ver ranking.control_nulo: sin esto la nula se
    # evalua sobre 3 lotes y el dato real sobre 96, y la comparacion no significa nada.
    rotables = list(ejes) + ['cobertura', 'n_px', 'calidad', 'FVC', 'NDVI']
    for _ in range(n_rep):
        partes = []
        for _, g in df.sort_values('fecha').groupby('lote_id'):
            g = g.copy()
            n = len(g)
            if n > 2:
                k = int(rng.integers(1, n))
                cols = [c for c in rotables if c in g.columns]
                g[cols] = np.roll(g[cols].to_numpy(), k, axis=0)
            partes.append(g)
        d = pd.concat(partes, ignore_index=True)
        car = rk.ewma(rk.residuos(d, ejes))
        if car.empty:
            continue
        for f in cortes:
            r = rk.ranking(car, fecha=f)
            if not r.empty:
                tasas.append(r['estado'].isin(('ATENCION', 'VIGILANCIA')).mean())
    return float(np.mean(tasas)) if tasas else float('nan')


def _corr_ejes(df, ejes):
    """Correlacion entre los z de los dos ejes, sobre los pares (lote, fecha).

    Es la medida de si el par aporta dos evidencias o una repetida.
    """
    res = rk.residuos(df, ejes)
    if res.empty:
        return float('nan')
    piv = res.pivot_table(index=['lote_id', 'fecha'], columns='eje', values='z')
    piv = piv.dropna()
    if len(piv) < 30 or piv.shape[1] < 2:
        return float('nan')
    return float(np.corrcoef(piv[ejes[0]], piv[ejes[1]])[0, 1])


def _ar1(n, sigma, rho, rng):
    """Ruido AR(1) con varianza marginal sigma^2 y autocorrelacion lag-1 rho."""
    x = np.empty(n)
    x[0] = rng.normal(0, sigma)
    s_e = sigma * np.sqrt(max(1 - rho ** 2, 1e-6))
    for i in range(1, n):
        x[i] = rho * x[i - 1] + rng.normal(0, s_e)
    return x


def nula_sintetica(df, ejes, cortes, n_rep, semilla=0):
    """LA NULA CORRECTA: cada lote sigue la trayectoria de SU cohorte + ruido.

    Por que no sirve la rotacion circular, que es lo que usaba `control_nulo`:

    1. Rotando cada lote un desplazamiento DISTINTO, la mediana por (cohorte, fecha)
       deja de ser una trayectoria fenologica y se aplana — medido sobre HDS, el
       desvio del NDMI mediano de cohorte cae de 0,1338 a 0,1022. El residuo contra
       una referencia plana es mayor, asi que la "nula" dispara mas que el dato real.
       No mide falsa alarma: mide el daño de haber roto la referencia.
    2. Una rotacion CONSERVA los episodios sostenidos, solo los cambia de fecha. El
       EWMA detecta desvios sostenidos, asi que los sigue viendo. Una permutacion que
       preserva justo lo que el estadistico busca no puede ser su nula.

    Acá se construye el mundo donde la hipotesis nula es CIERTA por construccion:
    valor = mediana de la cohorte en esa fecha + ruido AR(1) con la escala y la
    autocorrelacion medidas en el dato real. Ningun lote se aparta de su cohorte,
    asi que TODA alarma es falsa. Eso si es una tasa de falsa alarma.

    Se conservan las fechas, la calidad de cada observacion y el soporte de pixeles:
    la nula tiene que sufrir los mismos huecos de nube que el dato real.
    """
    rng = np.random.default_rng(semilla)
    d0 = df.copy()
    if 'cohorte' not in d0.columns:
        from pix_alerta import cohorte as coh
        d0 = coh.estimar(d0)
    pl = d0[d0['calidad'] == 'pleno']

    # Trayectoria real y parametros del ruido, por eje.
    traj, par = {}, {}
    for eje in ejes:
        t = pl.groupby(['cohorte', 'fecha'])[eje].median().rename('_traj')
        traj[eje] = t
        r = pl.join(t, on=['cohorte', 'fecha'])
        res = (r[eje] - r['_traj']).to_numpy(dtype=float)
        res = res[np.isfinite(res)]
        sigma = 1.4826 * np.nanmedian(np.abs(res - np.nanmedian(res))) if len(res) else 0.0
        rhos = []
        for _, g in r.sort_values('fecha').groupby('lote_id'):
            v = (g[eje] - g['_traj']).to_numpy(dtype=float)
            v = v[np.isfinite(v)]
            if len(v) >= 4 and v.std() > 1e-12:
                rhos.append(np.corrcoef(v[:-1], v[1:])[0, 1])
        rho = float(np.clip(np.median(rhos), 0, 0.95)) if rhos else 0.0
        par[eje] = (float(sigma), rho)

    # CORRELACION ENTRE EJES EN EL RUIDO. Generar los dos ejes independientes
    # favorece al par mas correlacionado: si NDMI y NDRE se mueven juntos tambien
    # cuando no pasa nada, exigir los dos a la vez filtra menos de lo que parece, y
    # la nula independiente no lo refleja. Se usa la correlacion de los residuos
    # observados, que mezcla senal y ruido y por lo tanto es una COTA SUPERIOR: si
    # el ganador sigue ganando con esta nula, gana de verdad.
    e1, e2 = ejes
    r1 = pl.join(traj[e1], on=['cohorte', 'fecha'])
    r2 = pl.join(traj[e2], on=['cohorte', 'fecha'])
    v1 = (r1[e1] - r1['_traj']).to_numpy(dtype=float)
    v2 = (r2[e2] - r2['_traj']).to_numpy(dtype=float)
    ok = np.isfinite(v1) & np.isfinite(v2)
    rho_xy = float(np.corrcoef(v1[ok], v2[ok])[0, 1]) if ok.sum() > 30 else 0.0
    rho_xy = float(np.clip(rho_xy, -0.98, 0.98))

    tasas = []
    for _ in range(n_rep):
        sint = d0.copy()
        ordenado = sint.sort_values('fecha')
        grupos = list(ordenado.groupby('lote_id', sort=True))
        s1, s2 = par[e1][0], par[e2][0]
        n1, n2, filas = [], [], []
        for _, g in grupos:
            a1 = _ar1(len(g), 1.0, par[e1][1], rng)
            a2 = _ar1(len(g), 1.0, par[e2][1], rng)
            # Mezcla de Cholesky: impone corr(x1,x2)=rho_xy conservando la
            # estructura temporal de cada uno.
            n1.append(a1 * s1)
            n2.append((rho_xy * a1 + np.sqrt(max(1 - rho_xy ** 2, 0)) * a2) * s2)
            # El indice se acumula en el MISMO orden que el ruido. Ver
            # ranking.control_nulo: con el indice global ordenado por fecha se
            # rompia la autocorrelacion intra-lote y la nula daba 0,00% siempre.
            filas.append(g.index.to_numpy())
        idx = pd.Index(np.concatenate(filas)) if filas else ordenado.index
        for eje, ru in ((e1, np.concatenate(n1)), (e2, np.concatenate(n2))):
            base = sint.set_index(['cohorte', 'fecha']).index.map(traj[eje])
            s = pd.Series(ru, index=idx).reindex(sint.index)
            sint[eje] = np.asarray(base, dtype=float) + s.to_numpy()
        car = rk.ewma(rk.residuos(sint, ejes))
        if car.empty:
            continue
        for f in cortes:
            r = rk.ranking(car, fecha=f)
            if not r.empty:
                tasas.append(r['estado'].isin(('ATENCION', 'VIGILANCIA')).mean())
    return float(np.mean(tasas)) if tasas else float('nan'), par, rho_xy


def _una_serie(ruta, rep, etiqueta):
    """Corre los candidatos sobre UNA campaña. Devuelve las filas."""
    df = pd.read_csv(ruta, parse_dates=['fecha'])
    faltan = [c for c in ({e for _, e in CANDIDATOS} | {'NDMI'})
              if c not in df.columns]
    if faltan:
        print('  [SALTEADA] %s no trae %s' % (ruta, ', '.join(sorted(faltan))))
        return []
    pl = (df['calidad'] == 'pleno').sum()
    cortes = _fechas_corte(df)
    print('\n### %s — %d filas · %d lotes · %d fechas · %.1f%% plenas · %d cortes'
          % (etiqueta, len(df), df.lote_id.nunique(), df.fecha.nunique(),
             100 * pl / len(df), len(cortes)), flush=True)
    filas = []
    for ejes in CANDIDATOS:
        real, n_lotes = _tasa(df, ejes, cortes)
        nula, par, rxy = nula_sintetica(df, ejes, cortes, rep)
        corr = _corr_ejes(df, ejes)
        sep = real - nula if np.isfinite(real) and np.isfinite(nula) else float('nan')
        lift = real / nula if np.isfinite(nula) and nula > 0 else float('inf')
        filas.append({'campana': etiqueta, 'ejes': ' + '.join(ejes),
                      'lotes_evaluados': n_lotes,
                      'tasa_real_%': 100 * real, 'tasa_nula_%': 100 * nula,
                      'separacion_pp': 100 * sep, 'lift': lift, 'corr_ejes': corr,
                      'rho_ruido': par[ejes[1]][1], 'rho_xy_nula': rxy})
        print('  %-14s evaluados %3d | real %5.2f%% | nula %5.2f%% | sep %+5.2f pp '
              '| lift %5.1fx | corr %+.2f'
              % (filas[-1]['ejes'], n_lotes, 100 * real, 100 * nula, 100 * sep,
                 lift, corr), flush=True)
    return filas


def main(argv=None):
    p = argparse.ArgumentParser(description='Comparacion de pares de ejes')
    p.add_argument('--serie', nargs='+', default=['salida/serie_HDS.csv'],
                   help='una o varias series; con varias se REPLICA la comparacion')
    p.add_argument('--rep', type=int, default=20,
                   help='repeticiones de la nula (mas = menos ruido en la tasa)')
    p.add_argument('--salida', default='medicion/comparacion_ejes.csv')
    a = p.parse_args(argv)

    print('Nula: sintetica (cohorte + AR(1) con correlacion entre ejes), '
          '%d repeticiones' % a.rep)
    filas = []
    for ruta in a.serie:
        et = os.path.splitext(os.path.basename(ruta))[0].replace('serie_HDS_', '')
        filas += _una_serie(ruta, a.rep, et or os.path.basename(ruta))
    if not filas:
        raise SystemExit('[ERROR] ninguna serie utilizable.')
    t = pd.DataFrame(filas)

    print('\n' + '=' * 74)
    if t['campana'].nunique() > 1:
        # Con replicas, lo que decide NO es el mejor resultado de una campaña sino
        # la CONSISTENCIA: un eje que gana en una sola puede estar ajustando el año.
        res = (t.groupby('ejes')
                 .agg(campanas=('campana', 'nunique'),
                      lift_medio=('lift', 'mean'),
                      lift_min=('lift', 'min'),
                      sep_media=('separacion_pp', 'mean'),
                      sep_min=('separacion_pp', 'min'),
                      corr=('corr_ejes', 'mean'))
                 .sort_values('lift_min', ascending=False))
        print('CONSOLIDADO SOBRE %d CAMPANAS' % t['campana'].nunique())
        print(res.to_string(float_format=lambda v: '%7.2f' % v))
        gana = res.index[0]
        print('\nGANA POR PEOR CASO: %s (lift minimo %.1fx sobre %d campanas)'
              % (gana, res.loc[gana, 'lift_min'], res.loc[gana, 'campanas']))
        print('Se decide por el PEOR caso, no por el promedio: un eje que rinde en')
        print('un año y falla en otro no sirve para un servicio anual.')
        ganan_todas = (t.loc[t.groupby('campana')['lift'].idxmax(), 'ejes']
                        .value_counts())
        print('\nGanador por campana: %s' % ganan_todas.to_dict())
        if len(ganan_todas) > 1:
            print('  OJO: el ganador NO es el mismo en todas las campanas. La')
            print('  eleccion no esta cerrada; hace falta mas replicacion.')
    else:
        mejor = t.loc[t['separacion_pp'].idxmax()]
        print('MAYOR SEPARACION: %s (%+.2f pp, lift %.1fx)'
              % (mejor['ejes'], mejor['separacion_pp'], mejor['lift']))
        print('UNA SOLA CAMPANA: no alcanza para cerrar la eleccion.')
    print('=' * 74)

    os.makedirs(os.path.dirname(a.salida) or '.', exist_ok=True)
    t.to_csv(a.salida, index=False)
    print('\n  -> %s' % a.salida)
    return 0


if __name__ == '__main__':
    sys.exit(main())
