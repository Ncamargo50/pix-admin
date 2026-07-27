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
SCL_MALAS = [1, 2, 3, 8, 9, 10, 11]
DILATAR_NUBE_PX = 2              # a 20 m = 40 m de dilatacion

# Compuerta de vegetacion por FVC, no por NDVI absoluto. Los extremos salen de la
# propia escena (p2/p98), no de una tabla: un umbral absoluto no transfiere.
FVC_MINIMA = 0.35
