"""Capa de acercamiento: DONDE, dentro del lote alertado, y CUANTO.

`ranking.py` responde a que lote ir. Este modulo responde a donde pararse adentro
y que fraccion del lote esta comprometida. Corre SOLO sobre los lotes que el
criterio ya saco de control (el top-K), no sobre la cartera entera: bajar a
pixel en 220 lotes cuesta caro y no aporta — si el lote no salio de control, no
hay a donde mandar a nadie.

POR QUE NO SE COPIA EL ENFOQUE ESPACIAL HABITUAL
------------------------------------------------
El patron comun (y el que embarca la competencia) es un alto-paso espacial: se
compara cada pixel con su entorno y se marca la cola inferior con un umbral fijo
de z. Eso NO se puede usar acá y la razon es la misma que ya rechazo a Gi* en
`ranking.py`: la nula de aleatoriedad espacial es falsa por construccion en un
lote agricola, asi que rechazarla no informa. Con un corte fijo en z <= -1,3 se
marca el 9,7% del area SIEMPRE, tenga o no tenga problema el lote. Es una cuota
disfrazada de deteccion, y el porcentaje que se le reporta al cliente seria un
artefacto del umbral, no una medicion del campo.

Medido sobre un panel de terceros construido asi (auditoria 2026-07-26): la
compuerta que decia proteger contra eso usaba NDRE contra la mediana del propio
lote — relativa, la cumple entre el 35% y el 44% de los pixeles — y ademas NDRE
es colineal con el indice del gatillo (comparten B5). No es un segundo eje: es
el mismo dato medido dos veces.

EL CRITERIO DE ACA
------------------
Residuo TEMPORAL por pixel contra la ESCENA LIMPIA ANTERIOR del propio lote, en
los ejes que declara `config.EJES`, exigiendo que TODOS se muevan en el sentido
del deterioro. El sentido de cada uno lo da `ranking.SIGNO`, no este modulo.

Con la configuracion medida (NDMI + NDRE, ver `medicion/comparar_ejes.py`):

    foco  <=>  z(dNDMI) <= -Z_FOCO   Y   z(dNDRE) <= -Z_FOCO

  · NDMI (B8A-B11, SWIR): agua del dosel. Baja cuando el dosel se seca.
  · NDRE (B8A-B5, borde rojo): clorofila. Baja cuando el dosel pierde pigmento.

Pedir la CONJUNCION es lo que sostiene el porcentaje: exigir cola en los dos ejes
a la vez baja mucho el area marcada bajo ruido, comparado con el 9,7% que marca
por construccion un corte simple de z<=-1,3.

⚠️ NO vale el argumento teorico "alfa^2". Medido sobre HDS, la correlacion entre
los residuos de los dos ejes es de 0,79 a 0,90 segun el par — no son
independientes, asi que la conjuncion filtra MENOS de lo que predice la
independencia.

⚠️⚠️ **ESTE MODULO NO TIENE TASA DE FALSA ALARMA VALIDADA.** `control_nulo()`
existe pero fue AUDITADO Y RECHAZADO: invierte las colas del MISMO par de fechas,
con el mismo estimador, asi que detector y nula estan anticorrelados por
construccion (ante una sombra de nube el detector marca 25% y la "puerta" devuelve
0,09%). NO se publica en ningun entregable. Lo que haria falta —pares de fechas de
lotes con evento VERIFICADO en campo— no existe todavia; para eso es la campaña de
validacion. Hasta entonces el acercamiento entrega POLIGONOS Y HECTAREAS para ir a
mirar, no una probabilidad de que la mancha sea real, y asi hay que ofrecerlo.

La escala se estima por MAD TRANSVERSAL DE ESE PAR DE FECHAS dentro del lote, no
sobre la serie: el estimador de escala es lo que fija la tasa de falsa alarma, y
un rango movil supone independencia que no hay.
"""
import json

import ee

from . import config as cfg
from . import series as sr

# --- Parametros, todos declarados y todos barribles ---------------------------
Z_FOCO = 2.0              # sigmas por eje. Se exige en AMBOS, en sentidos opuestos.
# Fraccion MINIMA del lote que la escena tiene que TOCAR para representar a esa
# fecha. Distinto de la cobertura: la huella es geometrica (donde llega el granulo),
# la cobertura es de calidad (que fraccion es dosel util). Una astilla de borde de
# tile con cobertura 0,97 sobre el 8% del lote no es una observacion del lote.
HUELLA_MINIMA = 0.90
MMU_HA = 0.20             # unidad minima de mapeo: a 20 m son ~5 pixeles conectados.
ESCALA = 20               # m. El test se agrega a 20 m ANTES de testear, no por pixel.
MIN_GAP_DIAS = 5          # revisita S2. Debajo de esto no hay dos observaciones reales.
MAX_REF_DIAS = 40         # una referencia mas vieja compara fenologias distintas.
# Cobertura minima de dosel util para que una escena sirva de actual o de referencia.
#
# NO se hereda de `cfg.UMBRAL_PLENO` (0,80). Ese umbral existe para otra cosa: para
# que el PROMEDIO de un lote sea confiable. Acá no se promedia el lote, se testea
# pixel a pixel, y lo que hace falta es soporte estadistico suficiente, no que el
# lote entero este verde.
#
# ⚠️ EL RAZONAMIENTO ORIGINAL DE ESTE UMBRAL ERA FALSO. Se deja escrito porque el
# error importa. Decia: "medido sobre el trigo de Santo Antonio, la cobertura se
# estanca entre 70,7% y 78,8% con patron sostenido, o sea NO es nube, es el propio
# campo". La segunda parte no se sigue de la primera.
#
# El 70-79% es el TECHO ESTRUCTURAL DEL ESTIMADOR, no una propiedad del campo.
# `series._fvc` ancla el FVC en p2/p98 de la propia escena y `cfg.FVC_MINIMA=0.35`
# corta ahi: para cualquier distribucion aproximadamente simetrica eso excluye ~27%
# SIEMPRE. Medido sobre cinco distribuciones de NDVI: lote sano 73,1%, lote enfermo
# 73,3%, lote con 25% de cabecera desnuda 75,0%. **Sano y enfermo dan el mismo
# numero.**
#
# Tres consecuencias que hay que tener presentes:
#   1. Con 0,80 el acercamiento era MATEMATICAMENTE INALCANZABLE (0,80 > 0,735), no
#      "corria poco". El diagnostico llego al numero correcto por la razon equivocada.
#   2. 0,70 esta al 96% de su propio techo: exige de hecho >=96% de pixel limpio.
#      Esta sobre el filo, no es un umbral moderado.
#   3. La verificacion "con 0,70 y con 0,60 da lo mismo" probo el lado que NO manda:
#      casi nada cae entre 0,60 y 0,70 porque la masa esta en 0,735. La sensibilidad
#      esta ARRIBA de 0,70.
#
# LIMITE DECLARADO, y este si se sostiene y queda reforzado: el ~27% excluido no es
# aleatorio, es el cuartil inferior de NDVI del lote — o sea justo la zona floja
# donde puede haber un foco. El test corre sistematicamente sobre la parte de mas
# vigor. Bajar el umbral no crea ese sesgo, ya existia a 0,80.
COB_MINIMA = 0.70
VENTANA_DIAS = 90         # hacia atras desde el corte, para buscar el par de fechas.


class SinPar(Exception):
    """No hay par (actual, referencia) utilizable para este lote."""


def _geom_lote(sitio, feat):
    """Geometria del lote con el mismo buffer negativo que usa la serie.

    Tiene que ser EL MISMO buffer: si el acercamiento midiera sobre el borde crudo
    y el ranking sobre el interior, el porcentaje del informe no seria del area que
    disparo la alerta.
    """
    g = {'type': feat['geometry']['type'],
         'coordinates': sr._sin_z(feat['geometry']['coordinates'])}
    return ee.Geometry(g, geodesic=False).buffer(-sitio.buffer_negativo_m, maxError=1)


def _cobertura_por_escena(geom, ini, fin):
    """[(fecha, id_escena, cobertura util)] para el lote, en UNA sola llamada.

    Se resuelve del lado del servidor y se baja una tabla chica: hacer un getInfo
    por escena convierte 10 lotes en cientos de viajes de ida y vuelta.
    """
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
           .filterDate(ini, fin).filterBounds(geom))

    def marcar(img):
        img = ee.Image(img)
        valido = sr._mascara(img)
        idx = sr._indices(img)
        fvc = sr._fvc(idx.select('NDVI').updateMask(valido), geom, ESCALA)
        util = valido.And(fvc.gte(cfg.FVC_MINIMA))
        # `unmask(0)` SIN el segundo argumento usa sameFootprint=True: NO rellena
        # fuera de la huella del granulo, asi que los pixeles del lote que caen en
        # otro tile quedan enmascarados y `reduceRegion(mean)` los saca del
        # DENOMINADOR. La cobertura pasaba a medir "util / (lote ∩ granulo)".
        #
        # MEDIDO 2026-07-27, SAO_FRANCISCO-02 (a caballo de T22KEU/T22KEV), escena
        # 2026-05-31: la astilla del tile EU cubre el 8,2% del lote y reportaba
        # cob=0,972; el tile EV cubre el 100% y reportaba 0,968. Con el desempate
        # de abajo ganaba la astilla, y el detector corria sobre el 8% del lote
        # informando "cobertura 0,97". Es justo lo que estos campos existen para
        # impedir. `unmask(0, False)` extiende el relleno a toda la geometria.
        cob = util.unmask(0, False).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=geom, scale=ESCALA,
            maxPixels=1e9, bestEffort=True).get('valido')
        # HUELLA: que fraccion del lote toca esta escena. Es lo que distingue una
        # astilla de borde de tile de una escena entera, y sin esto el desempate
        # entre tiles no puede hacerse bien.
        huella = valido.mask().gt(-1).unmask(0, False).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=geom, scale=ESCALA,
            maxPixels=1e9, bestEffort=True).values().get(0)
        return ee.Feature(None, {
            'fecha': ee.Date(img.get('system:time_start')).format('YYYY-MM-dd'),
            'idx': img.get('system:index'),
            'cob': ee.Algorithms.If(cob, cob, 0),
            'huella': ee.Algorithms.If(huella, huella, 0),
        })

    fc = ee.FeatureCollection(col.map(marcar)).getInfo()
    filas = [(f['properties']['fecha'], f['properties']['idx'],
              float(f['properties']['cob'] or 0),
              float(f['properties'].get('huella') or 0)) for f in fc['features']]
    # Un lote puede caer en dos tiles. El desempate va por HUELLA primero, no por
    # cobertura: una astilla del 8% del lote puede tener cobertura casi perfecta
    # DENTRO de la astilla y ganarle a la escena que cubre el lote entero. Se elige
    # la que mas lote toca, y entre huellas parejas, la de mejor cobertura.
    mejor = {}
    for fch, idx, cob, hue in filas:
        clave = (round(hue, 3), round(cob, 4))
        if fch not in mejor or clave > mejor[fch][2]:
            mejor[fch] = (idx, cob, clave, hue)
    # Una escena que no cubre el lote no puede representar a esa fecha, tenga la
    # cobertura que tenga: lo que no se vio no se puede declarar limpio.
    return sorted((f, v[0], v[1]) for f, v in mejor.items()
                  if v[3] >= HUELLA_MINIMA)


def _par_de_fechas(escenas, hasta):
    """(actual, referencia): las dos escenas limpias mas recientes, separadas.

    La referencia es la ESCENA LIMPIA ANTERIOR, no la media de la temporada. Usar
    la media como referencia infla el area marcada varias veces, porque el propio
    episodio entra en su referencia y ademas se compara contra otra fenologia.
    """
    limpias = [(f, i, c) for f, i, c in escenas if c >= COB_MINIMA and f <= hasta]
    if len(limpias) < 2:
        raise SinPar('menos de dos escenas con cobertura >= %.0f%%'
                     % (COB_MINIMA * 100))
    act = limpias[-1]
    from datetime import date as _d

    def _dias(a, b):
        ya, ma, da = (int(x) for x in a.split('-'))
        yb, mb, db = (int(x) for x in b.split('-'))
        return abs((_d(ya, ma, da) - _d(yb, mb, db)).days)

    for cand in reversed(limpias[:-1]):
        d = _dias(act[0], cand[0])
        if MIN_GAP_DIAS <= d <= MAX_REF_DIAS:
            return act, cand
    raise SinPar('sin referencia limpia entre %d y %d dias antes de %s'
                 % (MIN_GAP_DIAS, MAX_REF_DIAS, act[0]))


def _escena(idx_escena):
    return ee.Image(ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                    .filter(ee.Filter.eq('system:index', idx_escena)).first())


def _par_enmascarado(idx_act, idx_ref, geom):
    """(actual, referencia) con los ejes, listos para restar.

    LA COMPUERTA DE DOSEL SE EXIGE SOLO EN LA REFERENCIA. La de nube, en las dos.

    Antes se exigia dosel util en AMBAS fechas, y eso tenia dos problemas, uno
    conceptual y uno medido:

    · CONCEPTUAL. Un pixel que era dosel y HOY YA NO LO ES es exactamente el daño
      que se busca. Exigir dosel tambien en la fecha actual descarta el caso mas
      severo — el unico que nadie discutiria. El motivo original de la compuerta
      («si en la referencia era suelo, la diferencia mide emergencia, no daño»)
      solo justifica exigirla en la REFERENCIA, que es lo que se hace ahora.

    · MEDIDO 2026-07-29, SANTO_ANTONIO-02 (par 07-20 / 07-15):
          sin nube en las dos fechas ............ 87,4% del lote
          la compuerta pasaba en las dos ........ 51,0%   <- lo que se testeaba
          DISCREPABA entre fechas ............... 36,1%   (41% de lo limpio)
          no pasaba en ninguna ..................  0,4%
      O sea: casi nada fallaba de verdad la compuerta. Se perdia el 41% de los
      pixeles limpios porque `series._fvc` ancla en p2/p98 de CADA escena, asi que
      el mismo punto del suelo caia de un lado del corte una fecha y del otro la
      siguiente sin que hubiera cambiado nada en el terreno.

    Se probo tambien un ancla COMUN al par (percentiles sobre la referencia
    restringida a lo limpio en ambas): empeoro —bajo el area util de 49% a 23% y
    perdio los tres focos—, porque calcular los percentiles sobre un subconjunto
    recortado por la nube corre el rango. Queda descartado y escrito.
    """
    ia_img, ir_img = _escena(idx_act), _escena(idx_ref)
    va, vb = sr._mascara(ia_img), sr._mascara(ir_img)
    ea, eb = sr._indices(ia_img), sr._indices(ir_img)
    # Dosel en la REFERENCIA, con el ancla de su propia escena (que es lo correcto:
    # un umbral absoluto de NDVI no transfiere entre sitios ni cultivares).
    fvc_ref = sr._fvc(eb.select('NDVI').updateMask(vb), geom, ESCALA)
    dosel_ref = fvc_ref.gte(cfg.FVC_MINIMA)
    util = va.And(vb).And(dosel_ref)
    return (ea.select(list(cfg.EJES)).updateMask(util),
            eb.select(list(cfg.EJES)).updateMask(util))


def _imagen_util(idx_escena, geom):
    """Los dos ejes de la escena, enmascarados a dosel util y agregados a 20 m.

    Se conserva para la puerta `control_nulo` y para uso suelto; el camino de
    produccion usa `_par_enmascarado`, que decide la compuerta mirando el PAR.
    """
    img = _escena(idx_escena)
    valido = sr._mascara(img)
    ejes = sr._indices(img)
    fvc = sr._fvc(ejes.select('NDVI').updateMask(valido), geom, ESCALA)
    util = valido.And(fvc.gte(cfg.FVC_MINIMA))
    return ejes.select(list(cfg.EJES)).updateMask(util)


# PISO DE ESCALA, EN UNIDADES DEL INDICE. No es un guard de division por cero.
#
# MEDIDO 2026-07-27 sobre los pares reales del cliente de trigo:
#     SANTO_ANTONIO-02 (heterogeneo)  sigma(dNDMI)=0,0398   sigma(dNDRE)=0,0600
#     SANTO_ANTONIO-01                sigma(dNDMI)=0,0071   sigma(dNDRE)=0,0068
#     SAO_FRANCISCO-01                sigma(dNDMI)=0,0074   sigma(dNDRE)=0,0067
#
# En un lote parejo la dispersion del DELTA cae a ~0,007, que es el orden del ruido
# radiometrico + BRDF + aerosol residual de S2 entre dos fechas. Con el piso
# anterior (1e-6, mil veces mas chico) el z se calculaba contra el ruido del sensor:
# una diferencia atmosferica espacialmente coherente de 0,015 NDMI daba z = -2,1 en
# los DOS ejes a la vez —comparten B8A— y pasaba la conjuncion. Lo unico que
# sostenia el resultado era `focalMode` + la MMU, que borran lo aislado pero NO un
# gradiente extenso: por eso el propio `control_nulo` mide 25% ante una sombra.
#
# 0,010 es deliberadamente CONSERVADOR: por debajo de eso la diferencia entre dos
# fechas no se puede atribuir al cultivo con S2. En un lote heterogeneo (0,04-0,06)
# no toca nada; en uno parejo impide que el criterio corra sobre ruido.
SIGMA_MINIMA = 0.010


def _z_robusto(delta, geom, banda, piso=None):
    """(delta - mediana) / (1,4826 * MAD), con la escala de ESE par de fechas.

    Piso en la escala: ver `SIGMA_MINIMA`. Sin el, un lote parejo hace que el z se
    calcule contra el ruido del sensor y el criterio marque diferencias de
    adquisicion. Es el analogo del piso derivado del dato de `ranking.py` (que alli
    es `mediana(escalas)*0,33`, posible porque hay una cohorte de la cual sacarlo;
    aca hay un solo lote y el piso tiene que venir de la fisica del sensor).
    """
    d = delta.select(banda)
    med = ee.Number(d.reduceRegion(
        reducer=ee.Reducer.median(), geometry=geom, scale=ESCALA,
        maxPixels=1e9, bestEffort=True).get(banda))
    med = ee.Number(ee.Algorithms.If(med, med, 0))
    mad = ee.Number(d.subtract(med).abs().reduceRegion(
        reducer=ee.Reducer.median(), geometry=geom, scale=ESCALA,
        maxPixels=1e9, bestEffort=True).get(banda))
    mad = ee.Number(ee.Algorithms.If(mad, mad, 0))
    sigma = mad.multiply(1.4826).max(piso if piso is not None else SIGMA_MINIMA)
    return d.subtract(med).divide(sigma).rename('z_' + banda)


def _mascara_focos(zs, z=Z_FOCO, invertir=False):
    """Conjuncion de los ejes de `cfg.EJES`, cada uno en su sentido de deterioro.

    `zs` es {eje: imagen de z}. El sentido lo da `ranking.SIGNO`, no este modulo:
    NDMI y NDRE alertan por valor BAJO, PSRI por valor ALTO. Cablearlo acá fue lo
    que obligo a tocar dos archivos al cambiar de eje, y un signo invertido hace que
    el motor marque los lotes SANOS sin fallar ni avisar.

    Que sea AND y no OR es lo que separa esto de una cuota: exigir cola en los dos
    ejes a la vez baja mucho el area marcada bajo ruido. Con OR se sumarian y el
    resultado seria peor que un solo eje. La tasa real la mide `control_nulo`, no
    se asume — con los ejes correlacionados no vale el alfa^2 teorico.

    `invertir=True` pide las colas de MEJORA: es la nula del procedimiento.
    """
    from .ranking import SIGNO
    m = None
    for eje, zi in zs.items():
        # SIN default: un eje que no declare su sentido tiene que REVENTAR, no
        # asumir +1. Con el default, un eje cuya alarma es el valor bajo queda
        # invertido y el motor marca los lotes SANOS sin fallar ni avisar.
        s = SIGNO[eje]
        cond = (zi.multiply(s).lte(-z) if invertir else zi.multiply(s).gte(z))
        m = cond if m is None else m.And(cond)
    return m.rename('foco')


# --- PERSISTENCIA: ¿el foco tambien estaba en la escena limpia anterior? ------
#
# LA IDEA. Un deterioro del cultivo no se mueve: un foco real deberia estar en el MISMO
# lugar cinco a diez dias despues. Una bruma no.
#
# ⚠️ LA COMPARACION CORRECTA NO ES LA OBVIA, Y ESTO COSTO UNA CONCLUSION EQUIVOCADA.
#
# El primer intento comparo los POLIGONOS entregados de una fecha contra los POLIGONOS
# entregados de la anterior, y dio **0% de solape** entre el 07-15 y el 07-10 — lo que
# parecia decir que el motor marcaba ruido. Era la pregunta equivocada: preguntaba
# «¿ya era REPORTABLE?» y no «¿ya ESTABA?».
#
# Un foco entregado es lo que quedo despues del filtro de mayoria y de la unidad minima de
# mapeo. Una anomalia que existe pero todavia es chica NO produce poligono. Comparando
# contra la MASCARA de anomalia de la escena anterior —no contra sus poligonos— el
# resultado se da vuelta:
#
#     foco entregado el 2026-07-15 (0,44 ha) en SANTO_ANTONIO-02
#         ya estaba marcado en la escena del 2026-07-10 en el  81,8% de su superficie
#         solape esperado POR AZAR                              2,72%
#         ->  30 VECES EL AZAR
#
# O sea que el foco que se le reporto al cliente **no es ruido**: ya estaba cinco dias
# antes, por debajo del tamano reportable, y crecio hasta pasar el umbral. Es exactamente
# lo que parece un problema que avanza.
#
# POR QUE SIGUE SIENDO ETIQUETA Y NO FILTRO
# -----------------------------------------
# 1. Un evento REAL Y NUEVO tampoco estaba antes. Filtrar por persistencia convertiria el
#    motor en un detector de anomalias viejas y agregaria un retraso de una imagen a TODA
#    alerta real.
# 2. Hay UN solo foco medido. Un caso a 30x el azar es alentador y no es una calibracion.
#
# Y ADEMAS QUEDO A LA VISTA OTRA COSA, que es la que mas importa: MEDIDO sobre la campana
# (`medicion/persistencia_focos.py`), el motor marco en 1 de 5 fechas en SANTO_ANTONIO-02 y
# en 0 de 5 en SANTO_ANTONIO-01. **Marca tan poco que casi no se puede validar con su
# propia salida.** Converge con lo ya medido: la escala del criterio es 2,7 a 6,5 veces el
# ruido real. Cuando eso se corrija, esta medicion se vuelve concluyente sola.
#
# TRES ESTADOS, y el tercero importa:
#   'persistente'    el foco ya estaba, por encima de lo que daria el azar
#   'sin_confirmar'  no estaba. NO significa falso: un evento nuevo tampoco estaba
#   'no_evaluable'   NO HAY escena anterior utilizable, asi que no se sabe. Paso con los
#                    3 focos del 07-10: el 06-30 tenia 17% de cobertura y el 07-05 lo
#                    rechaza la puerta de bruma. 'no se sabe' no comparte rotulo con 'no'.

# Cuantas veces el azar tiene que superar el solape para llamarlo persistente. El azar es
# la fraccion del area evaluada que estaba marcada en la escena anterior: si los focos de
# hoy cayeran en cualquier parte, se solaparian aproximadamente en esa proporcion.
# 3 veces es una eleccion declarada, no medida — con un solo foco no hay que calibrar.
# El caso medido dio 30x, asi que el umbral no esta ni cerca de decidir nada todavia.
FACTOR_PERSISTENCIA = 3.0


def _persistencia(sitio, feat, fecha_actual, focos, escala=ESCALA):
    """Fraccion de cada foco que TAMBIEN estaba marcada en la escena limpia anterior.

    Devuelve (lista de fracciones alineada con `focos`, fraccion marcada antes, fecha
    anterior) o (None, None, None) si no se pudo evaluar la escena anterior.

    Se llama SOLO cuando hay focos: en la mayoria de las corridas no hay ninguno y el
    costo es cero. Cuando hay, cuesta una evaluacion extra del criterio.
    """
    import pandas as pd

    from . import criterio as cri
    if not focos:
        return None, None, None
    try:
        # ⚠️ EL CORTE VA UN DIA ANTES. La ventana de candidatas del criterio es
        # `filterDate(hasta - N, hasta + 1)`, o sea que INCLUYE `hasta`: pasandole la
        # fecha actual volvia a elegir la MISMA escena y la persistencia salia
        # `no_evaluable` siempre. Con un dia menos, la ventana la excluye y elige la
        # anterior — para el 2026-07-15 elige el 2026-07-10.
        corte = str(pd.Timestamp(fecha_actual) - pd.Timedelta(days=1))[:10]
        r = cri.para_focos(_geom_lote(sitio, feat), corte, sitio=sitio)
    except Exception:                                    # noqa: BLE001
        return None, None, None
    if not r.get('fecha_img') or str(r['fecha_img'])[:10] >= str(fecha_actual)[:10]:
        return None, None, None
    geom = _geom_lote(sitio, feat)
    antes = r['foco'].unmask(0, False)
    # cuanto del area evaluada estaba marcada: es el solape que daria el azar
    base = antes.rename('a').reduceRegion(
        reducer=ee.Reducer.mean(), geometry=geom, scale=escala,
        maxPixels=1e9, bestEffort=True).get('a').getInfo()
    fc = ee.FeatureCollection([
        ee.Feature(ee.Geometry(f['geometry']), {'i': i})
        for i, f in enumerate(focos)])
    d = antes.rename('p').reduceRegions(
        collection=fc, reducer=ee.Reducer.mean().setOutputs(['p']),
        scale=escala, tileScale=4).getInfo()
    por_i = {int(x['properties']['i']): x['properties'].get('p')
             for x in d.get('features', [])}
    return ([por_i.get(i) for i in range(len(focos))],
            float(base or 0.0), str(r['fecha_img'])[:10])


def detectar_lote(sitio, feat, hasta, z=Z_FOCO, mmu_ha=None):
    """Focos de un lote: poligonos, area y porcentaje del lote comprometido.

    Devuelve dict con `focos` (lista de features GeoJSON), `area_focos_ha`,
    `pct_lote`, `fecha_img`, `fecha_ref` y `nota`. Nunca inventa: si no hay par de
    fechas utilizable lo declara en `nota` y devuelve cero focos.
    """
    lote_id = str(feat['properties'].get(sitio.campo_id))
    # Los dos parametros que un cliente puede necesitar distintos: la unidad minima
    # de mapeo (cuan chico es un foco que igual vale la pena caminar) y el piso de
    # escala (el ruido del sensor sobre ESE cultivo). Ver `config.Sitio`.
    if mmu_ha is None:
        mmu_ha = cfg.valor_de(sitio, 'mmu_ha', MMU_HA)
    piso = cfg.valor_de(sitio, 'sigma_minima', SIGMA_MINIMA)
    geom = _geom_lote(sitio, feat)
    desde = str(__import__('pandas').Timestamp(hasta)
                - __import__('pandas').Timedelta(days=VENTANA_DIAS))[:10]

    base = {'lote_id': lote_id, 'focos': [], 'area_focos_ha': 0.0,
            'error': None,          # None = no hubo averia (haya o no par de fechas)
            'pct_lote': 0.0, 'pct_util': 0.0, 'area_util_ha': None,
            'area_lote_ha': None, 'cobertura_img': None, 'cobertura_ref': None,
            'fecha_img': None, 'fecha_ref': None, 'nota': None}
    # --- CRITERIO ------------------------------------------------------------
    # v2 es el criterio por defecto desde 2026-07-29. Ver `criterio.py` para el
    # diseño y `medicion/calibrar_criterio.py` para la evidencia. En una linea:
    # medido sobre fechas SIN evento de los 4 lotes de trigo, v1 marcaba hasta el
    # 11,8% del lote y v2 baja el maximo a 2,2%. v1 queda accesible con
    # `config.CRITERIO = 'v1'` para poder comparar, no como camino de produccion.
    if getattr(cfg, 'CRITERIO', 'v2') == 'v2':
        from . import criterio as cri
        try:
            r2 = cri.para_focos(geom, hasta, sitio=sitio)
        except cri.SinBase as e:
            base['nota'] = 'Sin acercamiento: %s.' % e
            return base
        zs = r2['zs']
        foco = r2['foco']
        evaluada = r2['evaluada']
        ia = r2['ref']
        base['fecha_img'] = r2['fecha_img']
        # Ventana real de ocurrencia y satelite de la escena. Viajan hasta el
        # informe: sin esto el cliente lee una fecha exacta que el dato no sostiene,
        # y un foco no se puede auditar contra el satelite que lo produjo.
        for k in ('fecha_previa', 'dt_dias', 'fecha_imprecisa',
                  'sat', 'sat_corregido'):
            base[k] = r2.get(k)
        # La referencia ya NO es una fecha: es la trayectoria del propio pixel.
        # Se declara como tal en vez de inventar una fecha que no existe.
        base['fecha_ref'] = 'trayectoria %s a %s' % (r2['base_desde'],
                                                     r2['base_hasta'])
        base['_idx_escena'] = None
        act = ref = None
    else:
        try:
            escenas = _cobertura_por_escena(geom, desde, hasta)
            act, ref = _par_de_fechas(escenas, hasta)
        except SinPar as e:
            base['nota'] = 'Sin acercamiento: %s.' % e
            return base
        # La compuerta de dosel se exige SOLO en la referencia.
        ia, ir = _par_enmascarado(act[1], ref[1], geom)
        delta = ia.subtract(ir)
        zs = {e: _z_robusto(delta, geom, e, piso) for e in cfg.EJES}
        foco = _mascara_focos(zs, z)
        evaluada = delta.select(cfg.EJES[0]).mask().rename('u')

    # AREA REALMENTE TESTEADA. El numerador (los focos) se mide sobre la geometria
    # con buffer negativo Y con la compuerta de FVC aplicada en LAS DOS fechas. Si
    # el denominador es el area declarada del poligono completo, el porcentaje
    # SUBESTIMA entre 1,4x y 2x: un lote donde todo lo observable cayo en los dos
    # ejes se le informaba al productor como "70% del lote". Se mide la mascara de
    # la interseccion —que es exactamente sobre lo que corrio el test— y el
    # porcentaje se calcula contra eso, declarando ademas que fraccion del lote es.
    area_util_m2 = ee.Number(
        evaluada.selfMask()
        .multiply(ee.Image.pixelArea())
        .reduceRegion(reducer=ee.Reducer.sum(), geometry=geom, scale=ESCALA,
                      maxPixels=1e9, bestEffort=True).get('u'))
    area_util_ha = float(ee.Algorithms.If(
        area_util_m2, area_util_m2, 0).getInfo() or 0) / 1e4

    # Sal y pimienta fuera, y el test se resuelve en la grilla de 20 m declarada.
    proj = ia.projection().atScale(ESCALA)
    limpio = (foco.focalMode(1.5, 'square', 'pixels')
              .reproject(proj).selfMask().rename('foco'))
    # Severidad del foco: el z del PRIMER eje (humedad), con signo. Va con nombre
    # estable `z_sev` porque la app y el informe lo leen; los z de cada eje van
    # ademas con su propio nombre, para poder auditar cual disparo.
    # `z_sev` se guarda ORIENTADO de modo que **MAS NEGATIVO = PEOR**, sea cual sea
    # el eje. Los dos consumidores de abajo asumen esa convencion: el orden ascendente
    # (peor primero) y el corte `z_sev <= -(Z_FOCO+1)` para 'alta'.
    #
    # EL MULTIPLICADOR ES `-SIGNO`, NO `SIGNO`. `_mascara_focos` usa
    # `z*SIGNO >= Z_FOCO`, o sea que `z*SIGNO` es POSITIVO cuando hay deterioro; para
    # dejarlo negativo hay que invertirlo una vez mas.
    #
    #     NDMI  SIGNO=-1  deterioro z=-3,45  ->  z*(-SIGNO) = -3,45   negativo OK
    #     PSRI  SIGNO=+1  deterioro z=+3,45  ->  z*(-SIGNO) = -3,45   negativo OK
    #
    # MEDIDO 2026-07-27 en produccion con el signo mal: `z_sev` salia +3,45 con
    # `z_ndmi` -3,45, asi que NINGUN foco alcanzaba nunca el corte de 'alta' (todos
    # 'media') y el orden quedaba invertido — F1 era el foco MAS LEVE, justo el que
    # el tecnico visita primero. No rompia nada visible: entregaba, con la prioridad
    # al reves.
    from .ranking import SIGNO          # import local: ranking importa config, no focos
    _eje0 = cfg.EJES[0]
    apilado = limpio.addBands(
        zs[_eje0].multiply(-SIGNO[_eje0]).rename('z_sev'))
    for e in cfg.EJES:
        apilado = apilado.addBands(zs[e].rename('z_' + e.lower()))
    vec = (apilado
           .reduceToVectors(reducer=ee.Reducer.mean(), geometry=geom,
                            scale=ESCALA, geometryType='polygon',
                            eightConnected=True, labelProperty='foco',
                            maxPixels=1e9, bestEffort=True))
    vec = (vec.map(lambda f: f.set('area_ha', f.geometry().area(1).divide(1e4)))
              .filter(ee.Filter.gte('area_ha', mmu_ha)))
    fc = vec.getInfo()

    area_lote = float(feat['properties'].get(sitio.campo_area, 0) or 0)
    focos, total = [], 0.0
    for i, f in enumerate(sorted(fc.get('features', []),
                                 # z_sev ya viene orientado: ascendente = peor primero
                                 key=lambda x: (x['properties'].get('z_sev') or 0))):
        p = f['properties']
        a = round(float(p.get('area_ha', 0)), 3)
        total += a
        props = {
            'id': '%s-F%d' % (lote_id, i + 1),
            'etiqueta': 'F%d' % (i + 1),
            'lote_id': lote_id, 'orden': i + 1,
            'area_ha': a,
            # % del AREA TESTEADA (no del poligono declarado): es la unica base
            # sobre la que el numerador pudo medirse.
            'pct_util': round(100 * a / area_util_ha, 2) if area_util_ha else None,
            'pct_lote': round(100 * a / area_lote, 2) if area_lote else None,
            'z_sev': round(float(p.get('z_sev') or 0), 2),
            'ejes': '+'.join(cfg.EJES),
            'fecha_img': base['fecha_img'], 'fecha_ref': base['fecha_ref'],
            'status': 'pending',
        }
        for e in cfg.EJES:
            k = 'z_' + e.lower()
            props[k] = round(float(p.get(k, 0)), 2)
        focos.append({'type': 'Feature', 'geometry': f['geometry'],
                      'properties': props})

    # PERSISTENCIA. Solo si hay focos: sin focos no hay nada que confirmar y no se
    # gasta una evaluacion extra del criterio.
    if focos:
        pers, azar, fecha_ant = _persistencia(sitio, feat, base['fecha_img'], focos)
        if pers is not None:
            piso = (azar or 0.0) * FACTOR_PERSISTENCIA
            for f_, p_ in zip(focos, pers):
                pp = float(p_ or 0.0)
                f_['properties']['persistencia_pct'] = round(100 * pp, 1)
                f_['properties']['persistencia_azar_pct'] = round(100 * (azar or 0), 2)
                f_['properties']['fecha_anterior'] = fecha_ant
                # 'sin_confirmar' NO significa falso: un evento nuevo y real tampoco
                # estaba antes. Significa que esta escena sola no lo confirma.
                f_['properties']['confirmacion'] = (
                    'persistente' if pp > piso else 'sin_confirmar')
        else:
            for f_ in focos:
                # No se pudo mirar la escena anterior. NO es 'sin_confirmar': es que no
                # se sabe, y las dos cosas no pueden compartir rotulo.
                f_['properties']['confirmacion'] = 'no_evaluable'
                f_['properties']['persistencia_pct'] = None

    base.update({
        'focos': focos, 'area_focos_ha': round(total, 3),
        'pct_util': round(100 * total / area_util_ha, 2) if area_util_ha else None,
        'pct_lote': round(100 * total / area_lote, 2) if area_lote else None,
        'area_util_ha': round(area_util_ha, 3),
        'area_lote_ha': round(area_lote, 3) if area_lote else None,
        # `fecha_img` y `fecha_ref` ya vienen puestas por el bloque de criterio.
        # En v2 la referencia NO es una fecha: es la trayectoria del propio pixel,
        # y se declara como tal en vez de inventar una fecha que no existe.
        # Sobre que fraccion del campo se testeo, en cada una de las dos fechas.
        # Sin esto no se puede juzgar si el "0 focos" significa campo limpio o
        # analisis hecho sobre media hectarea.
        'cobertura_img': round(act[2], 3) if act else None,
        'cobertura_ref': round(ref[2], 3) if ref else None,
        # Id de la escena usada. Lo necesita el informe para pedir el MISMO recorte
        # RGB de fondo: un mapa con la foto de otra fecha le mostraria al tecnico un
        # campo que no es el que se analizo.
        '_idx_escena': act[1] if act else base.get('_idx_escena'),
    })
    if not focos:
        # NO se afirma que el lote "salio de control por su promedio": en el modo
        # campo chico NO HAY RANKING, ningun lote salio de control por nada, y esa
        # nota fabricaba una alerta a partir de un resultado limpio. Se dice lo unico
        # que este modulo puede afirmar: se miro y el cambio no esta concentrado.
        base['nota'] = ('Se evaluo el lote y no hay ninguna mancha de al menos '
                        '%.2f ha con cambio en los dos ejes a la vez.' % mmu_ha)
    return base


def detectar(sitio, lote_ids, hasta, z=Z_FOCO, mmu_ha=MMU_HA, verbose=True):
    """Acercamiento sobre los lotes indicados. Un lote que falla no frena al resto."""
    with open(sitio.lotes_geojson, encoding='utf-8') as fh:
        gj = json.load(fh)
    por_id = {str(f['properties'].get(sitio.campo_id)): f for f in gj['features']}
    out = {}
    for lid in [str(x) for x in lote_ids]:
        feat = por_id.get(lid)
        if feat is None:
            out[lid] = {'lote_id': lid, 'focos': [], 'area_focos_ha': 0.0,
                        'pct_lote': None, 'fecha_img': None, 'fecha_ref': None,
                        'error': 'lote_ausente',
                        'nota': 'El lote no esta en el GeoJSON del sitio.'}
            continue
        try:
            r = detectar_lote(sitio, feat, hasta, z=z, mmu_ha=mmu_ha)
        except Exception as e:                       # noqa: BLE001 — se declara
            r = {'lote_id': lid, 'focos': [], 'area_focos_ha': 0.0,
                 'pct_lote': None, 'fecha_img': None, 'fecha_ref': None,
                 # AVERIA, no falta de escenas. Si TODOS los lotes caen aca, el sitio
                 # no es "no evaluable por nubes": esta roto, y tiene que despertar a
                 # alguien. Ver main._entregar_acercamiento.
                 'error': type(e).__name__,
                 'nota': 'Acercamiento no disponible (%s).' % type(e).__name__}
        out[lid] = r
        if verbose:
            n = len(r['focos'])
            print('  %-14s %d foco(s)  %.2f ha  %s%%  %s'
                  % (lid, n, r['area_focos_ha'],
                     r['pct_lote'] if r['pct_lote'] is not None else '-',
                     r.get('nota') or ''), flush=True)
    return out


def control_nulo(sitio, lote_ids, hasta, z=Z_FOCO, mmu_ha=MMU_HA, verbose=True):
    """⚠️ NO ES UNA PUERTA VALIDA. NO PUBLICAR SU NUMERO. Auditado 2026-07-26.

    Se conserva porque el diagnostico esta abajo y sirve de referencia, pero
    `main.py` ya NO la corre y el informe ya NO la imprime.

    POR QUE NO SIRVE
    ----------------
    El detector marca la cola de DETERIORO y esta "nula" marca la cola de MEJORA
    del MISMO campo de delta, centrado en la MISMA mediana y escalado por el MISMO
    MAD, sobre el MISMO par de fechas. No son dos experimentos: son las dos mitades
    de una distribucion. **Estan anticorrelados por construccion**: todo lo que el
    detector manda a la cola inferior sale de la superior, y ademas arrastra la
    mediana e infla el MAD. Cuanto mas marca el detector, MENOS marca la nula.

    MEDIDO (simulacion con los mismos estimadores, rho=0,85 entre ejes, 30 replicas):

        escenario                        detector   nula invertida
        delta simetrico (H0 pura)           1,09%        1,01%
        sombra de nube / gradiente         25,01%        0,09%   <-- PASA
        foco real en 4% del lote            4,59%        0,88%

    O sea: **funciona solo cuando no hace falta**. Frente al artefacto numero uno
    del acercamiento —un desplome espacialmente estructurado y comun a los dos
    ejes, como una sombra residual o un gradiente de aerosol— el detector marca el
    25% del lote y la puerta lo aprueba.

    Y el corolario que invierte la lectura de lo que ya se habia reportado: **un
    0,00% no es una validacion, es el sintoma.** Bajo H0 pura esta nula da ~1%. Un
    cero medido sobre un lote real dice que el campo de delta estaba fuertemente
    asimetrico — evidencia A FAVOR del artefacto, que se estaba leyendo como
    evidencia en contra.

    QUE HARIA FALTA
    ---------------
    Una nula que no comparta el estimador con el detector. Dos caminos:
      · nula sintetica por lote: campo de ruido con el semivariograma intra-lote y
        la correlacion entre ejes medidos en el dato real (es lo que se hizo bien en
        `ranking.control_nulo`);
      · el MISMO criterio y el MISMO sentido, sobre pares de fechas de una ventana
        SIN evento y sobre lotes NO alertados.
    RAZONAMIENTO ORIGINAL, QUE RESULTO FALSO — se deja escrito porque el error es
    instructivo: "un lote no puede estar mejorando y deteriorandose en el mismo
    pixel, asi que lo que salga por el lado de la mejora es la tasa de falsa alarma".
    El paso en falso esta en el "asi que": las dos colas no son independientes, son
    complementarias sobre la misma distribucion centrada en la misma mediana.
    """
    with open(sitio.lotes_geojson, encoding='utf-8') as fh:
        gj = json.load(fh)
    por_id = {str(f['properties'].get(sitio.campo_id)): f for f in gj['features']}
    import pandas as pd
    marcado, evaluados = [], 0
    for lid in [str(x) for x in lote_ids]:
        feat = por_id.get(lid)
        if feat is None:
            continue
        geom = _geom_lote(sitio, feat)
        desde = str(pd.Timestamp(hasta) - pd.Timedelta(days=VENTANA_DIAS))[:10]
        try:
            escenas = _cobertura_por_escena(geom, desde, hasta)
            act, ref = _par_de_fechas(escenas, hasta)
        except SinPar:
            continue
        ia, ir = _par_enmascarado(act[1], ref[1], geom)
        delta = ia.subtract(ir)
        zs = {e: _z_robusto(delta, geom, e) for e in cfg.EJES}
        # Sentido INVERTIDO en TODOS los ejes: las colas de mejora.
        nulo = _mascara_focos(zs, z, invertir=True)
        proj = ia.select(cfg.EJES[0]).projection().atScale(ESCALA)
        limpio = (nulo.focalMode(1.5, 'square', 'pixels')
                  .reproject(proj).selfMask())
        # reduceToVectors consume la PRIMERA banda como etiqueta y necesita al menos
        # una mas para el reducer; con una sola banda falla con "Need 1+1 bands".
        vec = (limpio.rename('foco').addBands(ee.Image.constant(1).rename('n'))
               .reduceToVectors(
            reducer=ee.Reducer.count(), geometry=geom, scale=ESCALA,
            geometryType='polygon', eightConnected=True, labelProperty='foco',
            maxPixels=1e9, bestEffort=True)
            .map(lambda f: f.set('area_ha', f.geometry().area(1).divide(1e4)))
            .filter(ee.Filter.gte('area_ha', mmu_ha)))
        a = float(ee.Number(vec.aggregate_sum('area_ha')).getInfo() or 0)
        area_lote = float(feat['properties'].get(sitio.campo_area, 0) or 0)
        if area_lote > 0:
            marcado.append(100 * a / area_lote)
            evaluados += 1
            if verbose:
                print('  [nulo] %-14s %.2f%%' % (lid, marcado[-1]), flush=True)
    if not evaluados:
        return None
    tasa = sum(marcado) / len(marcado)
    if verbose:
        print('\n  PUERTA acercamiento — falsa alarma: %.2f%% del area '
              '(%d lotes)' % (tasa, evaluados))
        print('  (referencia: un corte simple de z<=-1,3 marca 9,7% por construccion)')
    return tasa


def a_geojson(sitio, resultados, perimetro=None):
    """FeatureCollection en el formato que LEE PIX Scout.

    Mismos nombres de campo que `main._geojson_salida`: no son decorativos, son la
    interfaz con la app. El perimetro va primero con `tipo:'perimetro'` para que la
    app lo use de marco y no lo liste como foco.
    """
    feats = []
    if perimetro is not None:
        feats.append({'type': 'Feature', 'geometry': perimetro,
                      'properties': {'tipo': 'perimetro',
                                     'id': '%s-PERIMETRO' % sitio.clave,
                                     'hacienda': sitio.titulo}})
    for lid, r in resultados.items():
        for f in r['focos']:
            p = dict(f['properties'])
            p.update({'hacienda': sitio.titulo,
                      'cultivo': getattr(sitio, 'cultivo', '') or None,
                      # `confirmacion` viaja para que el registro del tecnico quede
                      # atado a si el foco ya estaba antes o no. NO se muestra como
                      # severidad: es trazabilidad, no prioridad.
                      'confirmacion': p.get('confirmacion'),
                      'name': '%s / %s' % (lid, p['etiqueta']),
                      # z_sev orientado: mas negativo = peor, para cualquier eje.
                      'sev': 'alta' if (p.get('z_sev') or 0) <= -(Z_FOCO + 1) else 'media'})
            feats.append({'type': 'Feature', 'geometry': f['geometry'],
                          'properties': p})
    return {'type': 'FeatureCollection', 'features': feats}
