# -*- coding: utf-8 -*-
"""Madurez / senescencia de fin de ciclo: funciones PURAS compartidas por el entregable
de orden de cosecha (`entregables/orden_cosecha.py`) y por los arneses de medicion.

Nacen de la auditoria del 2026-08-19 (tres agentes) sobre el informe SF/SA:

1. COMPUERTA DE BRUMA por (unidad, fecha). El caso medido: la escena del 26-may-2026
   tenia B2 0,185-0,19 y PSRI -0,05 sobre dosel y CloudScore+ la dejaba pasar como
   fraccion de pixeles claros (87-100 % con cs>=0,60). Ese unico punto deprimido
   fabrico una diferencia de "emergencia" entre haciendas que NO existia.
   La compuerta es la conjuncion de tres firmas independientes; ninguna sola alcanza:
     - cs_med  : mediana de CloudScore+ sobre la unidad (no la fraccion binaria)
     - PSRI    : la bruma dispersa mas el azul que el rojo -> PSRI se hace NEGATIVO
                 mas alla de lo que un dosel sano da (piso medido -0,059)
     - B2      : azul sobre dosel/suelo despejado <= 0,13 medido en 5 meses de serie;
                 la bruma del 26-may dio 0,185-0,192. OJO: suelo desnudo da 0,07-0,13
                 y NO es bruma — por eso el corte va en 0,15, no en 0,06 (primer intento
                 de esta compuerta, que excluia todas las fechas de suelo desnudo).

2. FACTOR S2C POR NIVEL. La banda B5 de Sentinel-2C esta en 707,1 nm (S2A/B: ~704 nm).
   En el borde rojo el sesgo de CIre escala con la PENDIENTE espectral, o sea con el
   propio CIre: medido ratio S2C/S2A-B ~0,78 con dosel cerrado (CIre 4-5,5), 0,87-0,93
   a CIre 2-4, y ~1 sobre suelo. Un factor CONSTANTE infla el CIre del trigo senescente
   un 15-20 % y puede mover un lote de clase. Modelo: r(c) = 1 + b*c (pasa por 1 en
   c=0: sin dosel no hay borde rojo que desplazar), b ajustado por minimos cuadrados
   sobre pares (escena S2C, interpolacion S2A/B vecina) de la PROPIA serie.
   Correccion: CIre_AB = CIre_C / r(CIre_C)  ->  resolver la implicita
   c_AB = c_C / (1 + b*c_AB), que es lineal: c_AB = (c_C - ... ) — ver corregir_cire.

3. ETIQUETAS DE ESTADO. "Listo / cosechar" queda PROHIBIDO como salida de satelite:
   el fin de la clorofila (CIre en el piso) NO es punto de cosecha — la humedad de
   grano (Embrapa: 16-18 % para iniciar; 13 % maximo comercial) y el PH se miden a
   campo. La clase final se llama "clorofila agotada". Si hay un lote de REFERENCIA
   SECA declarado por el cliente, se agrega el estado "seco como la referencia" =
   CIre y NDMI ambos al nivel de la referencia (el eje que sigue separando cuando la
   clorofila toca piso es el AGUA del dosel: NDMI, B8A/B11).

Sin GEE ni I/O: todo testeable offline (tests/test_madurez.py).
"""
import datetime as dt

# ---------------------------------------------------------------- compuerta de bruma
CS_MED_MIN = 0.80    # mediana de cs_cdf sobre la unidad
PSRI_MIN = -0.02     # PSRI de dosel mas negativo que esto = dispersion azul (bruma)
B2_MAX = 0.15        # azul; despejado da <= 0,13 incluso sobre suelo desnudo


def bruma(cs_med, psri, b2):
    """(es_bruma, razon). Cualquiera de las tres firmas dispara; None = no disponible.

    Devuelve la RAZON para que el informe pueda decir por que se excluyo la fecha:
    'no pude mirar' nunca viaja con el mismo codigo que 'mire y no hay nada'."""
    if cs_med is not None and cs_med < CS_MED_MIN:
        return True, 'cs_med %.2f < %.2f' % (cs_med, CS_MED_MIN)
    if psri is not None and psri < PSRI_MIN:
        return True, 'PSRI %.3f < %.2f (dispersion azul)' % (psri, PSRI_MIN)
    if b2 is not None and b2 > B2_MAX:
        return True, 'B2 %.3f > %.2f' % (b2, B2_MAX)
    return False, ''


def filtrar_bruma(serie):
    """Parte una serie [{fecha, cs_med?, PSRI?, B2?...}] en (limpias, excluidas).
    Las excluidas llevan 'razon'. No muta la entrada."""
    limpias, excluidas = [], []
    for x in serie:
        es, razon = bruma(x.get('cs_med'), x.get('PSRI'), x.get('B2'))
        if es:
            excluidas.append({**x, 'razon': razon})
        else:
            limpias.append(x)
    return limpias, excluidas


# ---------------------------------------------------------------- factor S2C
R_MIN = 0.70         # r nunca baja de esto (fuera del rango medido)


def pares_s2c(serie, max_hueco=18, max_salto=2.0, ref_min=1.0):
    """Pares (CIre_S2C, CIre_interpolado_S2A/B) de una serie de UNA unidad.

    serie: [{fecha 'YYYY-MM-DD', sat 'A'|'B'|'C', CIre}] YA filtrada de bruma.
    - anclas S2A/B a lo sumo `max_hueco` dias a cada lado;
    - se EXCLUYE la subida rapida (emergencia): si la serie se multiplica por mas de
      `max_salto` entre anclas, la interpolacion lineal no vale (medido: daba 0,93
      en plena subida del 31-may cuando el valor con dosel era 0,78);
    - `ref_min`: sin dosel (CIre < 1) el ratio es ruido de suelo, no senal.
    """
    F = lambda s: dt.date.fromisoformat(s)
    ab = [x for x in serie if x['sat'] in ('A', 'B')]
    out = []
    for x in serie:
        if x['sat'] != 'C':
            continue
        f0 = F(x['fecha'])
        ant = [y for y in ab if 0 < (f0 - F(y['fecha'])).days <= max_hueco]
        pos = [y for y in ab if 0 < (F(y['fecha']) - f0).days <= max_hueco]
        if not ant or not pos:
            continue
        a = max(ant, key=lambda y: y['fecha'])
        b = min(pos, key=lambda y: y['fecha'])
        lo, hi = sorted((a['CIre'], b['CIre']))
        if lo <= 0 or hi / max(lo, 1e-9) >= max_salto:
            continue
        t = (f0 - F(a['fecha'])).days / (F(b['fecha']) - F(a['fecha'])).days
        ref = a['CIre'] + t * (b['CIre'] - a['CIre'])
        if ref >= ref_min:
            out.append(dict(fecha=x['fecha'], c=x['CIre'], ref=ref,
                            ratio=x['CIre'] / ref, ancla=(a['fecha'], b['fecha'])))
    return out


def ajustar_b(pares, b_defecto=-0.05, min_pares=3):
    """b de r(c) = 1 + b*c por minimos cuadrados a traves del origen (r-1 vs c).
    Con menos de `min_pares` pares devuelve el valor por defecto MEDIDO en SA/SF
    (2026-08-19: b = -0,050, n=7, ratios 0,77-0,87) y lo declara."""
    if len(pares) < min_pares:
        return b_defecto, False
    num = sum(p['ref'] * 0 + p['c'] * (p['ratio'] - 1) for p in pares)
    den = sum(p['c'] ** 2 for p in pares)
    if den <= 0:
        return b_defecto, False
    return num / den, True


def r_de(cire, b):
    """r(c) con piso: fuera del rango medido no se extrapola la caida."""
    return max(R_MIN, min(1.0, 1.0 + b * cire))


def corregir_cire(cire, sat, b):
    """Lleva un CIre observado a la escala S2A/B.

    Para S2C resuelve la forma consistente: el sesgo depende del CIre VERDADERO
    (escala A/B), no del observado:  c_obs = c_ab * r(c_ab) = c_ab * (1 + b*c_ab).
    Es una cuadratica en c_ab con raiz positiva:
        c_ab = (-1 + sqrt(1 + 4*b*c_obs)) / (2*b)      (b < 0)
    Si el discriminante se anula (c_obs fuera de rango del modelo) se usa el piso
    R_MIN, que es lo mismo que dividir por 0,70."""
    if sat != 'C' or cire is None:
        return cire
    if abs(b) < 1e-9:
        return cire
    disc = 1.0 + 4.0 * b * cire
    if disc <= 0:
        return cire / R_MIN
    c_ab = (-1.0 + disc ** 0.5) / (2.0 * b)
    # respeta el piso: nunca corregir mas que 1/R_MIN
    return min(c_ab, cire / R_MIN) if cire > 0 else c_ab


# ---------------------------------------------------------------- estados
# La palabra "listo" y la palabra "cosecha" NO aparecen: el satelite no las sostiene.
ESTADOS = {0: 'Verde (<15 %)',
           1: 'Caida inicial (15-40 %)',
           2: 'Caida avanzada (40-70 %)',
           3: 'Clorofila agotada (>=70 %)'}
SECO_REF = 'Seco como la referencia'


def estado(avance, psri):
    """Clase relativa por avance de clorofila (misma banda 15/40/70 del entregable
    del 01-ago; solo cambian los rotulos). `avance` en %, respecto del pico propio."""
    if avance < 15 and (psri is None or psri < 0.03):
        return ESTADOS[0], 0
    if avance < 40:
        return ESTADOS[1], 1
    if avance < 70:
        return ESTADOS[2], 2
    return ESTADOS[3], 3


def estado_final(cire, ndmi, ref_cire_p90, ref_ndmi_p90):
    """Con referencia seca declarada: 'seco como la referencia' exige los DOS ejes.
    Cuando la clorofila toca piso (cire <= ref) el eje que decide es el agua (NDMI)."""
    if cire is None or ndmi is None or ref_cire_p90 is None or ref_ndmi_p90 is None:
        return None
    if cire <= ref_cire_p90 and ndmi <= ref_ndmi_p90:
        return SECO_REF
    if cire <= ref_cire_p90:
        return 'Clorofila agotada, dosel aun humedo'
    return None


# ---------------------------------------------------------------- inicio / horquilla
def inicio_cobertura(serie_corr, nivel=1.0):
    """Primer cruce ASCENDENTE de `nivel` en [(fecha, cire_corr)] ordenada.
    Devuelve dict(interp, desde, hasta, hueco_dias) — la HORQUILLA completa
    [ultima fecha < nivel, primera >= nivel], nunca un ± inventado. Es 'inicio de
    cobertura del dosel', NO emergencia (CIre 1,0 ~ NDVI 0,5 = macollaje)."""
    F = lambda s: dt.date.fromisoformat(s) if isinstance(s, str) else s
    pts = [(F(f), v) for f, v in serie_corr if v is not None]
    for j in range(1, len(pts)):
        if pts[j][1] >= nivel > pts[j - 1][1]:
            t = (nivel - pts[j - 1][1]) / (pts[j][1] - pts[j - 1][1])
            d0, d1 = pts[j - 1][0], pts[j][0]
            return dict(interp=(d0 + dt.timedelta(days=(d1 - d0).days * t)).isoformat(),
                        desde=d0.isoformat(), hasta=d1.isoformat(),
                        hueco_dias=(d1 - d0).days)
    return None


# ---------------------------------------------------------------- lote desparejo
# MEDIDO 19-ago-2026 sobre la flota SA/SF (log(CIre) clip 0,05; p90-p10; interior
# erosionado 1 px de 20 m): lotes uniformes 0,63-0,85 · lote con dos plantios en
# estados distintos 1,22. El corte va en el medio. En LOG y no en CIre crudo porque
# el ruido de un cociente escala con el nivel (auditoria 2026-08-19).
# ⚠ LIMITE MEDIDO: la bandera es DE UNA ESCENA. El 01-ago el mismo lote mezclado dio
# 0,36 (uniforme) porque el plantio tardio estaba en su pico y las trayectorias se
# CRUZABAN. La bandera detecta la mezcla cuando los estados divergen; la particion
# declarada por el cliente la cubre siempre.
UMBRAL_DESPAREJO = 1.0

# Dos bloques se reportan JUNTOS cuando su diferencia de avance cae debajo de la
# repetibilidad del avance (%): factor S2C ±4-6 pts + escena a escena. Colapso de
# DISPLAY: la geometria del catalogo no se toca (la fecha de siembra es un hecho).
REPETIBILIDAD_AVANCE = 10.0


def desparejo(cire_vals, umbral=UMBRAL_DESPAREJO):
    """(es_desparejo, dispersion). cire_vals: valores de CIre del lote en la escena
    (interior; lista/array, NaN tolerado). Dispersion = p90-p10 de log(CIre)."""
    import numpy as _np
    v = _np.asarray(cire_vals, float)
    v = v[_np.isfinite(v)]
    if v.size < 50:                       # sin pixeles no hay veredicto
        return False, None
    lv = _np.log(_np.clip(v, 0.05, None))
    d = float(_np.percentile(lv, 90) - _np.percentile(lv, 10))
    return d > umbral, round(d, 2)


def colapsar_bloques(avances, repetibilidad=REPETIBILIDAD_AVANCE):
    """True si TODOS los bloques estan dentro de la repetibilidad entre si:
    se reportan como una sola fila ('bloques convergieron')."""
    a = [x for x in avances if x is not None]
    return len(a) >= 2 and (max(a) - min(a)) <= repetibilidad


# ---------------------------------------------------------------- ventana estimada
# Fecha estimada de cruce por ajuste logistico descendente (auditoria 19-ago: la
# extrapolacion LINEAL sesga largo porque la caida se acelera; la logistica con piso
# anclado en la referencia seca se autovalido — la referencia cruza CIre 1,0 el
# 23-jul, coherente con estar seca a mediados de agosto).
#
# ⚠ ALCANCE DE LA EVIDENCIA (validador 21-ago-2026): la prueba del 21-ago es una
# VERIFICACION DE CONSISTENCIA a 2 dias — el ajuste <=19-ago reprodujo el NDMI del
# 21-ago con error <=0,021, pero una recta por los ultimos 2 puntos pasa casi igual
# (MAE 0,013 vs 0,011); NO valida la fecha extrapolada a 10-30 dias. El eje CIre
# FALLO la misma prueba (sobre-prediccion 0,15-0,38: la clorofila cae mas rapido que
# la cola logistica) — por eso las fechas SOLO se estiman sobre el eje de agua.
# Es una FECHA ESTIMADA de estado espectral ("seco como la referencia"), nunca una
# fecha de cosecha: humedad de grano y PH se miden a campo. Sin verdad de campo,
# la exactitud contra el estado FISICO del lote sigue sin medir.
HORIZONTE_EXTRAPOLACION = 30   # dias mas alla de la ultima escena; mas lejos NO se publica
                               # (el caso b2 21-ago: cruce a 30 d con IC degenerado = no creible)
SIGMA_NDMI_ESCENA = 0.021      # repetibilidad escena-a-escena del NDMI de unidad, MEDIDA
                               # (validador 21-ago: tripletes 31-may/02-jun/05-jun y
                               # 10/12/15-jul vs recta local, n=14: SD 0,021). El rmse del
                               # ajuste con 4-6 puntos y 3 parametros subestima esto 2-3x.


def _logistica(t, A, t0, tau, piso):
    import numpy as _np
    return piso + A / (1.0 + _np.exp((t - t0) / tau))


def ajuste_cruce(serie, piso, nivel, n_boot=400, seed=0,
                 horizonte=HORIZONTE_EXTRAPOLACION, sigma_min=0.0):
    """Fecha estimada en que la serie cruza `nivel` bajando, con intervalo bootstrap.

    serie: [(fecha_iso, valor)] cronologica y SIN bruma. Ajusta
    y(t) = piso + A/(1+exp((t-t0)/tau)) a la fase post-pico (pico inclusive), con
    el piso FIJO (anclado en la referencia seca: el nivel al que un trigo seco
    real LLEGA, medido — no un parametro libre con 4-6 puntos).

    `sigma_min`: PISO DE RUIDO para el bootstrap (parametrico, gaussiano). Con 4-6
    puntos y 3 parametros el rmse subestima el ruido real 2-3x y el intervalo sale
    angosto (cobertura medida ~60-79 % rotulada 95 % — RECHAZADO por el validador
    21-ago). El caller debe pasar la repetibilidad MEDIDA del indice (NDMI:
    SIGMA_NDMI_ESCENA); el sigma efectivo es max(rmse*sqrt(n/(n-3)), sigma_min).

    Devuelve dict(fecha, ic=(desde,hasta), rmse, n, extrapolacion_dias, params),
    dict(alcanzado=True, fecha=ultima_medicion, ...) si la ultima medicion ya esta
    al nivel, o None — y None es un resultado legitimo, nunca lo disfraza un numero:
      - menos de 4 puntos post-pico ('no ajustable'),
      - el ajuste no converge o el nivel no se alcanza (nivel <= piso o A chico),
      - el cruce (o el extremo del intervalo) cae a mas de `horizonte` dias de la
        ultima escena (extrapolar la cola de una logistica no es medir),
      - el bootstrap no converge (<50 cruces) o el intervalo degenera (~0): el caso
        de MENOS confianza jamas sale con MAS aplomo (fecha pelada sin rango).
    """
    import numpy as _np
    if nivel <= piso:
        return None
    F = lambda s: dt.date.fromisoformat(s)
    pts = [(F(f), v) for f, v in serie if v is not None]
    if not pts:
        return None
    # ya cruzo: la ultima MEDICION esta al nivel o debajo. Eso no es una estimacion,
    # es un hecho — nunca mostrar una fecha pasada como "estimada" (auditoria 21-ago).
    if pts[-1][1] <= nivel:
        return dict(alcanzado=True, fecha=pts[-1][0].isoformat(), ic=None,
                    rmse=None, n=len(pts), extrapolacion_dias=0.0, params=None)
    d0 = pts[0][0]
    ts = _np.array([(d - d0).days for d, _ in pts], float)
    ys = _np.array([v for _, v in pts], float)
    j = int(_np.argmax(ys))
    ts, ys = ts[j:], ys[j:]
    if len(ts) < 4:
        return None
    from scipy.optimize import curve_fit
    lims = ([0.05, ts.min() - 40, 1.5], [12, ts.max() + 60, 40])
    try:
        p, _ = curve_fit(lambda t, A, t0, tau: _logistica(t, A, t0, tau, piso),
                         ts, ys, p0=[max(ys.max() - piso, 0.1), ts.mean(), 8.0],
                         bounds=lims, maxfev=20000)
    except Exception:
        return None
    resid = ys - _logistica(ts, *p, piso)
    rmse = float(_np.sqrt(_np.mean(resid ** 2)))

    def _cruce(pp):
        A, t0, tau = pp
        if A <= (nivel - piso):
            return None
        return t0 + tau * _np.log(A / (nivel - piso) - 1.0)

    c0 = _cruce(p)
    if c0 is None:
        return None
    extra = float(c0 - ts.max())
    if extra > horizonte:
        return None
    # bootstrap PARAMETRICO con sigma honesto: rmse corregido por gdl (sqrt(n/(n-3)))
    # y NUNCA por debajo de la repetibilidad medida del indice (sigma_min). El rotulo
    # del intervalo lo fija la cobertura SIMULADA con ese sigma, no el deseo
    # (feedback: auditar lo propio antes de aprobar).
    infl = (len(ts) / max(len(ts) - 3.0, 1.0)) ** 0.5
    sigma_b = max(rmse * infl, sigma_min)
    rng = _np.random.default_rng(seed)
    cs = []
    for _ in range(n_boot):
        yb = _logistica(ts, *p, piso) + rng.normal(0.0, sigma_b, len(ts))
        try:
            pb, _ = curve_fit(lambda t, A, t0, tau: _logistica(t, A, t0, tau, piso),
                              ts, yb, p0=p, bounds=lims, maxfev=5000)
        except Exception:
            continue
        cb = _cruce(pb)
        if cb is not None:
            cs.append(cb)
    D = lambda d: (d0 + dt.timedelta(days=float(d))).isoformat()
    # el caso de MENOS confianza no puede salir con MAS confianza (fecha sin rango):
    # bootstrap inestable (<50 cruces) o IC degenerado (~0) -> None, no publicable.
    if len(cs) < 50:
        return None
    lo, hi = float(_np.percentile(cs, 2.5)), float(_np.percentile(cs, 97.5))
    if hi - lo < 0.5:
        return None
    if hi - ts.max() > horizonte:         # el horizonte tambien rige el extremo del IC
        return None
    return dict(fecha=D(c0), ic=(D(lo), D(hi)), rmse=round(rmse, 4), n=int(len(ts)),
                extrapolacion_dias=round(extra, 1),
                # parametros para DIBUJAR la curva (graficos del entregable);
                # d0 = fecha origen del eje t en dias
                params=dict(A=float(p[0]), t0=float(p[1]), tau=float(p[2]),
                            piso=float(piso), d0=d0.isoformat()))
