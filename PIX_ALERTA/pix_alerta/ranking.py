"""El criterio: ranking de lotes por apartamiento de su PROPIA trayectoria.

Por que no Gi* sobre el indice crudo. Medido sobre escena real de Santa Cruz
(PIX_ALERTA/medicion/gi_nulo_y_estratos.py): Gi*+FDR marca 33,3% del campo sin
estratificar y 30,3% estratificando por suelo, mientras que con los mismos valores
barajados en el espacio marca 0,0%. La implementacion es correcta; la nula de
aleatoriedad espacial es FALSA POR CONSTRUCCION en un lote agricola, asi que
rechazarla no informa nada y el resultado es una cuota del 30%.

La nula temporal si puede ser verdadera: un lote sano sigue su curva. Por eso el
estadistico es el residuo del lote respecto de la trayectoria de su cohorte,
acumulado con EWMA, y no un rank ni un cuantil.

Consecuencia buscada: el sistema PUEDE devolver "no pasa nada".
"""
import numpy as np
import pandas as pd

from . import config as cfg

# Parametros del criterio. Todos declarados, todos barribles (puerta 2.4).
LAMBDA_EWMA = 0.35        # peso de la observacion nueva
L_CONTROL = 3.0           # limite de la carta, en sigmas del propio lote
# Tiene que ser > N_BASE: si la serie entera es fase I, la mediana de la base cae
# DENTRO del episodio y el signo se invierte (medido: un colapso de -0,30 daba
# z=[+6,0, -0,07, +0,07, -2,81] y estado SIN SEÑAL).
MIN_OBS_LOTE = 7          # >= N_BASE + 3 observaciones de fase II
MIN_LOTES_COHORTE = 8     # sin esto la mediana de la cohorte no significa nada
N_BASE = 4                # observaciones de fase I para fijar la linea base
CADUCIDAD_DIAS = 30       # una alerta mas vieja que esto se declara sin dato
MIN_PIXELES = 8           # px limpios minimos por unidad (JRC 10.3390/rs12142195)
RHO_PISO = 0.05           # solo acota el rho de diagnostico
# E[1.4826*MAD(residuos centrados por la mediana de n)] / sigma, por simulacion
# (40.000 replicas). Centrar por la mediana de pocos puntos ENCOGE la dispersion.
SHRINK_MAD = {4: 0.7351, 5: 0.8259, 6: 0.8427}
# Var(mediana de n)/sigma^2 para n=N_BASE. Para n=4 es 0,2963 (no 0,25, que seria
# el de la MEDIA). Si se cambia N_BASE hay que recalcularlo.
VAR_BASE = 0.2963


def _rho_lag1(d, col):
    """Autocorrelacion lag-1 agrupada entre lotes, sobre la ventana de fase I.

    Se estima la mediana de los rho por lote y se acota: un rho cerca de 1 haria
    explotar el factor de correccion, y con series cortas el estimador es ruidoso.
    """
    rs = []
    for _, g in d.groupby('lote_id'):
        v = g[col].to_numpy(dtype=float)
        v = v[np.isfinite(v)]
        if len(v) < 3:
            continue
        a, b = v[:-1], v[1:]
        if a.std() < 1e-12 or b.std() < 1e-12:
            continue
        rs.append(float(np.corrcoef(a, b)[0, 1]))
    if not rs:
        return 0.0
    return float(np.clip(np.median(rs), 0.0, 1.0 - RHO_PISO))


def _trayectoria_cohorte(df, eje):
    """Mediana de la cohorte por fecha: la trayectoria fenologica esperada.

    Se usa la mediana, no la media, porque si media docena de lotes estan
    afectados no deben arrastrar la referencia contra la que se los mide.
    """
    g = df.groupby(['cohorte', 'fecha'])[eje]
    ref = g.median().rename('ref')
    n = g.size().rename('n_cohorte')
    return pd.concat([ref, n], axis=1).reset_index()


def dentro_de_campana(fecha, sitio):
    """True si la fecha cae dentro de alguna campaña declarada del sitio.

    `Sitio.campanas` estaba declarado en config y NO LO LEIA NINGUN MODULO. Resultado
    real: se produjo un ranking para el 2026-05-06, fuera de la campaña 2025/2026
    (que cierra el 30-abr), en plena cosecha de soya. En cosecha el NDMI baja y el
    PSRI sube — que es EXACTAMENTE la firma que el criterio busca. El motor no tiene
    forma de distinguir madurez/cosecha de deterioro, y la mediana de cohorte no lo
    corrige porque los lotes no se cosechan a la vez.
    """
    f = str(pd.Timestamp(fecha).date())
    for ini, fin in (sitio.campanas or {}).values():
        if ini <= f <= fin:
            return True
    return False


def inicio_de_campana(fecha, sitio):
    """Fecha de arranque de la campaña que contiene a `fecha`. None si no hay.

    LA VENTANA TIENE QUE EMPEZAR CON LA CAMPAÑA, NO N DIAS ATRAS.
    Medido en la primera corrida real contra Earth Engine: con la ventana por defecto de
    150 dias, una corrida al 30-abr arranca el 1-dic — a mitad de campaña, cuando los
    lotes ya emergieron. El estimador de cohorte necesita ver la RAMA ASCENDENTE del
    NDVI para ubicar la emergencia, asi que mando **188 de 207 lotes a EST-SIN-CICLO** y
    el ranking salio con CERO lotes evaluados. Con la serie completa de la campaña, el
    mismo dia daba 126 lotes y 6 alertados.

    El sitio ya declara sus campañas; no hace falta adivinar el largo de la ventana.
    """
    f = str(pd.Timestamp(fecha).date())
    for ini, fin in (sitio.campanas or {}).values():
        if ini <= f <= fin:
            return ini
    return None


def residuos(df, ejes=cfg.EJES, solo_pleno=True):
    """Apartamiento de cada lote respecto de SU PROPIA trayectoria.

    Tres pasos, y el segundo es el que hace que la nula sea temporal y no espacial:

    1. `resid = valor - mediana(cohorte, fecha)` quita la trayectoria fenologica:
       lo que baja porque la campaña avanza, baja para todos.
    2. `centrado = resid - mediana(resid del lote)` quita el desnivel propio del
       lote. Sin este paso, un lote que siempre esta por debajo de la mediana de la
       hacienda (otra variedad, otra edad, otro suelo) queda marcado para siempre:
       eso seria volver a preguntar "¿este lote es distinto de sus vecinos?", que es
       la nula falsa por construccion que se quiere evitar.
    3. Se estandariza por una dispersion AGRUPADA entre lotes, estimada por rango
       movil (diferencias sucesivas). No por la dispersion de cada lote: con pocas
       observaciones ese estimador esta sesgado a la baja y el denominador termina
       eligiendo el ranking — defecto medido en el motor de caña, 49 de 131 lotes
       con SD < 0,03 y minimo 0,0016.
    """
    d = df.copy()
    if solo_pleno:
        d = d[d['calidad'] == 'pleno']
    # Criterio numerico del JRC (10.3390/rs12142195): una unidad con muy pocos pixeles
    # limpios no se analiza. `n_px` se venia capturando sin usar, asi que un lote de
    # media hectarea con 3 pixeles validos podia rankear primero.
    if 'n_px' in d.columns:
        antes = len(d)
        d = d[d['n_px'].fillna(0) >= MIN_PIXELES]
        if antes - len(d):
            print('[criterio] %d observaciones descartadas por <%d pixeles limpios'
                  % (antes - len(d), MIN_PIXELES))
    if 'cohorte' not in d.columns:
        d['cohorte'] = 'unica'

    salida = []
    for eje in ejes:
        t = _trayectoria_cohorte(d, eje)
        m = d.merge(t, on=['cohorte', 'fecha'], how='left')
        m = m[m['n_cohorte'] >= MIN_LOTES_COHORTE]
        m['resid'] = m[eje] - m['ref']
        # 2 y 3. La linea base sale de las PRIMERAS N_BASE observaciones del lote
        # (fase I de la carta), no de la serie entera. Si se usa toda la serie, un
        # episodio largo entra en su propia referencia y se anula solo: es el mismo
        # defecto que tiene el eje temporal del motor v7, cuya ventana de `cire_ref`
        # incluye la fecha que analiza.
        # Limite conocido y declarado: un deterioro que empiece DENTRO de la fase I
        # no se detecta. Por eso la linea base debe sembrarse temprano en campaña.
        m = m.sort_values(['lote_id', 'fecha'])
        cab = m.groupby('lote_id').head(N_BASE)
        base = cab.groupby('lote_id')['resid'].median().rename('base')
        m = m.merge(base, on='lote_id', how='left')
        m['centrado'] = m['resid'] - m['base']

        # Dispersion AGRUPADA sobre TODOS los residuos de fase I juntos, no la
        # mediana de los MAD individuales. Dos razones:
        #  - el MAD de N_BASE=4 puntos subestima la dispersion de forma sistematica;
        #    tomar la mediana de estimadores sesgados hereda el sesgo y el z se infla
        #    (medido: ~20% de falsas alarmas sobre campo sintetico sano).
        #  - el denominador termina eligiendo el ranking: los lotes que por azar
        #    salieron homogeneos se van arriba. Defecto medido en el motor de caña
        #    (49 de 131 lotes con SD < 0,03, minimo 0,0016).
        # Agrupando n_lotes x N_BASE observaciones la dispersion si es estimable.
        # Estimador por RANGO MOVIL: MAD de las diferencias sucesivas dentro de
        # cada lote, agrupadas. Se usa este y no el MAD de los residuos centrados
        # por dos motivos:
        #  - el MAD de la ventana de la que sale la propia mediana esta encogido
        #    hacia cero y subestima la escala (medido: SD del z = 1,7 en vez de 1);
        #  - las diferencias sucesivas son inmunes al desnivel del lote y a la
        #    deriva lenta, y un escalon sostenido contamina UNA sola diferencia.
        # Sobre la VENTANA DE FASE I, no sobre la serie completa: si se usa toda la
        # serie, un evento generalizado infla la dispersion y se enmascara solo.
        # DISPERSION POR FECHA, robusta y transversal entre lotes.
        #
        # Historia de este estimador, toda medida sobre HDS:
        #  1. MAD del propio lote: sesgado a la baja con pocos puntos; el denominador
        #     elegia el ranking (defecto del motor de caña, 49 de 131 lotes SD<0,03).
        #  2. Rango movil (MAD de diferencias sucesivas /sqrt(2)): supone INDEPENDENCIA
        #     temporal. Con el rho real (0,6-0,7) devuelve sigma*sqrt(1-rho) y la tasa
        #     de falsa alarma se dispara. SD del z medida: 2,9 en vez de 1.
        #  3. Dispersion marginal de fase I: tampoco alcanza, porque la heterogeneidad
        #     entre lotes CRECE a lo largo de la campaña — una escala fija para toda la
        #     temporada esta bien calibrada al principio y mal despues. SD del z: 2,9.
        #  4. Esta: MAD TRANSVERSAL entre lotes, recalculado en CADA fecha. No supone
        #     nada sobre la dependencia temporal y sigue la heterogeneidad real.
        #
        # Riesgo conocido y acotado: un evento GENERALIZADO infla la escala de esa fecha
        # y se enmascara. Por eso se usa MAD (haria falta que afectara a mas de la mitad
        # de los lotes para mover la mediana) y se pone un piso con la mediana temporal.
        esc = (m.groupby('fecha')['centrado']
                 .transform(lambda v: 1.4826 * np.nanmedian(np.abs(v - np.nanmedian(v)))))
        piso = float(np.nanmedian(esc)) * 0.33 if np.isfinite(np.nanmedian(esc)) else 0.0
        m['sd_usada'] = esc.fillna(piso).clip(lower=max(piso, 1e-6))
        m['rho_lag1'] = _rho_lag1(cab, 'resid')   # diagnostico, no entra al calculo
        m['z'] = (m['centrado'] / m['sd_usada']).clip(-6, 6)
        m['eje'] = eje
        cols = ['lote_id', 'fecha', 'cohorte', 'area_ha', 'eje', eje, 'ref',
                'resid', 'centrado', 'sd_usada', 'rho_lag1', 'z']
        for extra in ('cobertura', 'n_px', 'calidad'):
            if extra in m.columns:
                cols.append(extra)
        salida.append(m[cols].rename(columns={eje: 'valor'}))
    return pd.concat(salida, ignore_index=True)


def ewma(res, lam=LAMBDA_EWMA, L=L_CONTROL):
    """Carta EWMA sobre el residuo estandarizado, por lote y por eje.

    Acumula: un apartamiento chico y sostenido pesa mas que un pico de una fecha,
    que es justo lo que distingue un problema real de una escena rara.
    """
    # Sin residuos no hay carta. `residuos` devuelve vacio cuando ninguna cohorte
    # llega al minimo de lotes: sin esta guarda, `sort_values('fecha')` revienta
    # con un KeyError que no dice nada del problema real.
    if res is None or len(res) == 0 or 'fecha' not in getattr(res, 'columns', []):
        return pd.DataFrame()
    out = []
    for (lote, eje), g in res.sort_values('fecha').groupby(['lote_id', 'eje']):
        g = g.dropna(subset=['z'])
        if len(g) < MIN_OBS_LOTE:
            continue
        z = g['z'].to_numpy()
        n = len(z)
        # Limite del EWMA segun los pasos transcurridos DESDE EL ULTIMO REINICIO.
        # Al termino clasico se le suma la varianza del error de la linea base: esa
        # base se estimo con N_BASE puntos y su error es comun a toda la serie del
        # lote, asi que el EWMA no lo promedia, lo integra. Sin este termino cada
        # lote arrastra un desvio persistente (medido: 0,78 sigma con N_BASE=4) y la
        # carta dispara sola.
        pasos = np.arange(1, n + 1)
        # El error de la linea base entra al EWMA ACUMULANDOSE, con peso (1-(1-l)^i),
        # no de golpe. Y la base es una MEDIANA, no una media: Var(mediana de n)/sigma^2
        # es ~0,2963 para n=4, no 0,25. Sin las dos correcciones la carta queda CIEGA en
        # el primer paso tras cada arranque o reinicio (limite 1,83 en vez de 1,20) y
        # corre a ~1,7x la tasa nominal en regimen.
        curva = L * np.sqrt(lam / (2 - lam) * (1 - (1 - lam) ** (2 * pasos))
                            + (1 - (1 - lam) ** pasos) ** 2 * VAR_BASE)
        e, lim = np.zeros(n), np.zeros(n)
        acc, k = 0.0, 0
        for i, zi in enumerate(z):
            acc = lam * zi + (1 - lam) * acc
            e[i] = acc
            lim[i] = curva[k]
            # Reinicio tras señal. Sin esto la carta no se resuelve nunca: un lote
            # marcado en diciembre sigue marcado en abril y la lista solo crece
            # (medido sobre la campaña de HDS: 14,1% -> 22,6% de forma monotona).
            # Es la practica estandar "investigar y reiniciar": si el lote se
            # recupera deja de señalar, y si sigue mal vuelve a señalar.
            if abs(acc) > lim[i]:
                acc, k = 0.0, 0
            else:
                k = min(k + 1, n - 1)
        gg = g.copy()
        gg['ewma'] = e
        gg['limite'] = lim
        gg['fuera'] = np.abs(e) > lim
        out.append(gg)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


# Signo fisiologico: por que eje un valor BAJO (o alto) es la señal de alarma.
#   NDMI bajo = dosel mas seco de lo esperado.
#   PSRI alto = mas senescente.
#   NDRE / CIRE bajos = menos clorofila de la esperada.
#
# TODO eje que se use TIENE que estar acá. El `.get(eje, 1)` de mas abajo asume
# +1 para lo que no figure, o sea que un eje nuevo cuya alarma es el valor BAJO
# quedaria con el signo invertido: el motor alertaria sobre los lotes SANOS y
# callaria sobre los enfermos, sin fallar ni avisar. Es el error mas caro posible
# en este archivo.
SIGNO = {'NDVI': -1, 'NDMI': -1, 'PSRI': +1, 'NDRE': -1, 'CIRE': -1,
         # kNDVI es una transformacion MONOTONA CRECIENTE de NDVI (tanh(NDVI^2)
         # sobre NDVI>=0), asi que su alarma es el valor bajo, igual que NDVI.
         'KNDVI': -1,
         # --- LOS DOS DE TEXTURA: el signo es HIPOTESIS, no medicion -----------
         # TEXNIR (contraste GLCM en B8A). Razonamiento fisico: un dosel que se
         # degrada EN PARCHES —calvas, foco de plaga, ahogo— se vuelve mas
         # heterogeneo a la escala de la ventana, asi que el contraste SUBE. Alarma
         # = valor alto => +1.
         #
         # ⚠️ EL CASO QUE ROMPE EL RAZONAMIENTO, y hay que medirlo antes de confiar:
         # un dosel que se degrada de forma UNIFORME (deficit hidrico parejo,
         # senescencia normal) se vuelve mas PAREJO, no menos, y el contraste BAJA.
         # O sea que este eje detecta daño EN PARCHES y es CIEGO —o peor, se mueve
         # al reves— frente a daño uniforme. Eso no lo invalida: los focos de
         # scouting son parches por definicion. Pero significa que TEXNIR no es
         # intercambiable con un eje espectral y que su tasa hay que medirla sola.
         'TEXNIR': +1,
         # NDTX. **EL SIGNO NO ESTA MEDIDO NI RAZONADO CON CONFIANZA.** Se declara
         # +1 por coherencia con TEXNIR (el numerador es el contraste de B8A), pero
         # el cociente puede moverse por el denominador tanto como por el numerador,
         # y no hay literatura ni medicion propia que fije la direccion sobre un
         # cultivo en pie. **No usar como eje de produccion hasta medir el signo**
         # con `medicion/textura_como_eje.py --signo`.
         'NDTX': +1}

# La verificacion que convierte "el error mas caro posible" en un crash al importar.
# Sin ella, configurar un eje sin declarar su sentido no falla: el motor marca los
# lotes SANOS y calla sobre los enfermos. Con NDVI ausente y EJES=('NDVI','NDMI'),
# medido: el estado ATENCION se volvia INALCANZABLE y no habia ni un warning.
_faltan = [e for e in cfg.EJES if e not in SIGNO]
if _faltan:
    raise RuntimeError(
        'cfg.EJES declara %s y ranking.SIGNO no dice si su alarma es el valor alto '
        'o el bajo. Agregalos a SIGNO antes de usarlos: un signo invertido hace que '
        'el motor alerte sobre los lotes sanos sin fallar ni avisar.' % _faltan)


def ranking(car, fecha=None, K=None):
    """Lista de lotes ordenada por evidencia de apartamiento, a una fecha.

    Devuelve TODOS los lotes con su estado. Que el cliente corte en K es una
    decision de capacidad de scouting, no del criterio: un rank siempre tiene un
    primero, pero 'atencion' solo lo tienen los que salen de control.
    """
    if car.empty:
        return pd.DataFrame()
    f = pd.Timestamp(fecha) if fecha is not None else car['fecha'].max()
    # ultima observacion de cada lote/eje hasta la fecha pedida
    h = car[car['fecha'] <= f]
    ult = (h.sort_values('fecha').groupby(['lote_id', 'eje']).tail(1))
    ult = ult.copy()
    ult['ewma_dir'] = ult.apply(
        lambda r: r['ewma'] * SIGNO.get(r['eje'], 1), axis=1)
    # señal solo si el apartamiento va en el sentido fisiologico de deterioro
    ult['senal'] = ult['fuera'] & (ult['ewma_dir'] > 0)

    espec = dict(
        fecha_dato=('fecha', 'max'),
        area_ha=('area_ha', 'first'),
        cohorte=('cohorte', 'first'),
        ejes_en_senal=('senal', 'sum'),
        score=('ewma_dir', 'max'),
        dias_atras=('fecha', lambda s: (f - s.max()).days),
    )
    # Con que se construyo. Sin esto, en la campaña de validacion no se podra
    # distinguir un falso negativo real de una dekada nublada.
    if 'cobertura' in ult.columns:
        espec['cobertura'] = ('cobertura', 'min')
    agg = ult.groupby('lote_id').agg(**espec).reset_index()
    # Origen de la cohorte. `cohorte.py` rotula SIEMPRE `EST-<fecha>` / `EST-SIN-CICLO`
    # porque no hay una sola fecha de siembra declarada en toda la cartera. La condicion
    # anterior comparaba contra 'unica' y daba 'declarada' a todo lo demas, o sea rotulaba
    # como declarada una cohorte estimada por fenologia — justo lo que la metodologia
    # prohibe. Se decide por el prefijo que escribe el estimador, no por descarte.
    coh = agg['cohorte'].astype(str)
    agg['cohorte_origen'] = np.where(coh == 'EST-SIN-CICLO', 'ESTIMADA-SIN-CICLO',
                             np.where(coh.str.startswith('EST-'), 'ESTIMADA-FENOLOGIA',
                             np.where(coh == 'unica', 'ESTIMADA-UNICA', 'declarada')))

    # ATENCION exige que TODOS los ejes configurados esten en señal, no "2 o mas".
    # Con `>= 2` cableado, configurar 3 ejes convertia la conjuncion en "2 de 3"
    # —una regla mucho mas laxa— y con 1 eje volvia ATENCION inalcanzable, en los
    # dos casos sin que nada lo declarara.
    n_ejes = len(cfg.EJES)
    agg['estado'] = np.where(agg['ejes_en_senal'] >= n_ejes, 'ATENCION',
                    np.where(agg['ejes_en_senal'] >= 1, 'VIGILANCIA', 'SIN SEÑAL'))

    # UNA COHORTE SIN CICLO NO PUEDE PRODUCIR UN ATENCION. `EST-SIN-CICLO` agrupa a
    # los lotes cuya emergencia no se pudo ubicar — en HDS 2025/26 son 90 de 207
    # (43,5%) — y su "trayectoria mediana" mezcla fechas de siembra desconocidas.
    # Es exactamente la configuracion que `cohorte.py` declara MEDIDA COMO CIEGA
    # (cohorte unica: 1,3% marcado contra un nulo de 2,0%). Y sin esta degradacion,
    # el lote #1 del producto salia de ahi: se mandaba al tecnico primero al lote
    # cuya referencia el propio motor no puede sostener.
    sin_ciclo = agg['cohorte'].astype(str).eq('EST-SIN-CICLO')
    degradados = int((sin_ciclo & agg['estado'].eq('ATENCION')).sum())
    agg.loc[sin_ciclo & agg['estado'].eq('ATENCION'), 'estado'] = 'VIGILANCIA'
    agg['referencia_debil'] = sin_ciclo
    if degradados:
        print('[criterio] %d lote(s) bajados de ATENCION a VIGILANCIA: su cohorte es '
              'EST-SIN-CICLO (no se pudo ubicar la emergencia, la referencia no '
              'discrimina)' % degradados)
    # Una alerta vieja no es una alerta: con 48% de dekadas sin escena util, un lote
    # puede quedar meses sin observacion. Arrastrar su ultimo estado seria afirmar
    # algo que no se miro. Se declara la falta de dato en vez de suponer.
    agg.loc[agg['dias_atras'] > CADUCIDAD_DIAS, 'estado'] = 'SIN DATO'
    # SIN DATO va SIEMPRE al final. `ejes_en_senal` y `score` sobreviven al pisado
    # del estado, asi que un lote sin observar hace 80 dias se ordenaba ARRIBA de
    # lotes en VIGILANCIA reales y ocupaba un puesto en la tabla del informe. No se
    # oculta —sigue contado y declarado— pero no compite por prioridad con lo que si
    # se midio.
    # El orden lo manda el ESTADO FINAL, no el conteo de ejes. Con la degradacion de
    # cohorte debil, un lote podia quedar VIGILANCIA y seguir figurando primero, por
    # encima de ATENCIONes reales: el informe decia "van ordenados por prioridad" y
    # el primero de la lista era el de menor prioridad.
    _PRIORIDAD = {'ATENCION': 0, 'VIGILANCIA': 1, 'SIN SEÑAL': 2, 'SIN DATO': 3}
    agg['_prio'] = agg['estado'].map(_PRIORIDAD).fillna(9).astype(int)
    agg = agg.sort_values(['_prio', 'ejes_en_senal', 'score'],
                          ascending=[True, False, False], kind='mergesort')
    agg = agg.drop(columns='_prio')
    agg['orden'] = np.arange(1, len(agg) + 1)
    if K:
        # K es un TECHO de capacidad de scouting, no una cuota a llenar. Cortar por K
        # sin filtrar por estado reintroduciria en el ultimo paso justo la cuota que
        # todo el criterio evita: con K=10 sobre un campo sano se mandaria al tecnico
        # a 10 lotes igual. Solo viajan los que salen de control.
        con_senal = agg[agg['estado'].isin(('ATENCION', 'VIGILANCIA'))]
        agg = con_senal.head(K)
    return agg.reset_index(drop=True)


def _ar1(n, sigma, rho, rng):
    """Ruido AR(1) con varianza marginal sigma^2 y autocorrelacion lag-1 rho."""
    x = np.empty(n)
    x[0] = rng.normal(0, sigma)
    s_e = sigma * np.sqrt(max(1 - rho ** 2, 1e-6))
    for i in range(1, n):
        x[i] = rho * x[i - 1] + rng.normal(0, s_e)
    return x


def control_nulo(df, ejes=cfg.EJES, n_rep=20, semilla=0, fechas=None):
    """Puerta 2.1: la tasa de FALSA ALARMA del criterio.

    Se construye el mundo donde la hipotesis nula es CIERTA por construccion: cada
    lote sigue EXACTAMENTE la trayectoria de su cohorte mas ruido AR(1) con la
    escala, la autocorrelacion temporal y la correlacion entre ejes medidas en el
    dato real. Ningun lote se aparta, asi que toda alarma es falsa.

    POR QUE SE REEMPLAZO LA PERMUTACION (medido 2026-07-26, no supuesto)
    --------------------------------------------------------------------
    Las dos versiones anteriores permutaban el dato, y ninguna era una nula:

    1. Permutar identidades dentro de cada fecha dejaba a cada "lote" con una serie
       iid: destruia la autocorrelacion a la que el estimador de escala es sensible,
       y reportaba ~0% pasara lo que pasara.
    2. Rotar circularmente la serie de cada lote fallaba por TRES razones distintas:
       · rotaba los indices pero NO la etiqueta de calidad, asi que una fila 'pleno'
         recibia el valor de una fecha nublada (enmascarado, vacio). La nula perdia
         el 70% de las observaciones y se evaluaba sobre 3 lotes mientras el dato
         real se evaluaba sobre 96. No eran comparables.
       · rotando cada lote un desplazamiento DISTINTO, la mediana por (cohorte,
         fecha) deja de ser una trayectoria fenologica y se aplana: el desvio del
         NDMI mediano de cohorte caia de 0,1338 a 0,1022. El residuo contra una
         referencia degradada es mayor, asi que la "nula" disparaba MAS que el dato
         real (separacion negativa en las tres configuraciones de ejes probadas).
       · una rotacion circular CONSERVA los episodios sostenidos, solo los cambia de
         fecha. El EWMA busca desvios sostenidos, asi que los sigue viendo. Una
         permutacion que preserva justo lo que el estadistico detecta no puede ser
         su nula.

    Con esta version, sobre HDS 2025/26, la falsa alarma medida es 0,14%-0,28%
    segun el par de ejes — coherente con una carta a L=3 sigma. Los "0,7%-1,8%"
    que circulaban en la documentacion salian del metodo viejo y no son una tasa
    de falsa alarma.

    `fechas`: cortes donde evaluar. Por defecto la ultima. Conviene pasar varias:
    medir en un solo dia compara ruido de muestreo.
    """
    d0 = df.copy()
    if 'cohorte' not in d0.columns:
        # Mismo respaldo que `residuos`: sin NDVI no se puede estimar la cohorte,
        # y eso no es motivo para no poder medir la falsa alarma.
        try:
            from . import cohorte as coh
            d0 = coh.estimar(d0)
        except Exception:
            d0['cohorte'] = 'unica'
    pl = d0[d0['calidad'] == 'pleno'] if 'calidad' in d0.columns else d0
    rng = np.random.default_rng(semilla)

    traj, par = {}, {}
    for eje in ejes:
        t = pl.groupby(['cohorte', 'fecha'])[eje].median().rename('_traj')
        traj[eje] = t
        r = pl.join(t, on=['cohorte', 'fecha'])
        res = (r[eje] - r['_traj']).to_numpy(dtype=float)
        res = res[np.isfinite(res)]
        sigma = (1.4826 * np.nanmedian(np.abs(res - np.nanmedian(res)))
                 if len(res) else 0.0)
        rhos = []
        for _, g in r.sort_values('fecha').groupby('lote_id'):
            v = (g[eje] - g['_traj']).to_numpy(dtype=float)
            v = v[np.isfinite(v)]
            if len(v) >= 4 and v.std() > 1e-12:
                rhos.append(np.corrcoef(v[:-1], v[1:])[0, 1])
        par[eje] = (float(sigma), float(np.clip(np.median(rhos), 0, 0.95))
                    if rhos else 0.0)

    # Correlacion ENTRE ejes en el ruido: generar los dos independientes hace que la
    # conjuncion parezca mas exigente de lo que es. Se usa la de los residuos
    # observados, que mezcla senal y ruido y por lo tanto es una cota superior.
    e1, e2 = (list(ejes) + list(ejes))[:2]
    r1 = pl.join(traj[e1], on=['cohorte', 'fecha'])
    r2 = pl.join(traj[e2], on=['cohorte', 'fecha'])
    v1 = (r1[e1] - r1['_traj']).to_numpy(dtype=float)
    v2 = (r2[e2] - r2['_traj']).to_numpy(dtype=float)
    ok = np.isfinite(v1) & np.isfinite(v2)
    rho_xy = float(np.clip(np.corrcoef(v1[ok], v2[ok])[0, 1], -0.98, 0.98)
                   ) if ok.sum() > 30 else 0.0

    tasas = []
    for _ in range(n_rep):
        sint = d0.copy()
        ordenado = sint.sort_values('fecha')
        s1, s2 = par[e1][0], par[e2][0]
        n1, n2, filas = [], [], []
        for _, g in ordenado.groupby('lote_id', sort=True):
            a1 = _ar1(len(g), 1.0, par[e1][1], rng)
            a2 = _ar1(len(g), 1.0, par[e2][1], rng)
            n1.append(a1 * s1)
            n2.append((rho_xy * a1 + np.sqrt(max(1 - rho_xy ** 2, 0)) * a2) * s2)
            # El indice se acumula EN EL MISMO ORDEN que el ruido. Usar el indice
            # global ordenado por fecha emparejaba la observacion i-esima de un lote
            # con la i-esima fila cronologica de TODA la tabla: rompia la
            # autocorrelacion temporal intra-lote, que es justo lo que esta nula
            # tiene que preservar. Con el bug la puerta devolvia 0,00% pasara lo que
            # pasara — una puerta que no puede reprobar no es una puerta. Medido
            # sobre HDS 2025/26: 0,0000% con el bug, 0,30% corregido.
            filas.append(g.index.to_numpy())
        idx = pd.Index(np.concatenate(filas)) if filas else ordenado.index
        for eje, ru in ((e1, np.concatenate(n1)), (e2, np.concatenate(n2))):
            base = sint.set_index(['cohorte', 'fecha']).index.map(traj[eje])
            s = pd.Series(ru, index=idx).reindex(sint.index)
            sint[eje] = np.asarray(base, dtype=float) + s.to_numpy()
        car = ewma(residuos(sint, ejes))
        if car.empty:
            continue
        for f in (fechas or [None]):
            r = ranking(car, fecha=f)
            if not r.empty:
                tasas.append(r['estado'].isin(('ATENCION', 'VIGILANCIA')).mean())
    return float(np.mean(tasas)) if tasas else float('nan')


def _control_nulo_permutacion(df, ejes=cfg.EJES, n_rep=20, semilla=0):
    """OBSOLETA. Se conserva solo para poder reproducir los numeros viejos.

    No usar como puerta de aceptacion: ver el encabezado de `control_nulo`.

    La version anterior permutaba identidades DENTRO de cada fecha, lo que dejaba a
    cada "lote" con una serie iid: destruia justamente la autocorrelacion a la que el
    estimador de escala es sensible, asi que reportaba ~0% pasara lo que pasara.
    Medido: con rho=0,85 la tasa real sobre campo sano era 21,7% y este control
    informaba 0,0%. Una puerta que no puede reprobar no es una puerta.

    Ahora se rota CIRCULARMENTE la serie de cada lote (block shift). Eso conserva la
    estructura temporal intra-lote y la distribucion de valores, pero rompe la
    alineacion con la trayectoria de la cohorte, que es la alternativa que se testea.

    LA ETIQUETA DE CALIDAD VIAJA CON EL VALOR, y no es un detalle. Rotando solo los
    indices, una fila que era 'pleno' recibia el valor de una fecha nublada — que
    viene vacio, porque el indice esta enmascarado — y se caia en el EWMA. Medido
    sobre HDS: la nula perdia el 70% de las observaciones y solo 3 lotes de 96
    alcanzaban el minimo de observaciones. La nula se estaba calculando sobre otra
    poblacion de lotes que el dato real, asi que las dos tasas no eran comparables
    y la puerta no media lo que decia medir.
    """
    rng = np.random.default_rng(semilla)
    tasas = []
    # Todo lo que describe la OBSERVACION rota junto: valor, calidad y soporte.
    # Lo que describe al LOTE (area, cohorte) no rota: es la identidad, no el dato.
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
        car = ewma(residuos(d, ejes))
        if car.empty:
            continue
        r = ranking(car)
        tasas.append((r['estado'].isin(('ATENCION', 'VIGILANCIA'))).mean())
    return float(np.mean(tasas)) if tasas else float('nan')
