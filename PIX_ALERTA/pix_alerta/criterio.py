# -*- coding: utf-8 -*-
"""CRITERIO v2: trayectoria por pixel + Mahalanobis.  **EN PRODUCCION.**

Criterio por defecto desde 2026-07-29 (`config.CRITERIO = 'v2'`). v1 sigue
disponible en `focos.py` para poder comparar, no como camino de produccion.

LA EVIDENCIA, Y UNA CORRECCION DE AUDITORIA DEL 2026-07-29
----------------------------------------------------------
⚠️ Este docstring citaba `medicion/calibrar_criterio.py` como el arnes que aprobo v2,
con una tabla de tasas por lote. **Ese archivo NO EXISTIA en el repositorio** — no
estaba en el historial de git ni en `.gitignore`. O sea que los numeros que
justificaron poner v2 en produccion no se podian reproducir. El arnes se escribio el
2026-07-29 y esto es lo que mide, sobre 34 combinaciones lote-fecha reales:

    modelo                  MEDIANA (peor lote)   MAXIMO (peor lote)
    recta (este criterio)         0,58%                2,53%
    relativa_agrupada             3,23%                4,38%

    por lote, con el criterio en produccion:
    lote                 n fechas   MEDIANA   MAXIMO
    SANTO_ANTONIO-01         8       0,08%     1,77%
    SANTO_ANTONIO-02         9       0,31%     2,21%
    SAO_FRANCISCO-01         9       0,01%     2,53%
    SAO_FRANCISCO-02         8       0,58%     2,35%

Con alfa declarada del 1%, eso es aceptable: la mediana queda por debajo y el maximo
en 2,5 veces. Y el MAXIMO puede incluir eventos reales, porque no hay verdad de campo
para descartarlos — es una cota superior de la falsa alarma, no la falsa alarma.

Los numeros viejos (mediana 0,00%, maximo 2,17%) quedan en el mismo orden que los
nuevos, asi que la conclusion original probablemente era correcta. Pero no era
verificable, y eso es un defecto por si solo.

Y ademas recupera area evaluable, que era el otro cuello de botella:

    area evaluada de SANTO_ANTONIO-02:   v1: 49%   ->   v2: 75%
    los otros tres lotes:                          92% a 95%

PERSEGUIR SD(z)=1 FUE UN DESVIO, Y QUEDA ESCRITO
------------------------------------------------
Esa igualdad solo vale si la distribucion es normal; con colas pesadas se puede
tener SD 1,8 con la tasa perfecta o SD 0,4 con la tasa disparada. Lo que decide en
un producto de alerta es la TASA EMPIRICA sobre fechas sin evento. Se llego ahi
despues de cuatro intentos de calibrar por SD; la bitacora esta mas abajo porque el
recorrido vale mas que el resultado.

QUE REEMPLAZA
-------------
El criterio v1 hacia: residuo contra LA ESCENA LIMPIA ANTERIOR, z por eje con MAD
TRANSVERSAL (espacial) de ese par de fechas, y conjuncion `z1<=-2 Y z2<=-2`.

Los cuatro defectos medidos el 2026-07-29, y como los ataca este diseño:

1. **SD(z) va de 0,38 a 1,56 segun lote y eje** (deberia ser 1). Un z mal escalado
   significa que la tasa de falsa alarma NO es la que el umbral implica. Peor: PSRI
   daba SD=0,38, o sea que el corte en -2 equivalia a -5 sigmas reales y como
   segundo eje habria matado toda deteccion.
   -> **La escala pasa a ser TEMPORAL Y POR PIXEL**: la MAD de los residuos del
      propio pixel contra su propia trayectoria.
      ⚠️ MEDIDO 2026-07-29: ESTO NO LOGRO SD(z)=1. Da 0,19 a 1,30 sobre los 4 lotes
      reales, o sea el mismo orden de dispersion que tenia v1. La razon es que la MAD
      de los residuos contra una RECTA no mide ruido: mide sobre todo el error del
      modelo (ver el bloque de arriba). La frase original —"lo que hace que el z tenga
      SD 1 por construccion"— era un razonamiento, no una medicion, y la medicion la
      contradice.

2. **La conjuncion de dos z no controla alfa**: la tasa depende de la correlacion r
   entre ejes, que va de 0,17 a 0,82 entre lotes -> el error tipo I varia varias
   veces sin que pase nada en el campo.
   -> **Mahalanobis con la covarianza medida**: `d2 >= chi2(2, 1-alfa)` da alfa FIJA
      y comparable entre lotes, y ademas usa la direccion de la anomalia, no dos
      cortes marginales.

3. **Cobertura 49%, que es exactamente 0,70^2**: no se pierde por nubes, se pierde
   por exigir DOS fechas limpias.
   -> **Solo la fecha `t` tiene que estar limpia.** La referencia la aporta la
      trayectoria, que se arma con todas las observaciones limpias previas. La
      cobertura vuelve a ser p, no p^2.

4. **Var(residuo) = 2*sigma^2 con una sola escena de referencia** (las dos fechas
   aportan ruido). Con N observaciones en la base pasa a `sigma^2*(1+1/N)`: con N=5
   se detecta un cambio 23% mas chico A LA MISMA tasa de falsa alarma.

LO QUE ESTE MODULO DECIA Y NO ERA CIERTO
----------------------------------------
Aca decia: «la nula sigue siendo TEMPORAL: cada pixel contra su propia historia. No se
compara con vecinos ni con otros lotes». **La segunda frase es falsa**, y se ve
leyendo el codigo: la matriz de la Mahalanobis se calcula con

    reduceRegion(ee.Reducer.centeredCovariance(), geometry=geom)

sobre los z de LA ESCENA EVALUADA, o sea que es una covarianza ESPACIAL entre los
pixeles del lote. El residuo es temporal; la NORMALIZACION es espacial. La decision
final si se compara con los vecinos.

Eso tiene una consecuencia que hay que declarar: la referencia se estima sobre datos
que contienen el evento que se busca. Cuanto mas grande sea el evento, mas infla la
covarianza y menos se destaca. No esta medido a campo cuanto pesa —haria falta verdad
de campo para inyectar un evento real— pero el mecanismo esta ahi y no es opinable.

LO QUE SE MIDIO DE LAS TRIPAS, Y NO CIERRA
------------------------------------------
Sobre los 4 lotes reales al 2026-07-16 (`medicion/verificar_escala_real.py` y
`medicion/comparar_trayectoria.py`):

    · SD(z) va de 0,19 a 1,30 entre lotes y ejes. Deberia ser 1 en todos. Con esa
      dispersion, el umbral chi2 NO significa el mismo alfa en cada lote — que es
      exactamente el defecto que este docstring dice mas abajo venir a corregir de v1
      (donde iba de 0,38 a 1,56). **No lo corrigio.**
    · sigma vale 0,12 a 0,18 en unidades del indice, contra un ruido de corto plazo
      de 0,024 a 0,060 medido con diferencias entre escenas consecutivas. O sea que
      la escala es 2,7 a 6,5 veces el ruido: entre el 63% y el 85% de lo que se llama
      "ruido" es ERROR DEL MODELO, porque una recta no describe al trigo entre
      emergencia y llenado de grano. Eso comprime el z y vuelve sordo al criterio.
    · la mediana de z da -0,85 y -0,60: no es dispersion, es SESGO. La recta
      extrapola hacia arriba mientras el cultivo se aplana.

EL CANDIDATO SE RECALIBRO Y QUEDA RECHAZADO. Y DE PASO PRODUCCION QUEDO VALIDADA.
--------------------------------------------------------------------------------
Se probo un modelo que arregla las tres cosas de arriba (`MODELO = 'relativa_agrupada'`:
centrado por la mediana del lote en cada fecha + escala agrupada entre pixeles). MEDIDO:
lleva la razon sigma/ruido de 3,3 a 1,1, el sesgo de -0,85 a -0,01 y el rango de SD(z) de
0,19-1,30 a 0,86-1,54. Con el chi2 marcaba 3 a 4 veces mas, asi que se dejo apagado hasta
recalibrarlo. Se recalibro (`medicion/recalibrar.py`) y el resultado es concluyente.

PASO 1 — igualar la tasa. Barriendo umbrales de d2 sobre las fechas sin evento, para que la
mediana del peor lote iguale la que da produccion hoy (0,31%):

    modelo                        umbral   MEDIANA peor   MAXIMO peor
    recta (produccion)              9,21       0,31%         2,21%
    relativa_agrupada              27,00       0,24%         1,51%

El candidato necesita un umbral de 27 — casi TRES veces el chi2 al 1%. Con SD(z)=1,2 la
escala sola explicaria 13,3; que haga falta 27 dice que ademas tiene COLAS PESADAS, que es
lo esperable de un estimador de escala con pocas observaciones.

PASO 2 — a tasa igualada, cual marca cosas que PERSISTEN. Sin verdad de campo, la
persistencia es la unica medida de calidad disponible: lo que es una condicion del lote
sigue ahi en la escena siguiente; el ruido se mueve. Se mide como el solape de lo marcado
hoy con lo marcado en la escena limpia anterior, dividido por el solape que daria el azar.

    modelo                        marcado         persistencia
    recta (produccion)          1,14 a 2,15%   16,4x a 42,7x el azar   (4 lotes)
    relativa_agrupada           0,06%          no computable: no marca nada

**A la tasa que hace falta para no marcar de mas, el candidato deja de marcar.** No es una
mejora: es menos deteccion a igual tasa de falsa alarma. Queda RECHAZADO, y el codigo se
conserva porque documenta el intento y porque el arnes sirve para el proximo candidato.

Y EL HALLAZGO QUE MAS VALE DE TODA ESTA MEDICION, que no se buscaba:

    persistencia de lo que marca PRODUCCION, sobre los 4 lotes reales:
        SANTO_ANTONIO-01  42,7x     SAO_FRANCISCO-01  16,4x
        SANTO_ANTONIO-02  36,8x     SAO_FRANCISCO-02  27,1x     media 30,8x

Lo que el motor marca **ya estaba en la escena anterior mucho mas de lo que daria el azar,
en los cuatro lotes**. Es una validacion que NO necesita verdad de campo y que el criterio
podia fallar: dice que lo marcado es un rasgo REAL del lote y no ruido que paso el umbral.

QUE HAY QUE CORREGIR DE LO QUE ESTE DOCSTRING DECIA ANTES
--------------------------------------------------------
Aca se venia insistiendo con que las tripas «no dan» —SD(z) entre 0,19 y 1,30, sigma 3 a 6
veces el ruido, sesgo de -0,85— y se sospechaba SORDERA. Las mediciones siguen siendo
ciertas, y la conclusion que se saco de ellas era apresurada:

· **el diagnostico interno NO predice la calidad de la salida.** El modelo con las tripas
  arregladas produce peor salida que el que las tiene mal.
· lo que el motor es, medido, es **CONSERVADOR**: marca poco —en 1 de 5 fechas— y lo que
  marca es solido (30,8x el azar). Para un producto de alerta que dirige recorridas, ese
  es el lado correcto del error.
· lo que sigue SIN medir es la SENSIBILIDAD A PROBLEMAS REALES: cuanto se le escapa. La
  persistencia dice que lo que marca es real; no dice cuanto real deja pasar. Eso lo
  contestan los puntos de control a campo (`pix_alerta/controles.py`).

LA POTENCIA DEL DETECTOR SI SE MIDIO, Y NO ES UN NUMERO SOLO
------------------------------------------------------------
Inyectando caidas sinteticas de magnitud conocida en la imagen real
(`medicion/sensibilidad.py`), sobre un parche de 0,75 ha en SANTO_ANTONIO-02:

    caida            sigma BAJO        sigma MEDIO       sigma ALTO
    CONTROL (0)       0%   no           0%   no           0%   no
    2 x ruido         0%   no          19%  0,15 ha no    5%  0,04 ha no
    3 x ruido         4%   no          36%  0,27 ha SI   18%  0,14 ha no
    5 x ruido        34%  0,25 ha SI   47%  0,35 ha SI   27%  0,20 ha SI

  («SI» = las hectareas marcadas superan la unidad minima de mapeo y el foco LLEGA)

· Por debajo de 2 veces el ruido de corto plazo, el motor no ve nada en ninguna parte.
· 5 veces el ruido de NDMI son 0,225 unidades = ~45% del agua del dosel de este trigo.

**Y LA SENSIBILIDAD NO ES UNIFORME DENTRO DEL LOTE.** La misma caida inyectada dio z de
-0,93 a -3,02 y d2 de 0,43 a 14,44 —treinta veces— segun donde cayera, con la inyeccion
verificada identica (0,2250) y los tres parches 100% evaluables. La causa es que
**SIGMA VARIA 6,1 VECES DENTRO DEL LOTE** (p5 0,031, p50 0,146, p95 0,186 en NDMI), y sigma
es lo que divide al residuo. Que sigma sea tan heterogenea es consecuencia directa de que
mide sobre todo el ERROR DEL MODELO de la recta, no ruido — y esa geografia no tiene nada
que ver con la sanidad del cultivo.

Es un limite del criterio que hay que declarar al cliente: hay partes del lote donde el
motor es mas sordo que en otras, y no por el cultivo.

LIMITES QUE HAY QUE DECLARAR
----------------------------
· **VENTANA CIEGA.** Un deterioro que empiece DENTRO de la ventana de linea base se
  incorpora a la propia referencia y no se detecta. Con N minimo de observaciones y
  cadencia real de ~10 dias utiles, eso es el primer mes de campaña. Va al informe.
· Un deterioro MUY lento tampoco: la mediana movil lo absorbe. Es el mismo limite
  que tiene cualquier referencia adaptativa, y es el precio de no usar una tabla de
  valores esperados (que no existe como estandar transferible).
· Sigue SIN tasa de falsa alarma validada a campo. Esto mejora la CALIBRACION
  nominal; la puntería real solo la puede medir el campo.
"""
import ee

from . import config as cfg
from . import series as sr

# --- parametros, todos declarados ---------------------------------------------
ESCALA = 20               # m
# Observaciones limpias MINIMAS en la linea base. Con menos, la mediana y la MAD
# temporal son ruido: dos puntos no definen una trayectoria ni una dispersion.
MIN_BASE = 4
# VENTANA DE LINEA BASE. El default de 75 dias sirve para un cultivo anual de ciclo
# corto; para caña (300-550 dias) es demasiado corta y para una hortaliza de 70
# dias se come la campaña entera. `ventana_de(sitio)` la deriva del ciclo declarado
# del cultivo — hay una tabla por especie en `ciclos.py`— y este valor solo se usa
# cuando no hay sitio de donde sacarla.
VENTANA_BASE_DIAS = 75
# Fraccion del ciclo del cultivo que abarca la linea base. Con 0,6 el motor mira
# poco mas de la mitad del ciclo hacia atras: suficiente para tener trayectoria y
# poco como para no arrastrar una fenologia de hace tres meses.
FRACCION_CICLO_BASE = 0.60


def ventana_de(sitio, default=VENTANA_BASE_DIAS):
    """Dias de linea base segun el CICLO del cultivo del sitio.

    Un motor que sirva para varios cultivos no puede tener 75 dias cableados: es
    medio ciclo de trigo, un quinto de un ciclo de caña y toda la vida de una
    hortaliza. Se deriva del ciclo declarado y se acota para que siga siendo
    manejable en cultivos muy largos.
    """
    from . import ciclos
    try:
        ciclo = (getattr(sitio, 'ciclo_dias', None)
                 or ciclos.CICLOS[getattr(sitio, 'cultivo', '')][0])
    except Exception:
        return default
    return int(min(max(ciclo * FRACCION_CICLO_BASE, 40), 180))
# Piso de escala en unidades del indice. Mismo argumento que en `focos.SIGMA_MINIMA`:
# por debajo de esto la diferencia entre dos fechas no se puede atribuir al cultivo
# con S2, es ruido radiometrico + BRDF + aerosol residual.
# ⚠️ MEDIDO SOBRE TRIGO EN PARANA. Es el orden del ruido radiometrico + BRDF +
# aerosol residual de S2 entre dos fechas, y **hay que recalibrarlo por cultivo y
# region**: `medicion/calibrar_criterio.py` mide la tasa de marcado sobre fechas sin
# evento, que es lo que dice si el piso esta bien puesto. Un piso demasiado bajo
# hace que el criterio corra sobre ruido; demasiado alto lo vuelve sordo.
SIGMA_MINIMA = 0.010

# MODELO DE TRAYECTORIA Y DE ESCALA. Default 'recta' = lo que corre hoy.
#
# MEDIDO el 2026-07-29 sobre los 4 lotes reales de trigo (`medicion/
# comparar_trayectoria.py`), al 2026-07-16:
#
#   modelo                razon sigma/ruido   mediana(z)      SD(z) y su rango
#   recta (hoy)              3,3 y 5,0       -0,85 / -0,60   0,50  (0,19 a 1,30)
#   cuadratica               0,7 y 1,2       +1,03 / +1,90   1,52  (0,88 a 2,14)
#   recta relativa           1,1 y 1,3       -0,02 / +0,02   1,72  (0,85 a 2,74)
#   relativa_agrupada        1,1 y 1,4       -0,01 / +0,02   1,23  (0,86 a 1,54)
#
# COMO SE LEE:
# · `razon` es la escala del ajuste dividida por el ruido de corto plazo (estimado
#   con diferencias entre escenas consecutivas, que son casi inmunes a una tendencia
#   suave). Con la RECTA da 3,3 a 5,0: entre el 63% y el 85% de lo que el criterio
#   llama "ruido" es ERROR DEL MODELO — una recta no describe al trigo entre
#   emergencia y llenado de grano. Eso comprime el z y el criterio se vuelve sordo.
# · `mediana(z)` con la recta da -0,85: no es dispersion, es SESGO. La recta
#   extrapola hacia arriba mientras el cultivo se aplana, asi que TODO el lote cae
#   por debajo de su propia referencia.
# · El RANGO de SD(z) es lo que decide si el umbral significa lo mismo en cada lote.
#   Con la recta va de 0,19 a 1,30 (factor 6,8) — el mismo defecto que v2 declaraba
#   venir a corregir de v1, donde iba de 0,38 a 1,56.
#
# 'relativa_agrupada' hace DOS cosas, y cada una arregla una de las dos:
#   1. CENTRADO POR FECHA: al residuo de cada escena se le resta la mediana espacial
#      del residuo de esa escena. Absorbe todo error de modelo COMPARTIDO —fenologia,
#      clima del dia, calibracion del sensor— porque todos los pixeles lo tienen
#      igual. Es lo que lleva la razon de 3,3 a 1,1 y el sesgo de -0,85 a -0,01.
#   2. ESCALA AGRUPADA: el ruido se estima juntando los residuos de todos los pixeles
#      del lote (miles x n fechas) en vez de 8-9 por pixel. Es lo que baja el rango
#      de SD(z) de 0,85-2,74 a 0,86-1,54.
#
# ⚠️ PRECIO QUE HAY QUE DECLARAR AL CLIENTE: el centrado por fecha deja al criterio
# CIEGO a un evento uniforme sobre todo el lote (una helada, un deficit hidrico
# general). Si todos los pixeles caen lo mismo, la mediana cae con ellos y el residuo
# centrado no se mueve. Eso NO es un descuido: un evento que afecta al lote entero es
# indistinguible de fenologia mirando solo ese lote, y se detecta comparando el lote
# con OTROS lotes — que es el ranking entre lotes, y necesita >= 8 lotes.
MODELO = 'recta'
MODELOS = ('recta', 'relativa_agrupada')

# --- COMO SE AJUSTA LA TRAYECTORIA DEL PIXEL ---------------------------------
#
# EL PROBLEMA, Y ESTA MEDIDO. Mouret, F. et al. (2022), Comput. Electron. Agric.
# 198:106983 (DOI 10.1016/j.compag.2022.106983) senala el patron: **un pixel con
# anomalia real arrastra la recta de minimos cuadrados hacia si y encoge su propio
# residuo.** Cuanto mas grande el evento, menos detectable se vuelve — el estimador
# se sabotea justo cuando mas importa.
#
# MEDIDO EN GEE el 2026-08-03 sobre una serie de 10 puntos con tendencia real de
# -0,010/dia y una caida brusca de -0,22 en el ultimo punto:
#
#     ajuste       pendiente   ordenada   esperado en t=9   RESIDUO recuperado
#     (verdad)      -0,010      0,500          0,410           -0,210
#     MCO           -0,0215     0,531          0,338           -0,1375   <- pierde 35%
#     Theil-Sen     -0,010      0,500          0,410           -0,210    <- exacto
#
# El MCO absorbio la anomalia en la PENDIENTE: duplico la tasa de declive y subio la
# ordenada, y con eso se comio el 35% del residuo que el criterio necesita ver.
#
# POR QUE THEIL-SEN Y NO OTRO: es la mediana de las pendientes de todos los pares,
# con punto de ruptura 29% — hasta ~1 de cada 3 observaciones puede ser anomala sin
# mover la recta. Existe como reducer nativo (`ee.Reducer.sensSlope`), asi que no
# cuesta un viaje extra ni codigo propio.
#
# ⚠️ POR QUE EL DEFAULT SIGUE SIENDO 'mco': cambiar el ajuste **invalida la
# calibracion existente**. La tasa de falsa alarma medida (mediana 0,00%, maximo
# 0,2-2,2% sobre fechas sin evento) se midio CON MCO. La regla de la casa no cambia
# por tener un buen argumento: hace falta la razon POSITIVA medida —
#     medicion/calibrar_criterio.py --ajuste theilsen   (tasa sobre fechas sin evento)
#     medicion/sensibilidad.py      --ajuste theilsen   (anomalia minima detectable)
# y recien con las dos a favor se mueve el default.
AJUSTES = ('mco', 'theilsen')
AJUSTE = 'mco'

# --- Δt_max: hasta donde se puede FECHAR un evento ---------------------------
# Si la observacion limpia anterior esta a mas de esto, el foco pudo aparecer en
# cualquier momento del intervalo y el informe **no puede dar una fecha**: solo
# puede acotarla. Patron tomado de Sen4CAP (De Vroey et al. 2022, RSE 280:113145),
# que usa 60 dias y degrada la salida a un intervalo en vez de interpolar.
#
# 20 dias, y el numero sale de la propia disponibilidad medida: con S2B+S2C cada 5
# dias y 48% de dekadas utiles, dos escenas limpias consecutivas separadas por mas
# de 20 dias significan que se perdieron al menos 3 pasadas seguidas. A partir de
# ahi la ventana de ocurrencia es mas ancha que la dekada de entrega, y fechar el
# evento es una precision falsa.
DT_MAX_DIAS = 20
# Recorte robusto antes de agrupar cuadrados, en sigmas, y su factor de consistencia:
# recortar subestima sigma y el sesgo tiene forma cerrada (c=3 -> 0,99750).
RECORTE_SIGMAS = 3.0
RECORTE_FACTOR = 0.99750
# alfa NOMINAL del criterio. chi2 con 2 grados de libertad: d2 >= 9,21 <=> alfa=0,01.
# Es el numero que la conjuncion NO podia fijar.
# Cuanto se puede retroceder buscando una escena CON DATOS para evaluar, y cuanta
# cobertura minima se le exige. Con revisita de 5 dias y nubes, la ultima del
# calendario suele estar tapada: el 2026-07-25 dio 0,00 en los cuatro lotes.
VENTANA_ACTUAL_DIAS = 12
# Cobertura MINIMA de la escena que se evalua. Se toma el MISMO 0,70 que ya usa
# `focos.COB_MINIMA` para decidir si una escena sirve para testear — no un numero
# nuevo elegido a conveniencia.
#
# ⚠️ MEDIDO por que importa: con 0,35, SANTO_ANTONIO-02 elegia la escena del
# 2026-07-20 (cobertura 0,606, medio lote tapado) y el criterio marcaba 3 focos que
# estaban a 16, 20 y 68 m del borde de la nube. O sea: borde de nube otra vez, con
# el criterio nuevo. **El problema no era el criterio: era usar esa escena.** Una
# escena con el 40% del lote enmascarado tiene borde de nube por todas partes, y el
# residuo de bruma que SCL y CloudScore+ no atrapan escala con la cantidad de nube.
COB_MINIMA_ACTUAL = 0.70
ALFA = 0.01
CHI2 = {0.05: 5.991, 0.02: 7.824, 0.01: 9.210, 0.005: 10.597, 0.001: 13.816}


class SinBase(Exception):
    """No hay observaciones limpias suficientes para armar la trayectoria."""


# Fraccion MINIMA de pixel valido sobre el lote para que una escena entre a la base.
# NO es cosmetico: sin esto la coleccion incluye escenas del tile MGRS vecino que
# apenas rozan el lote, y tambien las tapadas por nube. MEDIDO: con la base sin
# filtrar, las dos escenas mas recientes de cada lote no se solapaban y el z salia
# **enteramente enmascarado** (px=0) — que era el origen de los "SD = 0,000" que
# parecian un resultado y eran una serie vacia.
COB_MINIMA_BASE = 0.30


def _coleccion_limpia(geom, desde, hasta, cob_minima=COB_MINIMA_BASE):
    """Imagenes con los ejes, enmascaradas a pixel valido. Sin compuerta de dosel.

    La compuerta de dosel NO va aca: se aplica una sola vez, sobre la linea base
    (ver `evaluar`). Aplicarla por escena es lo que censuraba justo la anomalia —
    un pixel que perdio dosel es el daño que se busca.
    """
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
           .filterDate(desde, hasta).filterBounds(geom))

    def preparar(img):
        img = ee.Image(img)
        valido = sr._mascara(img)
        ejes = sr._indices(img)
        # `copyProperties` con system:time_start NO es opcional: `_indices` arma
        # una imagen NUEVA y sin eso la marca de tiempo se pierde. El ajuste de la
        # trayectoria necesita el tiempo de cada escena, y sin el fallaba con
        # "Date: Parameter 'value' is required and may not be null".
        out = (ejes.select(list(cfg.EJES) + ['NDVI']).updateMask(valido)
               .copyProperties(img, ['system:time_start'])
               .set('fecha', ee.Date(img.get('system:time_start'))
                    .format('YYYY-MM-dd')))
        out = ee.Image(out)
        cob = valido.unmask(0, False).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=geom, scale=ESCALA,
            maxPixels=1e9, bestEffort=True).values().get(0)
        return out.set('cob', ee.Algorithms.If(cob, cob, 0))

    salida = col.map(lambda i: ee.Image(preparar(i)))
    if cob_minima:
        salida = salida.filter(ee.Filter.gte('cob', cob_minima))
    # UNA OBSERVACION POR FECHA. Un lote sobre un borde MGRS recibe DOS granulos de
    # la MISMA adquisicion (T22KEU y T22KEV): son la misma foto, no dos
    # observaciones. Contarlas dos veces metia pares con hueco CERO en la serie, y
    # esos pares —diferencia casi nula, fenologia nula— arrastraban el estimador de
    # ruido a cero. MEDIDO: SAO_FRANCISCO-01 daba dt=0 y SD(z)=0,03, o sea un sigma
    # ~30x lo que corresponde.
    # `distinct` conserva la PRIMERA de cada fecha, asi que se ordena por cobertura
    # descendente antes: queda la que mas lote cubre.
    # `distinct` devuelve una Collection generica y le hace perder el tipo: sin el
    # `ee.ImageCollection(...)` de abajo, `.count()` explota mas tarde con
    # "'FeatureCollection' object has no attribute 'count'".
    salida = salida.sort('cob', False).distinct(['fecha'])
    return ee.ImageCollection(salida.sort('system:time_start'))


def evaluar(geom, hasta, alfa=ALFA, min_base=MIN_BASE,
            ventana=None, escala=ESCALA, sitio=None, piso=None, modelo=None,
            umbral=None, inyeccion=None, ajuste=None):
    """Mahalanobis del residuo de la fecha `hasta` contra la trayectoria del pixel.

    Devuelve dict con:
        d2        imagen de distancia de Mahalanobis al cuadrado
        anomalia  mascara booleana d2 >= chi2 Y direccion de deterioro
        z         {eje: imagen de z temporal}
        n_base    imagen con cuantas observaciones tiene cada pixel en la base
        fecha     fecha de la escena evaluada
        umbral    el chi2 usado
    """
    import pandas as pd
    ventana = ventana or ventana_de(sitio)
    modelo = modelo or cfg.valor_de(sitio, 'modelo_criterio', MODELO)
    if modelo not in MODELOS:
        raise ValueError('modelo desconocido: %r. Hay: %s' % (modelo, MODELOS))
    if piso is None:
        piso = cfg.valor_de(sitio, 'sigma_minima', SIGMA_MINIMA)
    desde = str(pd.Timestamp(hasta) - pd.Timedelta(days=ventana))[:10]
    fin_base = str(pd.Timestamp(hasta) - pd.Timedelta(days=1))[:10]

    base = _coleccion_limpia(geom, desde, fin_base)

    # LA ESCENA A EVALUAR ES LA MAS RECIENTE **CON DATOS**, no la mas reciente.
    # Sin este chequeo se tomaba la ultima del calendario aunque estuviera 100%
    # nublada: paso el 2026-07-25, que dio cobertura 0,00 en los cuatro lotes, y
    # todo el z salia enmascarado sin decir por que.
    cand = _coleccion_limpia(
        geom, str(pd.Timestamp(hasta) - pd.Timedelta(days=VENTANA_ACTUAL_DIAS))[:10],
        str(pd.Timestamp(hasta) + pd.Timedelta(days=1))[:10])

    _e0 = list(cfg.EJES)[0]

    def _con_cobertura(img):
        img = ee.Image(img)
        cob = (img.select(_e0).mask()
               .unmask(0, False).reduceRegion(
                   reducer=ee.Reducer.mean(), geometry=geom, scale=escala,
                   maxPixels=1e9, bestEffort=True).values().get(0))
        return img.set('cob', ee.Algorithms.If(cob, cob, 0))

    cand = cand.map(_con_cobertura).filter(ee.Filter.gte('cob', COB_MINIMA_ACTUAL))

    # --- CALIDAD DE ESCENA: la bruma que pasa el filtro binario ---------------
    # ⚠️ AGREGADO 2026-07-29 DESPUES DE UN CASO MEDIDO. CloudScore+ se usaba solo como
    # decision por pixel: cada uno pasa o no pasa `CS_UMBRAL`. Un pixel con bruma leve
    # saca 0,62 y pasa. Si TODO el lote tiene bruma leve, pasan todos y la escena entra
    # como si estuviera limpia.
    #
    # Paso el 2026-07-05 sobre SANTO_ANTONIO-02: el 96% de los pixeles paso el umbral
    # binario, la escena entro, y el lote parecio derrumbarse — NDVI 0,928 (06-22) ->
    # 0,776 (07-05) -> 0,928 (07-10). Un trigo no hace eso. Y esa escena tambien habia
    # pasado la puerta de cobertura de arriba Y habria pasado la conjuncion de dos ejes,
    # porque **la bruma baja los DOS indices juntos**: la conjuncion no protege contra
    # contaminacion atmosferica, solo contra ruido independiente del sensor.
    #
    # MEDIDO con `medicion/calidad_escena.py`, promedio de `cs_cdf` sobre el lote en las
    # 7 fechas que pasaban la puerta de cobertura:
    #     05-31 0,911  06-02 0,916  06-05 0,917  06-22 0,918  07-10 0,929  07-15 0,926
    #     07-05 0,797  <- LA UNICA por debajo de 0,90, y es el artefacto
    # Con el piso en 0,85 se rechaza el artefacto y no se pierde ninguna limpia.
    if getattr(cfg, 'USAR_CLOUDSCORE', True):
        piso_cs = cfg.valor_de(sitio, 'cs_medio_minimo', cfg.CS_MEDIO_MINIMO)

        def _con_calidad(img):
            img = ee.Image(img)
            cs = sr._cloudscore(img)
            # Sin CloudScore+ no se puede juzgar la calidad: se deja pasar y se declara
            # en `cs_medio`, en vez de descartar la escena por falta del dato auxiliar.
            q = ee.Algorithms.If(
                cs,
                ee.Image(cs).select(cfg.CS_BANDA).rename('q').reduceRegion(
                    reducer=ee.Reducer.mean(), geometry=geom, scale=escala,
                    maxPixels=1e9, bestEffort=True).get('q'),
                1)
            return img.set('cs_medio', ee.Algorithms.If(q, q, 1))

        cand = cand.map(_con_calidad).filter(
            ee.Filter.gte('cs_medio', piso_cs))

    if not cand.size().getInfo():
        raise SinBase('sin escena con al menos %.0f%% de pixel valido Y calidad de '
                      'nube >= %.2f en los ultimos %d dias'
                      % (100 * COB_MINIMA_ACTUAL,
                         cfg.valor_de(sitio, 'cs_medio_minimo', cfg.CS_MEDIO_MINIMO),
                         VENTANA_ACTUAL_DIAS))
    actual = ee.Image(cand.sort('system:time_start', False).first())
    fecha_actual = actual.get('fecha').getInfo()

    ejes = list(cfg.EJES)
    n_base = base.select([ejes[0]]).count().rename('n_base')

    # --- TRAYECTORIA: recta por pixel, no una mediana ------------------------
    #
    # ⚠️ ESTO NO PUEDE SER UNA MEDIANA, y el error se midio. Con la mediana como
    # referencia, los residuos de la base quedan dominados por la FENOLOGIA —el
    # trigo cambia a lo largo de la ventana— y no por el ruido. La MAD de esos
    # residuos sale inflada, sigma sale grande y el z sale APLASTADO:
    #
    #     con mediana constante:  SD(z) = 0,14 a 0,55   (deberia ser 1)
    #
    # Con SD(z)=0,14 el corte en chi2 equivale a varias veces mas sigmas de las
    # declaradas y el criterio no marca NADA. Es el mismo error que ya se habia
    # visto con PSRI en v1, por otro camino.
    #
    # La referencia correcta es la TENDENCIA del propio pixel: se ajusta una recta
    # contra el tiempo y el residuo se mide contra la recta, no contra un nivel.
    # Asi la MAD estima el ruido y no el crecimiento del cultivo.
    dia0 = ee.Date(desde).millis()

    def _con_t(img):
        img = ee.Image(img)
        t = ee.Image(ee.Date(img.get('system:time_start')).millis()
                     .subtract(dia0).divide(86400000)).float().rename('t')
        return t.addBands(img.select(ejes)).updateMask(img.select(ejes[0]).mask())

    con_t = base.map(_con_t)
    ajuste = ajuste or cfg.valor_de(sitio, 'ajuste_trayectoria', AJUSTE)
    if ajuste not in AJUSTES:
        raise ValueError('ajuste desconocido: %r. Hay: %s' % (ajuste, AJUSTES))
    pend, orden = {}, {}
    for e in ejes:
        if ajuste == 'theilsen':
            # Theil-Sen: mediana de las pendientes de todos los pares. Punto de
            # ruptura 29%: hasta ~1 de cada 3 observaciones puede ser anomala sin
            # mover la recta. `sensSlope` devuelve 'slope'/'offset' (no 'scale').
            fit = con_t.select(['t', e]).reduce(ee.Reducer.sensSlope())
            pend[e] = fit.select('slope')
        else:
            fit = con_t.select(['t', e]).reduce(ee.Reducer.linearFit())
            pend[e] = fit.select('scale')      # pendiente por dia
        orden[e] = fit.select('offset')

    t_act = ee.Number(ee.Date(fecha_actual).millis()).subtract(dia0).divide(86400000)

    def _esperado(e, t):
        return orden[e].add(pend[e].multiply(ee.Image(ee.Number(t))))

    # Residuos CON SIGNO de la base contra su propia recta. Con signo y no en valor
    # absoluto porque el centrado por fecha necesita el signo; la MAD sale igual.
    def resid(img):
        img = ee.Image(img)
        t = (ee.Number(ee.Date(img.get('system:time_start')).millis())
             .subtract(dia0).divide(86400000))
        cap = [img.select(e).subtract(_esperado(e, t)).rename(e) for e in ejes]
        return (ee.Image.cat(cap).updateMask(img.select(ejes[0]).mask())
                .copyProperties(img, ['system:time_start']))

    res = base.map(resid)

    def _mediana_lote(img):
        """Mediana espacial del residuo de ESA fecha, como imagen constante."""
        img = ee.Image(img)
        m = img.reduceRegion(reducer=ee.Reducer.median(), geometry=geom,
                             scale=escala, maxPixels=1e9, bestEffort=True)
        corr = ee.Image.cat([
            ee.Image.constant(ee.Number(
                ee.Algorithms.If(m.get(e), m.get(e), 0))).rename(e) for e in ejes])
        return corr

    if modelo == 'relativa_agrupada':
        # CENTRADO POR FECHA: saca lo que el lote entero hizo ese dia.
        res = res.map(lambda i: ee.Image(i).subtract(_mediana_lote(i))
                      .copyProperties(i, ['system:time_start']))

    mad = res.map(lambda i: ee.Image(i).abs()).median().multiply(1.4826)

    if modelo == 'relativa_agrupada':
        # ESCALA AGRUPADA sobre el lote, con los grados de libertad correctos y
        # recorte robusto para que una nube residual no infle la escala de todos.
        _corte = mad.max(ee.Image.constant(piso)).multiply(RECORTE_SIGMAS)
        _rec = res.map(lambda i: ee.Image(i).max(_corte.multiply(-1)).min(_corte))
        _ss = _rec.map(lambda i: ee.Image(i).pow(2)).sum()
        _gl = (n_base.subtract(2).max(1).rename('gl')
               .updateMask(_ss.select(0).mask()))
        _tot = _ss.addBands(_gl).reduceRegion(
            reducer=ee.Reducer.sum(), geometry=geom, scale=escala,
            maxPixels=1e9, bestEffort=True)
        _gt = ee.Number(_tot.get('gl')).max(1)
        sigma = ee.Image.cat([
            ee.Image.constant(ee.Number(_tot.get(e)).divide(_gt).sqrt()
                              .divide(RECORTE_FACTOR)).rename(e) for e in ejes])
        sigma = sigma.max(piso)
    else:
        sigma = mad.max(piso if piso is not None else SIGMA_MINIMA)

    # INYECCION SINTETICA, para medir la ANOMALIA MINIMA DETECTABLE. Se resta una imagen
    # a la escena evaluada —y SOLO a ella, no a la linea base— porque asi se ve un evento
    # nuevo. Sin esto la sensibilidad no se puede medir sin verdad de campo. Ver
    # `medicion/sensibilidad.py`. En produccion es None y no cambia nada.
    _act = actual.select(ejes)
    if inyeccion is not None:
        _act = _act.subtract(ee.Image(inyeccion).select(ejes))
    r_actual = ee.Image.cat(
        [_act.select(e).subtract(_esperado(e, t_act)).rename(e) for e in ejes])
    if modelo == 'relativa_agrupada':
        # La fecha evaluada se centra con SU propia mediana espacial, igual que la
        # base. Sin esto el residuo de hoy y los de la base no serian comparables.
        r_actual = r_actual.subtract(_mediana_lote(r_actual))
    med = ee.Image.cat([_esperado(e, t_act).rename(e) for e in ejes])
    z = {e: r_actual.select(e).divide(sigma.select(e)).rename('z_' + e)
         for e in ejes}

    # --- Mahalanobis con la covarianza MEDIDA de los z -----------------------
    # La conjuncion de cortes marginales no controla alfa porque la tasa depende de
    # la correlacion entre ejes. La Mahalanobis la usa explicitamente: con la
    # covarianza real, `d2` es chi2 con 2 grados de libertad bajo la nula, sea cual
    # sea r. Es el unico cambio que devuelve un alfa comparable entre lotes.
    zi = ee.Image.cat([z[e] for e in ejes])
    n = len(ejes)
    # `centeredCovariance` es el reductor que devuelve la matriz bajo la clave
    # 'array'; `covariance` no la produce en ese formato y deja el resultado en
    # null, que aguas abajo revienta con "Parameter 'values' may not be null".
    cov = ee.Array(zi.toArray().reduceRegion(
        reducer=ee.Reducer.centeredCovariance(), geometry=geom, scale=escala,
        maxPixels=1e9, bestEffort=True).get('array'))
    # Regularizacion minima: si un eje quedo casi constante la matriz es singular.
    cov = cov.add(ee.Array.identity(n).multiply(1e-6))
    inv = ee.Image(cov.matrixInverse())
    arr = zi.toArray().toArray(1)
    d2 = (arr.arrayTranspose().matrixMultiply(inv)
          .matrixMultiply(arr).arrayGet([0, 0]).rename('d2'))

    # UMBRAL EXPLICITO para poder CALIBRARLO. El chi2 supone SD(z)=1, y eso no se
    # cumple: `medicion/comparar_trayectoria.py` lo midio entre 0,19 y 1,54 segun el
    # modelo y el lote. Cuando SD(z) no es 1 el cuantil teorico no da la tasa que
    # promete, asi que el umbral tiene que poder fijarse por TASA EMPIRICA sobre fechas
    # sin evento — que es el estandar que este proyecto ya adopto.
    if umbral is None:
        umbral = CHI2.get(round(alfa, 3), CHI2[0.01])
    # DIRECCION. La Mahalanobis es simetrica: un pixel que MEJORO mucho tambien da
    # d2 alto. Se exige ademas que el residuo apunte al deterioro en todos los ejes
    # —el mismo sentido que declara `ranking.SIGNO`—, o el motor marcaria el lote
    # que se recupero despues de una lluvia.
    from .ranking import SIGNO
    dir_mala = None
    for e in ejes:
        c = r_actual.select(e).multiply(SIGNO[e]).gte(0)
        dir_mala = c if dir_mala is None else dir_mala.And(c)

    anomalia = (d2.gte(umbral).And(dir_mala)
                .And(n_base.gte(min_base))
                .rename('anomalia'))
    # --- CUANDO SE PUDO HABER PRODUCIDO EL EVENTO ----------------------------
    # El criterio compara la escena de `fecha_actual` contra la trayectoria de la
    # base. Si la observacion limpia ANTERIOR esta lejos, el foco pudo aparecer en
    # cualquier momento de ese intervalo — decir "apareci0 el 1 de agosto" cuando la
    # anterior es del 15 de julio es inventar precision temporal que no se tiene.
    #
    # Sen4CAP (De Vroey et al. 2022, RSE 280:113145, el sistema de la Comision
    # Europea para control de la PAC) resuelve esto declarando un Δt_max: cuando la
    # brecha con la ultima escena limpia excede el tope, **degradan la salida a un
    # INTERVALO de fechas en lugar de una fecha**. Cambian la resolucion del
    # producto en vez de inventar el dato. Ellos usan 60 dias; acá los huecos
    # medidos llegan a 66.
    _f_base = base.aggregate_array('fecha').getInfo() or []
    _prev = max([f for f in _f_base if f < fecha_actual], default=None)
    _dt = None
    if _prev:
        _dt = int((pd.Timestamp(fecha_actual) - pd.Timestamp(_prev)).days)
    return {'d2': d2, 'anomalia': anomalia, 'z': z, 'n_base': n_base,
            'fecha': fecha_actual, 'umbral': umbral, 'sigma': sigma,
            'mediana': med, 'residuo': r_actual,
            # Ventana temporal REAL dentro de la que pudo ocurrir el evento.
            'fecha_previa': _prev,
            'dt_dias': _dt,
            # True => el informe NO puede fechar el evento, solo acotarlo.
            'fecha_imprecisa': bool(_dt is not None and _dt > DT_MAX_DIAS),
            # La puerta de direccion, aparte de `anomalia`, para poder barrer umbrales
            # sin recalcular todo el criterio en cada uno.
            'direccion': dir_mala,
            # Calidad de nube de la escena elegida. Viaja para que se pueda auditar por
            # que se acepto una escena, no solo que se acepto.
            'cs_medio': actual.get('cs_medio')}


def compuerta_dosel(geom, hasta, ventana=None, escala=ESCALA, sitio=None):
    """Dosel util segun la LINEA BASE, no segun la fecha evaluada.

    La pregunta correcta es «¿este pixel alguna vez fue cultivo?», no «¿lo es hoy?».
    Preguntar lo segundo filtra sobre la variable de respuesta: un pixel que perdio
    dosel es exactamente la anomalia buscada, y la compuerta lo borraba.
    """
    import pandas as pd
    ventana = ventana or ventana_de(sitio)
    desde = str(pd.Timestamp(hasta) - pd.Timedelta(days=ventana))[:10]
    fin = str(pd.Timestamp(hasta) - pd.Timedelta(days=1))[:10]
    base = _coleccion_limpia(geom, desde, fin)
    # NDVI maximo de la base: si alguna vez fue dosel pleno, cuenta como cultivo.
    ndvi_max = base.select('NDVI').max()
    q = ndvi_max.reduceRegion(
        reducer=ee.Reducer.percentile([2, 98]), geometry=geom,
        scale=escala * 5, maxPixels=1e9, bestEffort=True)
    lo = ee.Number(ee.Algorithms.If(q.get('NDVI_p2'), q.get('NDVI_p2'), 0))
    hi = ee.Number(ee.Algorithms.If(q.get('NDVI_p98'), q.get('NDVI_p98'), 0))
    rango = hi.subtract(lo).max(1e-6)
    fvc = ndvi_max.subtract(lo).divide(rango).clamp(0, 1)
    return fvc.gte(cfg.FVC_MINIMA).rename('dosel')


# --- SEGUNDA CAPA: zonas por debajo de su propio porte ------------------------
#
# Responde una pregunta DISTINTA de la del criterio temporal, y por eso convive con
# el en vez de reemplazarlo:
#
#     temporal (`evaluar`)  ->  "acá CAMBIÓ algo esta semana"        -> ALERTA
#     zonas    (`zonas`)    ->  "esta zona VIENE peor de lo que su   -> ZONA DE
#                                porte indica"                          MANEJO
#
# MEDIDO 2026-07-29 sobre los 4 lotes: **0% de solapamiento entre las dos capas.**
# Marcan lugares completamente distintos. Ninguna sobra.
#
# COMO SE CONSTRUYE, Y POR QUE ASI
# --------------------------------
# Medido sobre imagen limpia (SANTO_ANTONIO-02, 2026-06-22, cobertura 1,000): los
# cinco indices correlacionan ESPACIALMENTE entre 0,97 y 0,998. Son biomasa con
# cinco nombres. Exigir varios sobre la imagen cruda NO es redundancia: es pedir la
# misma condicion tres veces.
#
# La informacion util aparece al SACAR ese factor: se regresa cada indice contra
# NDVI pixel a pixel y se mira el residuo. Ahi los residuos de NDMI, NDRE y CIRE
# correlacionan entre 0,62 y 0,74 — una segunda dimension REAL, chica (7-19% de la
# varianza) pero confirmada por tres indices independientes.
#
# Que significa un residuo negativo: un punto con LA MISMA BIOMASA que sus pares
# pero mas seco o con menos clorofila de la que le corresponde a su porte. No es
# "creció menos" —eso es biomasa— es "está mal para lo que creció".
#
# Y RESUELVE SOLO EL PROBLEMA DE LAS FECHAS DE SIEMBRA. Sembrar 9 dias mas tarde se
# manifiesta sobre todo como MENOS BIOMASA; al sacar el NDVI se saca tambien esa
# parte. No hace falta estimar la fenologia por pixel, que ademas no se puede: con
# ~10 escenas limpias en 80 dias el estimador de emergencia por medio-maximo da el
# mismo dia para casi todo el lote y confunde "sembrado tarde" con "crece poco".
#
# LAS DOS PRUEBAS QUE LO HABILITARON
# ----------------------------------
# 1. NO ES CUOTA. La fraccion marcada varia de 0,00% a 3,28% entre lotes y fechas —
#    SANTO_ANTONIO-01 marca 4x mas que SANTO_ANTONIO-02, en el mismo campo. Una
#    cuota marcaria lo mismo siempre. (La nula espacial es falsa por construccion y
#    esta es la unica defensa honesta: medir que la fraccion se mueva.)
# 2. ES PERSISTENTE. El solapamiento entre fechas consecutivas es de **18x a 73x**
#    lo que daria el azar. Una zona real esta en el mismo lugar la semana siguiente;
#    el ruido se mueve.
#
# LIMITE QUE HAY QUE DECLARAR: la persistencia prueba que es REAL, no que sea un
# PROBLEMA. Una mancha estable puede ser suelo, un bajo, un borde de terraza o una
# compactacion vieja. Por eso esta capa se entrega como ZONA A INVESTIGAR y no como
# alerta: la urgencia la marca la capa temporal.

# Pixeles validos MINIMOS para intentar la regresion espacial de la capa de zonas.
# Por debajo de esto el ajuste no tiene sentido y ademas devuelve null.
MIN_PIXELES_ZONA = 100
Z_ZONA = 2.0          # sigmas del residuo, en ambos ejes
MMU_ZONA_HA = 0.30    # una zona de manejo mas chica que esto no se maneja distinto


class SinEscena(Exception):
    """No hay escena UTIL en esa fecha sobre ese lote. NO es una averia.

    ⚠️ CORREGIDO 2026-07-29, Y EL DIAGNOSTICO ANTERIOR ESTABA MAL. Se habia creado
    esta excepcion suponiendo que el error
    `EEException: Image.constant: Parameter value is required` venia de que NO HUBIERA
    pasada del satelite ese dia, y solo se chequeaba que la coleccion estuviera vacia.
    Medido despues: la escena SI existe —por ejemplo la del 2026-06-20 sobre
    SANTO_ANTONIO-02— pero queda 100% enmascarada por nube, asi que no hay pixeles
    para el ajuste, `linearFit` devuelve null y `Image.constant(null)` revienta.

    O sea que la condicion correcta no es "no hay escena" sino "no hay escena con
    pixeles suficientes". Son dos causas distintas con el mismo sintoma, y la
    verificacion vieja solo tapaba una.
    """


def zonas(geom, fecha, z=Z_ZONA, escala=ESCALA):
    """Zonas por debajo de su propio porte en la escena `fecha`.

    Devuelve (mascara, {eje: z del residuo}). Ver el bloque de arriba para el
    diseño y la evidencia. Lanza `SinEscena` si ese dia no hubo pasada util.
    """
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
           .filterDate(fecha, ee.Date(fecha).advance(1, 'day'))
           .filterBounds(geom).sort('CLOUDY_PIXEL_PERCENTAGE'))
    # Se pregunta ANTES de construir el calculo. Con la coleccion vacia, `first()`
    # es null y el error aparece recien al final, disfrazado de `Image.constant`.
    if int(col.size().getInfo() or 0) == 0:
        raise SinEscena('no hay escena Sentinel-2 del %s sobre este lote' % fecha)
    img = ee.Image(col.first())
    idx = sr._indices(img).updateMask(sr._mascara(img))
    # Y ADEMAS: que quede algo despues de la mascara. Una escena existente pero
    # totalmente nublada deja cero pixeles, el `linearFit` da null y el error sale
    # como averia del servicio. Cuesta un getInfo por lote y fecha; es una capa de
    # contexto, no la corrida principal.
    _n = int(idx.select('NDVI').reduceRegion(
        reducer=ee.Reducer.count(), geometry=geom, scale=escala,
        maxPixels=1e9, bestEffort=True).get('NDVI').getInfo() or 0)
    if _n < MIN_PIXELES_ZONA:
        raise SinEscena('la escena del %s existe pero deja solo %d pixel(es) validos '
                        'sobre este lote (minimo %d)'
                        % (fecha, _n, MIN_PIXELES_ZONA))
    zs = {}
    for e in cfg.EJES:
        # Recta espacial del indice contra NDVI: es el "porte esperado" de cada
        # punto. El residuo es lo que le sobra o le falta respecto de su biomasa.
        fit = idx.select(['NDVI', e]).reduceRegion(
            reducer=ee.Reducer.linearFit(), geometry=geom, scale=escala,
            maxPixels=1e9, bestEffort=True)
        # Los null del ajuste se resuelven DEL LADO DEL SERVIDOR. Sin esto, una
        # escena escasa hace que `Image.constant` reciba null y la averia aparezca
        # lejos de su causa.
        _esc = ee.Number(ee.Algorithms.If(fit.get('scale'), fit.get('scale'), 0))
        _off = ee.Number(ee.Algorithms.If(fit.get('offset'), fit.get('offset'), 0))
        esperado = idx.select('NDVI').multiply(_esc).add(_off)
        r = idx.select(e).subtract(esperado)
        _sd = r.reduceRegion(
            reducer=ee.Reducer.stdDev(), geometry=geom, scale=escala,
            maxPixels=1e9, bestEffort=True).values().get(0)
        sg = ee.Number(ee.Algorithms.If(_sd, _sd, 0))
        # ⚠️ MEDIDO 2026-07-29: EL NDVI DE ESTOS LOTES ESTA SATURADO Y LA REGRESION
        # FUNCIONA IGUAL. Se sospecho —a partir de Herrmann et al. 2011, que mide que
        # el NDVI pierde sensibilidad al LAI sobre LAI=2— que esta regresion corriera
        # contra una variable sin gradiente. Sobre los 4 lotes reales, escena limpia:
        #
        #     NDVI mediana 0,92-0,93 y rango p95-p5 de solo 0,062 a 0,097  (saturado)
        #     R2 de la regresion indice~NDVI:            0,822 a 0,914     (funciona)
        #
        # O sea que dentro de ese rango angosto las diferencias chicas de NDVI todavia
        # siguen la misma variacion de biomasa que sigue el indice. LA HIPOTESIS NO SE
        # SOSTIENE: esta capa no esta muda por la saturacion del NDVI.
        #
        # Lo que el R2 SI dice es cuanta señal queda en el residuo: entre el 9% y el 18%
        # de la varianza espacial. Coincide con la medicion previa de 7-19%, y explica
        # por que una zona "a 2 sigmas del residuo" es un apartamiento CHICO en terminos
        # absolutos aunque sea estadisticamente real.
        #
        # ⚠️ ESTE `divide` ES LO QUE HACE QUE ESTA CAPA SEA UNA CUOTA, y hay que
        # decirlo: al dividir por el desvio de LA MISMA escena, el z queda con SD=1
        # POR CONSTRUCCION. Entonces el corte en z>=2 marca una fraccion que depende
        # solo de la FORMA de la distribucion, no de si el lote esta bien o mal. La
        # selectividad real de la capa no viene de aca: viene del filtro de mayoria y
        # de la unidad minima, que borran lo que esta disperso. Ver `capas.py`.
        zs[e] = r.divide(sg.max(1e-6)).rename('zr_' + e)
    from .ranking import SIGNO
    m = None
    for e in cfg.EJES:
        # Mismo sentido de deterioro que declara SIGNO, aplicado al RESIDUO.
        cond = zs[e].multiply(SIGNO[e]).gte(z)
        m = cond if m is None else m.And(cond)
    return m.rename('zona'), zs


# --- puente hacia focos.py ----------------------------------------------------

def para_focos(geom, hasta, alfa=ALFA, sitio=None, modelo=None, ajuste=None):
    """Lo que `focos.detectar_lote` necesita, calculado con el criterio v2.

    Devuelve exactamente la misma interfaz que ya consumia el vectorizador, para
    que TODO lo de aguas abajo —unidad minima de mapeo, filtro de moda, severidad,
    GeoJSON, informe— siga igual y el cambio quede acotado al criterio:

        zs        {eje: imagen de z}   (temporal por pixel, no espacial)
        foco      mascara booleana de anomalia
        evaluada  mascara de pixel con dato (para el area util)
        ref       imagen de la que sacar la proyeccion
        fecha_img fecha de la escena evaluada
        n_base    escenas de la linea base (para declararlo en el informe)
        base_desde / base_hasta

    `fecha_ref` deja de ser UNA fecha: la referencia es la trayectoria del propio
    pixel sobre `n_base` observaciones. El informe tiene que decirlo asi, no
    inventar una fecha de referencia que ya no existe.
    """
    import pandas as pd
    r = evaluar(geom, hasta, alfa=alfa, sitio=sitio, modelo=modelo, ajuste=ajuste)
    dosel = compuerta_dosel(geom, hasta, sitio=sitio)
    ejes = list(cfg.EJES)
    zs = {e: r['z'][e].updateMask(dosel).rename('z_' + e) for e in ejes}
    foco = r['anomalia'].And(dosel).rename('foco')
    evaluada = zs[ejes[0]].mask().rename('u')
    desde = str(pd.Timestamp(hasta) - pd.Timedelta(days=ventana_de(sitio)))[:10]
    return {'zs': zs, 'foco': foco, 'evaluada': evaluada,
            'ref': zs[ejes[0]], 'fecha_img': r['fecha'],
            # Ventana real de ocurrencia (patron Δt_max de Sen4CAP). El informe usa
            # `fecha_imprecisa` para decidir si puede FECHAR el foco o solo ACOTARLO.
            'fecha_previa': r.get('fecha_previa'),
            'dt_dias': r.get('dt_dias'),
            'fecha_imprecisa': r.get('fecha_imprecisa', False),
            'n_base': r['n_base'], 'base_desde': desde,
            'base_hasta': str(pd.Timestamp(hasta) - pd.Timedelta(days=1))[:10],
            'd2': r['d2'], 'umbral': r['umbral']}
