"""Metricas de la campaña de validacion (Puerta 4.4).

QUE SE MIDE Y QUE NO
--------------------
**NUNCA exactitud global.** Con prevalencia baja, "no pasa nada en ningun lote" da 95%
de exactitud y es un sistema inutil. Por eso este modulo no la calcula: no es una
omision, es la decision. Las metricas correctas con prevalencia baja son precision,
recall y PR-AUC, siempre con la prevalencia declarada al lado.

POR QUE HACEN FALTA PESOS DE DISEÑO
-----------------------------------
El muestreo SOBREMUESTREA el rojo a proposito (ahi esta la señal). Si despues se
promedian los hallazgos sin corregir, la prevalencia estimada sale inflada: se estaria
midiendo la prevalencia del rojo, no la del campo. Cada estimacion poblacional de aca
usa la estructura del diseño (N_h conocidos, muestreo aleatorio simple dentro de cada
estrato), que es el estimador estratificado clasico:

    p = Σ_h (N_h/N) · p_h
    Var(p) = Σ_h (N_h/N)² · (1 − n_h/N_h) · p_h(1−p_h)/(n_h − 1)

El (1 − n_h/N_h) es la correccion por poblacion finita: si se visito TODO un estrato,
ese estrato no aporta incertidumbre.

LIMITE HONESTO
--------------
Con n chico por estrato (que es lo esperable en la primera campaña), los IC normales
subcubren. Se reporta `n_mínimo_por_estrato` para que quien lea sepa cuanto confiar, y
por debajo de 5 observaciones en un estrato se marca el resultado como no concluyente
en vez de imprimir un numero con dos decimales que nadie deberia creer.
"""
import numpy as np
import pandas as pd

from .muestreo import ESTRATOS

Z95 = 1.9600
N_MINIMO_CONFIABLE = 5


def ic_wilson(exitos, n, z=None):
    """IC de Wilson para una proporcion. SIN correccion por poblacion finita.

    POR QUE HACE FALTA Y POR QUE SIN fpc.
    La PRECISION del sistema —de los lotes a los que mando, cuantos tenian
    problema— es un parametro de RENDIMIENTO que tiene que generalizar a la
    proxima ronda, no un total finito de esta. El estimador de diseño con fpc es
    correcto para la PREVALENCIA del campo (ahi si hay una poblacion finita que se
    quiere estimar), y **catastrofico para la precision**: cuando un estrato se
    censa (n == N) la fpc vale 0 y la varianza da 0.

    Medido sobre el dimensionamiento REAL de HDS (4 ATENCION + 2 VIGILANCIA, que
    `dimensionar` manda visitar enteros): el informe imprimia
    `precision 50,0% IC95 [50,0% - 50,0%]` sobre SEIS observaciones. Un intervalo
    de ancho CERO. `VALIDACION.md` dice que con n=6 el intervalo es +-44 puntos.

    Wilson y no la normal simple porque con n chico y p cerca de 0 o de 1 la normal
    devuelve limites fuera de [0,1] y un ancho ridiculamente angosto.
    """
    z = Z95 if z is None else z
    if n <= 0:
        return (float('nan'), float('nan'))
    p = exitos / n
    d = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / d
    medio = (z / d) * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, centro - medio), min(1.0, centro + medio))


def _p_var_estrato(n, N, exitos):
    """Proporcion y varianza dentro de un estrato (SRS sin reemplazo)."""
    if n <= 0:
        return float('nan'), float('nan')
    p = exitos / n
    if n < 2:
        # Con una sola observacion no hay varianza muestral. Se declara, no se inventa.
        return p, float('nan')
    fpc = max(0.0, 1.0 - n / N) if N else 1.0
    return p, fpc * p * (1 - p) / (n - 1)


def _resumen_estratos(val, col_estrato='estrato', col_hallazgo='hubo_problema',
                      col_N='N_estrato'):
    filas = []
    for e in ESTRATOS:
        d = val[val[col_estrato] == e]
        n = len(d)
        if n == 0:
            continue
        N = int(d[col_N].iloc[0])
        exitos = int(d[col_hallazgo].astype(bool).sum())
        p, var = _p_var_estrato(n, N, exitos)
        filas.append(dict(estrato=e, N=N, n=n, con_problema=exitos, p=p, var=var))
    return pd.DataFrame(filas)


def _combinar(res, estratos):
    """Estimador estratificado sobre un subconjunto de estratos."""
    d = res[res['estrato'].isin(estratos)]
    if d.empty:
        return float('nan'), float('nan'), 0, 0, 0
    Ntot = d['N'].sum()
    if Ntot == 0:
        return (float('nan'), float('nan'), 0, int(d['n'].sum()),
                int(d['con_problema'].sum()))
    w = d['N'] / Ntot
    p = float((w * d['p']).sum())
    # `fillna(0)` sobre la varianza de un estrato con n=1 la convierte en CERO y
    # angosta el IC sin avisar: el `nan` honesto se perdia en el camino. Se propaga.
    var = float((w ** 2 * d['var']).sum()) if d['var'].notna().all() else float('nan')
    return p, var, int(Ntot), int(d['n'].sum()), int(d['con_problema'].sum())


def _ic(p, var, z=Z95):
    if not np.isfinite(p) or not np.isfinite(var) or var < 0:
        return (float('nan'), float('nan'))
    h = z * np.sqrt(var)
    return (max(0.0, p - h), min(1.0, p + h))


def evaluar(val, col_estrato='estrato', col_hallazgo='hubo_problema',
            col_N='N_estrato'):
    """Metricas de la campaña. `val` = muestra sorteada + lo que encontro el tecnico.

    `hubo_problema` es el veredicto de campo (bool). El registro negativo — el tecnico
    que llego y no encontro nada — es un dato tan valido como el positivo: es el unico
    que permite medir los falsos positivos.
    """
    res = _resumen_estratos(val, col_estrato, col_hallazgo, col_N)
    if res.empty:
        return {'concluyente': False, 'motivo': 'no hay observaciones de campo'}

    alertados = ['ATENCION', 'VIGILANCIA']
    prec, var_prec, N_al, n_al, exitos_al = _combinar(res, alertados)
    prev, var_prev, N_tot, n_tot, _ = _combinar(res, list(ESTRATOS))

    # Recall = P(alertado | problema). Cociente de dos totales estimados; el IC seria
    # por metodo delta y con n chico no aporta, asi que se reporta el punto y se declara.
    tot_prob_al = float((res[res['estrato'].isin(alertados)]['N']
                         * res[res['estrato'].isin(alertados)]['p']).sum())
    tot_prob_all = float((res['N'] * res['p']).sum())
    recall = tot_prob_al / tot_prob_all if tot_prob_all > 0 else float('nan')

    # `_resumen_estratos` OMITE los estratos con n=0, asi que `res['n'].min()` no los
    # ve: con 30 visitas solo en verde el informe salia `concluyente: si` y precision
    # `nan`, sin un solo lote alertado visitado.
    n_min = int(res['n'].min())
    n_alertados_vistos = int(res[res['estrato'].isin(alertados)]['n'].sum())
    faltan = res[res['n'] < N_MINIMO_CONFIABLE]['estrato'].tolist()
    verde = res[res['estrato'] == 'SIN SEÑAL']

    out = {
        'concluyente': (n_min >= N_MINIMO_CONFIABLE and not verde.empty
                        and n_alertados_vistos >= N_MINIMO_CONFIABLE),
        'n_alertados_vistos': n_alertados_vistos,
        'por_estrato': res,
        'precision_en_alerta': prec,
        # WILSON, no el IC de diseño: la precision generaliza, no es un total finito.
        # Con los estratos censados la fpc anulaba la varianza y salia ancho CERO.
        'precision_ic95': ic_wilson(exitos_al, n_al),
        'precision_n': n_al,
        'prevalencia': prev,
        'prevalencia_ic95': _ic(prev, var_prev),
        'recall_aprox': recall,
        'n_total': n_tot,
        'n_minimo_por_estrato': n_min,
        'lotes_alertados_en_poblacion': N_al,
        'lotes_en_poblacion': N_tot,
        'avisos': [],
    }
    if n_alertados_vistos == 0:
        out['avisos'].append(
            'NO SE VISITO NINGUN LOTE ALERTADO. La precision es la metrica que el '
            'producto vende y no se pudo estimar: sale `nan`, no cero. El resultado '
            'NO es concluyente por mas visitas en verde que haya.')
    elif n_alertados_vistos < N_MINIMO_CONFIABLE:
        out['avisos'].append(
            'Solo %d lote(s) alertado(s) visitado(s): la precision no distingue nada '
            'a esta altura. Hacen falta 40-60 acumulados a lo largo de la campaña '
            '(ver campana.agregar).' % n_alertados_vistos)
    if verde.empty:
        # Sin verde no hay forma de saber cuantos focos se escaparon: la precision sale
        # alta por construccion. Es el sesgo de verificacion, y invalida la campaña.
        out['avisos'].append(
            'NO SE VISITO NINGUN LOTE EN VERDE. Sin el estrato verde no se pueden medir '
            'los falsos negativos y la precision esta sesgada al alza por construccion '
            '(sesgo de verificacion). El resultado NO es concluyente.')
    if faltan:
        out['avisos'].append(
            'Estratos con menos de %d observaciones (%s): sus proporciones son ruido, '
            'y el IC normal subcubre. Tratar como preliminar.'
            % (N_MINIMO_CONFIABLE, ', '.join(faltan)))
    if np.isfinite(prev) and prev > 0 and np.isfinite(prec):
        # La comparacion que importa: ¿el sistema mejora sobre ir al azar?
        out['lift'] = prec / prev
        if prec <= prev:
            out['avisos'].append(
                'La precision en los lotes alertados (%.1f%%) NO supera a la prevalencia '
                'del campo (%.1f%%): dirigir el scouting con el mapa no rindio mas que '
                'ir al azar. Es un resultado valido y hay que reportarlo como tal.'
                % (100 * prec, 100 * prev))
    return out


def pr_auc(val, col_score='score', col_hallazgo='hubo_problema', col_peso='peso_diseño'):
    """Area bajo la curva precision-recall, PONDERADA por el diseño.

    Sin los pesos, el sobremuestreo del rojo infla la curva: los positivos del rojo
    pesarian lo mismo que los del verde, cuando en el campo hay muchos mas lotes verdes
    por cada rojo. Devuelve nan si no hay ambas clases (con una sola clase la curva no
    esta definida, y devolver 0,5 seria inventar).
    """
    d = val.dropna(subset=[col_score]).copy()
    if d.empty:
        return float('nan'), pd.DataFrame()
    y = d[col_hallazgo].astype(bool).to_numpy()
    if y.all() or not y.any():
        return float('nan'), pd.DataFrame()
    w = (d[col_peso].to_numpy().astype(float) if col_peso in d
         else np.ones(len(d)))
    s = d[col_score].to_numpy().astype(float)

    orden = np.argsort(-s)
    y, w, s = y[orden], w[orden], s[orden]
    tp = np.cumsum(w * y)
    fp = np.cumsum(w * ~y)
    total_pos = float((w * y).sum())
    prec = tp / np.maximum(tp + fp, 1e-12)
    rec = tp / total_pos

    curva = pd.DataFrame({'umbral': s, 'precision': prec, 'recall': rec})
    # Trapecio sobre recall. Se antepone (0, precision del primer punto) para no
    # extrapolar hacia recall=0 con una precision inventada.
    r = np.concatenate([[0.0], rec])
    p = np.concatenate([[prec[0]], prec])
    return float(np.trapezoid(p, r)) if hasattr(np, 'trapezoid') else float(np.trapz(p, r)), curva


def informe(res, titulo='Campaña de validacion'):
    """Texto del resultado. Declara la prevalencia SIEMPRE, al lado de la precision."""
    L = ['=' * 72, titulo, '=' * 72]
    if not res.get('por_estrato') is not None:
        pass
    if 'motivo' in res:
        L.append('SIN RESULTADO: ' + res['motivo'])
        return '\n'.join(L)

    L.append('')
    L.append('Muestra: %d lotes visitados sobre %d de la poblacion'
             % (res['n_total'], res['lotes_en_poblacion']))
    L.append('')
    L.append('%-12s %6s %5s %8s %8s' % ('ESTRATO', 'N', 'n', 'c/probl.', 'tasa'))
    for _, r in res['por_estrato'].iterrows():
        L.append('%-12s %6d %5d %8d %7.1f%%'
                 % (r['estrato'], r['N'], r['n'], r['con_problema'], 100 * r['p']))
    L.append('')
    pi = res['precision_ic95']
    vi = res['prevalencia_ic95']
    L.append('Precision en lotes alertados : %.1f%%  IC95 [%.1f%% – %.1f%%]'
             % (100 * res['precision_en_alerta'], 100 * pi[0], 100 * pi[1]))
    L.append('Prevalencia del campo        : %.1f%%  IC95 [%.1f%% – %.1f%%]'
             % (100 * res['prevalencia'], 100 * vi[0], 100 * vi[1]))
    if 'lift' in res:
        L.append('Mejora sobre ir al azar      : %.2fx' % res['lift'])
    L.append('Recall aproximado            : %.1f%%' % (100 * res['recall_aprox']))
    L.append('')
    L.append('(No se reporta exactitud global: con prevalencia baja premia al sistema '
             'que nunca alerta.)')
    if res['avisos']:
        L.append('')
        L.append('AVISOS')
        for a in res['avisos']:
            L.append('  ! ' + a)
    L.append('')
    L.append('CONCLUYENTE: %s' % ('si' if res['concluyente'] else 'NO'))
    return '\n'.join(L)
