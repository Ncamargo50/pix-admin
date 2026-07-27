"""Ciclo del cultivo: de la fecha de siembra a la ventana de monitoreo.

POR QUE EXISTE ESTE MODULO
--------------------------
El motor se para fuera de la campaña a proposito (`main.py`): en madurez el NDMI
baja y el PSRI sube, que es exactamente la firma que busca el criterio, asi que
cosecha y deterioro son indistinguibles. Hasta ahora la ventana habia que
escribirla a mano en el JSON del sitio, lote por lote y campaña por campaña. Eso
no escala a un cliente con varias haciendas ni a un tecnico dando de alta desde
el navegador.

Acá se declara UNA cosa por cultivo —cuantos dias dura el ciclo— y la ventana sale
sola de la fecha de siembra.

QUE SON ESTOS NUMEROS Y QUE NO SON
----------------------------------
Son **configuracion operativa declarada**, no una constante agronomica. La duracion
real depende del cultivar, del grupo de madurez, de la fecha de siembra y del año.
Por eso:

  · cada cultivo declara un RANGO observado y un valor OPERATIVO. **El operativo es
    el extremo CORTO del rango, no el largo.** El argumento original —"estirarla de
    mas solo agrega fechas que el motor descarta solo"— es FALSO y se corrigio el
    2026-07-27: el motor no descarta nada solo. Ni `focos.detectar_lote` ni el
    ranking tienen noción de estadio fenologico; el UNICO corte es el fin de esta
    ventana. Y a partir de la madurez el criterio deja de ser valido —NDMI y NDRE
    bajando a la vez ES la firma de senescencia, o sea literalmente el criterio de
    foco—, asi que una cosecha parcial produce un "foco" garantizado de decenas de
    hectareas. Con el extremo largo, un cultivar precoz quedaba hasta 25-30 dias
    monitoreado en senescencia y cosecha. Errar hacia el lado corto pierde el final
    del ciclo; errar hacia el largo INVENTA alertas. No es simetrico.
  · el valor se puede pisar por sitio con `ciclo_dias` en el JSON del cliente, que
    es lo que hay que hacer en cuanto el cliente diga su cultivar;
  · `FUENTE` dice de donde sale cada uno. Donde no hay respaldo institucional
    verificado, se dice.

NO confundir esto con una tabla de "valores esperados de indice por estadio". Eso
NO existe como estandar transferible y este modulo no lo pretende: acá solo se
declara cuanto dura el cultivo en el suelo.
"""
from datetime import date, timedelta

# Margen despues de la madurez fisiologica. La cosecha no es puntual y el lote
# puede quedar en pie unos dias; se corta igual porque a partir de la madurez el
# criterio no distingue senescencia de daño.
MARGEN_FIN_DIAS = 0
# El monitoreo arranca EN la siembra, no despues: el estimador de cohorte necesita
# ver la emergencia. Recortar el inicio fue lo que dejo 188 de 207 lotes sin ciclo.
MARGEN_INICIO_DIAS = 0

# cultivo -> (dias operativos, (rango observado), nota de fuente)
CICLOS = {
    # Operativo = extremo CORTO del rango. Ver la nota de arriba: pasarse de la
    # madurez no agrega fechas inocuas, fabrica focos de senescencia.
    'soya':          (95,  (95, 145),  'Grupos de madurez cortos a largos. Con un '
                                       'grupo largo, declarar `ciclo_dias` por sitio.'),
    'maiz':          (110, (110, 165), 'Hibridos precoces a tardios.'),
    'trigo':         (100, (100, 145), 'Trigo de invierno. El rango cubre tanto el '
                                       'tropical (Santa Cruz) como el subtropical '
                                       'del sur de Brasil; los lotes de Parana '
                                       'estan en el extremo corto.'),
    'sorgo':         (90,  (90, 135),  'Granifero.'),
    'girasol':       (90,  (90, 135),  'Sin umbrales oficiales de plaga; el ciclo '
                                       'si esta bien acotado.'),
    'cana_de_azucar': (300, (300, 550), 'Caña planta (~400-550) vs soca (~300-365) '
                                        'son dos poblaciones distintas: un solo '
                                        'numero esta mal para una de las dos. Se '
                                        'toma el corto y HAY QUE declarar '
                                        '`ciclo_dias` por sitio. Cerrar antes deja '
                                        'el sitio FUERA DE CAMPANA —un estado '
                                        'visible—; pasarse fabrica un foco enorme '
                                        'el dia de la cosecha.'),
    'pastura':       (365, (365, 365), 'Perenne: se monitorea todo el año, la '
                                       'ventana no la define un ciclo.'),
}

# Cultivos donde el valor operativo es especialmente flojo y conviene que el
# cliente lo declare. Se avisa en el alta en vez de dejarlo pasar callado.
DECLARAR_POR_SITIO = ('cana_de_azucar', 'pastura')

CULTIVOS = tuple(sorted(CICLOS))


def ciclo_dias(cultivo, override=None):
    """Dias de ciclo a usar. `override` (del JSON del sitio) siempre gana."""
    if override:
        if not isinstance(override, int) or override < 30:
            raise ValueError('ciclo_dias debe ser un entero >= 30, es %r' % override)
        return override
    if cultivo not in CICLOS:
        raise ValueError('cultivo %r desconocido. Declarados: %s'
                         % (cultivo, ', '.join(CULTIVOS)))
    return CICLOS[cultivo][0]


def ventana(cultivo, siembra, override=None):
    """(inicio, fin) de monitoreo en ISO, desde la fecha de siembra.

    El fin es la madurez fisiologica estimada: pasada esa fecha el motor no emite
    ranking porque no puede separar cosecha de deterioro.
    """
    if isinstance(siembra, str):
        y, m, d = (int(x) for x in siembra.split('-'))
        siembra = date(y, m, d)
    n = ciclo_dias(cultivo, override)
    ini = siembra + timedelta(days=MARGEN_INICIO_DIAS)
    fin = siembra + timedelta(days=n + MARGEN_FIN_DIAS)
    return ini.isoformat(), fin.isoformat()


def etiqueta_campana(cultivo, siembra, override=None):
    """Nombre de la campaña, del estilo '2025/2026' o '2026' si no cruza el año.

    El `override` NO es opcional aca: sin el, la etiqueta sale de un ciclo distinto
    del que define la ventana. Medido: soya sembrada 2025-11-01 con ciclo 400 daba
    la ventana hasta 2026-12-06 rotulada como campaña "2025/2026". Esa etiqueta es
    la clave del dict de campañas y lo que identifica la campaña en los entregables.
    """
    ini, fin = ventana(cultivo, siembra, override)
    a, b = ini[:4], fin[:4]
    return a if a == b else '%s/%s' % (a, b)


def campanas_desde_siembra(cultivo, siembra, override=None):
    """El dict `campanas` que espera `config.Sitio`, derivado de una sola fecha."""
    return {etiqueta_campana(cultivo, siembra, override):
            ventana(cultivo, siembra, override)}


def dias_restantes(cultivo, siembra, hoy=None, override=None):
    """Cuantos dias de monitoreo quedan. Negativo = la campaña ya cerro."""
    _, fin = ventana(cultivo, siembra, override)
    hoy = hoy or date.today()
    if isinstance(hoy, str):
        y, m, d = (int(x) for x in hoy.split('-'))
        hoy = date(y, m, d)
    y, m, d = (int(x) for x in fin.split('-'))
    return (date(y, m, d) - hoy).days


def describir(cultivo, siembra, override=None):
    """Frase para el alta y para el informe. Sin adornos: fechas y dias."""
    ini, fin = ventana(cultivo, siembra, override)
    n = ciclo_dias(cultivo, override)
    aviso = ''
    if cultivo in DECLARAR_POR_SITIO and not override:
        aviso = (' El ciclo de este cultivo varia demasiado para un valor unico: '
                 'conviene declararlo por sitio.')
    return ('%s sembrada el %s: se monitorea del %s al %s (%d dias de ciclo).%s'
            % (cultivo.replace('_', ' ').capitalize(), siembra, ini, fin, n, aviso))
