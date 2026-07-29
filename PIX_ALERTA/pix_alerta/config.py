"""Configuracion de sitios. Nada de esto va en el codigo del motor.

Agregar una hacienda = agregar una entrada aca. No se toca ningun otro archivo.
Es la correccion al hardcode del pipeline actual, donde el diccionario de haciendas
esta duplicado en tres modulos.
"""
from dataclasses import dataclass, field


@dataclass
class Sitio:
    clave: str
    titulo: str
    lotes_geojson: str
    campo_id: str                  # propiedad del GeoJSON que es el ID estable del lote
    campo_area: str = 'area_ha'
    # Cultivo del sitio, con la clave del banco de fichas de la app (soya, trigo, maiz,
    # sorgo, girasol, cana_de_azucar, pastura). Sin esto la app cae a su default 'trigo'
    # y abre el banco de TRIGO para diagnosticar una soya.
    cultivo: str = ''
    epsg_metrico: str = 'EPSG:32720'
    buffer_negativo_m: float = 5.0  # ESPECIFICACION.md paso 1 (JRC 10.3390/rs12142195)
    # Ventanas de campaña. Sin esto no hay cohorte ni trayectoria esperada.
    # Se pueden declarar a mano, o dejarlas salir de `siembra` + el ciclo del
    # cultivo (ver ciclos.py). Lo segundo es lo que usa el alta desde el navegador:
    # el tecnico sabe cuando sembro, no sabe entre que fechas conviene mirar.
    campanas: dict = field(default_factory=dict)
    siembra: str = ''              # 'YYYY-MM-DD'. Deriva `campanas` si esta vacio.
    ciclo_dias: int = None         # pisa el ciclo por defecto del cultivo
    # Filtro de unidades: el inventario de lotes trae pistas, montes y caminos.
    # Sin este filtro el ranking manda al tecnico a la pista de aterrizaje —
    # paso de verdad: "PISTA" (2,78 ha) salio primera en la corrida del 2026-05-06.
    # CAMPO CHICO. Con menos de ranking.MIN_LOTES_COHORTE lotes no hay cohorte, y no
    # la va a haber nunca: el ranking entre lotes no aplica a esta escala. Con esto en
    # true el sitio entrega el ACERCAMIENTO intra-lote, que compara cada pixel contra
    # el mismo lote en la escena limpia anterior y no necesita cohorte.
    # OJO: el acercamiento NO tiene tasa de falsa alarma validada (su nula fue
    # auditada y rechazada). Entrega poligonos y hectareas para ir a mirar.
    # SIEMBRAS DECLARADAS POR EL CLIENTE, de la mas temprana a la mas tardia.
    # Lista de fechas 'YYYY-MM-DD'. Cuando el lote se sembro en varias pasadas, el
    # motor contrasta el atraso MEDIDO de cada bloque contra el que estas fechas
    # implican. Una diferencia grande no es un error del satelite: es que ese bloque
    # tardo mas en implantarse de lo que su fecha explica.
    #
    # MEDIDO en Santo Antonio-02 (declarado 26/04, 29/04 y +9 dias): los atrasos
    # reales dieron 0 / 12,0 / 36,9 dias. El cliente confirmo que el fondo NO se
    # resembro — fue siembra normal corrida por lluvias. O sea que el desfase real
    # era mayor que el anotado, y el satelite lo midio bien.
    siembras: tuple = ()
    # --- AJUSTES QUE NO PUEDEN SER GLOBALES -----------------------------------
    # Los dos defaults de abajo se MIDIERON sobre un cultivo concreto: el piso de
    # escala sobre TRIGO en Parana, la unidad minima de mapeo sobre lotes de 40-90
    # ha. Sirven como punto de partida razonable, no como constantes universales:
    # un cultivo de porte bajo, una region con otra atmosfera o un cliente que
    # trabaja a otra escala pueden necesitar otro valor. Se declaran por sitio y
    # quedan a la vista en el JSON del cliente, en vez de escondidos en el codigo.
    #
    # Vacio / None = usar el default medido. Cambiarlos EXIGE volver a correr
    # `medicion/calibrar_criterio.py` sobre fechas sin evento de ese cliente.
    sigma_minima: float = None     # pisa el piso de escala (unidades del indice)
    mmu_ha: float = None           # pisa la unidad minima de mapeo de los focos
    solo_focos: bool = False
    unidades_csv: str = ''
    unidades_col_id: str = 'lote_id'
    unidades_col_cat: str = 'categoria'
    categorias_excluidas: tuple = ()


HDS = Sitio(
    clave='HDS',
    titulo='Hacienda del Señor',
    lotes_geojson=(r'C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS'
                   r'\Hacienda-Del-Senor\HACIENDA-DEL-SENOR-PIX-MUESTREO'
                   r'\HACIENDA_TODOS_LOTES_OVERVIEW.geojson'),
    campo_id='lote',
    cultivo='soya',
    epsg_metrico='EPSG:32720',
    campanas={'2025/2026': ('2025-10-01', '2026-04-30'),
              '2024/2025': ('2024-10-01', '2025-04-30'),
              '2023/2024': ('2023-10-01', '2024-04-30')},
    unidades_csv=(r'C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS'
                  r'\Hacienda-Del-Senor\04-Sacarosa-Sentinel2'
                  r'\clasificacion_lotes_2026-05-13.csv'),
    categorias_excluidas=('MONTE_FOREST', 'PASTO_O_COBERTURA', 'OTRO_REVISAR'),
)

SITIOS = {s.clave: s for s in [HDS]}


def unidades_validas(sitio):
    """IDs de lote que son cultivo. None si el sitio no declara filtro.

    Un lote que no esta en la clasificacion NO se incluye: si no se sabe que es,
    no se manda a nadie. Es preferible perder un lote a mandar al tecnico al monte.
    """
    if not sitio.unidades_csv:
        return None
    import pandas as pd
    d = pd.read_csv(sitio.unidades_csv, encoding='utf-8')
    ok = d[~d[sitio.unidades_col_cat].isin(sitio.categorias_excluidas)]
    return set(ok[sitio.unidades_col_id].astype(str))

# --- Parametros del criterio, todos declarados y todos barribles ---------------
# Dos ejes de dosel, no siete. Dimensionalidad efectiva medida de los 7 indices
# del motor v7: 1,87-2,40 (PIX_ALERTA/medicion/dimensionalidad_indices.py).
#
# EL SEGUNDO EJE SE ELIGIO MIDIENDO, no por preferencia. Contra la nula sintetica
# (cada lote sigue su cohorte + ruido AR(1) con la correlacion real entre ejes),
# replicado sobre las TRES campanas de HDS, 8 fechas de corte cada una —
# `python -m medicion.comparar_ejes --serie salida/serie_HDS_20*.csv`:
#
#                   2023/24   2024/25   2025/26  |  lift medio  lift PEOR
#     NDMI + PSRI     9,1x     13,2x      6,2x   |     9,5x       6,2x
#     NDMI + NDRE    11,2x     36,3x      6,7x   |    18,1x       6,7x   <- elegido
#     NDMI + CIRE    12,3x     26,9x      6,6x   |    15,3x       6,6x
#
# CONCLUSION FIRME: **PSRI es el peor de los tres en las tres campanas.** Tiene dos
# razones fisicas para serlo: usa B2 (azul), la banda de peor relacion senal-ruido
# sobre vegetacion y la mas afectada por atmosfera residual, y mezcla resoluciones
# nativas (B2/B4 a 10 m con B6 a 20 m).
#
# CONCLUSION NO CERRADA: NDRE y CIre estan EMPATADOS en el peor caso (6,69x contra
# 6,64x) y se reparten las campanas (NDRE gana 2, CIre gana 1). Se elige NDRE por
# ROBUSTEZ, no por la medicion: es una diferencia normalizada, acotada en [-1,1],
# mientras que CIre es un cociente B7/B5 sin cota — con B5 chico sobre vegetacion
# rala produce colas pesadas, y una escala robusta por MAD subestima esas colas.
# CIre queda como alternativa legitima: es el MENOS correlacionado con NDMI (0,72
# contra 0,82), o sea el que mas evidencia independiente aporta.
#
# EL HALLAZGO MAS IMPORTANTE NO ES EL EJE: el lift sigue a la COBERTURA, no al
# indice. La campana con 16,0% de observaciones plenas dio 36x; la de 11,8% dio
# 6,7x, con el mismo eje. Cambiar de eje compra ~2x; mejorar la disponibilidad de
# imagen compra ~5x. La continuidad con radar vale mas que afinar indices.
#
# Cambiar de eje es cambiar `EJES` y nada mas — todo el resto lo lee de aca, y
# `ranking.SIGNO` tiene que declarar el sentido de alarma del eje nuevo.
EJES = ('NDMI', 'NDRE')          # humedad de dosel, clorofila de borde rojo

# NO hay override de ejes por sitio, a proposito. Serian dos: el par de arriba se
# eligio contra una nula sintetica sobre TRES campañas de CAÑA, o sea que ya es
# evidencia de otro cultivo y no un ajuste al trigo; y todos los modulos leen `EJES`
# directo, asi que un override parcial dejaria medio motor con un par y medio con
# otro. Si algun dia hace falta, se cambia aca y en `ranking.SIGNO`, no por cliente.


def valor_de(sitio, atributo, default):
    """Lee un ajuste por sitio y cae al default MEDIDO si no esta declarado.

    Un `0` declarado a proposito se respeta; solo `None` y `''` caen al default.
    """
    v = getattr(sitio, atributo, None)
    return default if v is None or v == '' else v

# Calidad de observacion por lote y fecha. La etiqueta viaja DENTRO del dato:
# sin esto no se puede distinguir un falso negativo real de una dekada nublada.
UMBRAL_PLENO = 0.80
UMBRAL_PARCIAL = 0.40

# SCL a descartar. Las dos que importan y que casi nadie excluye:
#   3 = CLOUD_SHADOW — el artefacto que MAS se parece a un foco.
#   2 = DARK_AREA_PIXELS — Sen2Cor le asigna rutinariamente sombra de nube que no
#       alcanzo a clasificar como 3, ademas de sombra topografica y agua oscura.
#       Un dosel en sombra sin enmascarar da NDMI abajo Y NDRE abajo, o sea los DOS
#       ejes en el sentido de alarma: es un ATENCION fabricado por la iluminacion.
# Tambien 1 (saturado/defectuoso), 8/9/10 (nubes y cirros) y 11 (nieve).
# 0 = NO_DATA. AUDITADO 2026-07-29: no estaba en la lista, asi que un pixel sin dato
#     de SCL pasaba como VALIDO — `remap` le da el valor por defecto 0 = "no mala".
#     MEDIDO sobre las 14 escenas de mayo-julio de SANTO_ANTONIO-02: SCL=0 en el
#     0,000% del lote, o sea que el hueco estaba LATENTE y no activo. Se cierra igual:
#     un lote que cruce el borde de un granulo si puede tener NO_DATA adentro, y ahi
#     el indice se calcularia sobre reflectancia nula.
#
# QUE NO SE EXCLUYE, Y ES UNA DECISION:
#   6 = WATER. Un encharcado en trigo ES una anomalia que vale reportar. Y ademas SCL
#       confunde seguido suelo humedo oscuro y sombra de nube con agua. Se deja pasar
#       porque el criterio busca NDMI Y NDRE BAJANDO JUNTOS: el agua sube el NDMI, asi
#       que no dispara la direccion de deterioro. Si algun dia el criterio cambia de
#       direccion, esta decision hay que rehacerla.
#   7 = UNCLASSIFIED. Sen2Cor la usa cuando no pudo decidir. Excluirla descartaria
#       pixeles buenos en bordes de lote; dejarla pasar admite algun pixel dudoso.
#       Se deja, y queda anotado que no esta medido cual de los dos errores es peor.
SCL_MALAS = [0, 1, 2, 3, 8, 9, 10, 11]
# DILATACION DE LA MASCARA DE NUBE, en pixeles de 20 m.
#
# ⚠️ SUBIDO DE 2 A 4 (40 m -> 80 m) EL 2026-07-29, Y EL MOTIVO IMPORTA.
#
# Con 40 m, SANTO_ANTONIO-02 producia 3 focos (1,28 ha) que se le reportaron al
# cliente. MEDIDO ese dia:
#   · los 3 focos estaban a 19-70 m del borde de la mascara de nube (1 a 3,5 px);
#   · con dilatacion de 80 m DESAPARECEN LOS TRES, y tambien los 4 que producia la
#     variante de compuerta nueva;
#   · y ademas la escena del 20-07 —medio lote tapado— deja de pasar COB_MINIMA, asi
#     que el par cae al 15-07 / 10-07, que esta limpio y no tiene ningun foco.
#
# O sea: los focos no eran daño, eran **borde de nube fina que SCL no clasifica**.
# SCL marca el nucleo opaco; el cirro delgado y la bruma peri-nube quedan como
# "vegetacion" con reflectancia deprimida, que es exactamente la firma que busca el
# criterio (NDMI y NDRE bajando juntos).
#
# 80 m no es un numero elegido para que los focos desaparezcan: es el orden de
# magnitud que la literatura de mascaras de S2 usa como buffer minimo, y la
# alternativa correcta —CloudScore+ (GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED), que
# SI modela nube fina, bruma y cirro— esta pendiente de implementar. Mientras tanto,
# dilatar es la defensa barata y conservadora.
#
# COSTO DECLARADO: se pierde area util cerca de las nubes. Es el lado correcto del
# error: un foco de menos se descubre en la proxima escena limpia; un foco inventado
# manda al tecnico a caminar una nube.
DILATAR_NUBE_PX = 4              # a 20 m = 80 m de dilatacion

# CLOUDSCORE+ (Google). Cubre lo que SCL no ve: nube fina, bruma y cirro. Es el
# agujero por el que se colaron los 3 focos falsos del 2026-07-29.
# `cs_cdf` es la version acumulada, mas estable que `cs` cruda. Umbral recomendado
# por Google: 0,50-0,65. Se toma 0,60, el medio del rango: mas alto descarta escenas
# utilizables, mas bajo deja pasar bruma.
# CRITERIO DE DETECCION. 'v2' desde 2026-07-29 (ver pix_alerta/criterio.py).
# MEDIDO sobre fechas SIN evento de los 4 lotes de trigo, alfa nominal 1%:
#     v1 (z espacial + conjuncion):  mediana 0,38-2,11%   MAXIMO 7,9-11,8%
#     v2 (z temporal + Mahalanobis): mediana 0,00%        MAXIMO 0,2-2,2%
# v1 marcaba hasta el 12% del lote donde no pasaba nada. 'v1' queda disponible para
# poder comparar, no como camino de produccion.
CRITERIO = 'v2'

USAR_CLOUDSCORE = True
CS_BANDA = 'cs_cdf'
CS_UMBRAL = 0.60

# Compuerta de vegetacion por FVC, no por NDVI absoluto. Los extremos salen de la
# propia escena (p2/p98), no de una tabla: un umbral absoluto no transfiere.
FVC_MINIMA = 0.35
